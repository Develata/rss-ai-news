import os

from github import Github, InputGitTreeElement  # <--- 必须引入 InputGitTreeElement
from github.GithubException import GithubException

from news_crawler.core.settings import get_settings

try:
    from news_crawler.utils.logger import logger
except ImportError:
    import logging
    logger = logging.getLogger(__name__)


class GitHubPublisher:
    def __init__(self):
        settings = get_settings()
        token = settings.github.token
        repo_name = settings.github.repo_name
        self.target_folder = settings.github.target_folder

        if not token or not repo_name:
            error_msg = "❌ GitHub 配置缺失\n"
            if not token:
                error_msg += "   - GITHUB_TOKEN 未设置\n"
            if not repo_name:
                error_msg += "   - REPO_NAME 未设置\n"
            error_msg += "   💡 请在 .env 文件中配置这些变量"
            raise ValueError(error_msg)

        try:
            self.g = Github(token)
            self.repo = self.g.get_repo(repo_name)
            logger.info(f"🐙 已连接 GitHub 仓库: {repo_name}")
        except GithubException as e:
            if e.status == 401:
                raise ValueError("❌ GitHub 认证失败: Token 无效或已过期\n   💡 请检查 GITHUB_TOKEN 配置") from e
            elif e.status == 404:
                raise ValueError(f"❌ GitHub 仓库不存在: {repo_name}\n   💡 请检查 REPO_NAME 配置或 Token 的访问权限") from e
            else:
                raise ValueError(f"❌ GitHub 连接失败 ({e.status}): {e.data.get('message', str(e))}") from e
        except Exception as e:
            raise ValueError(f"❌ GitHub 初始化失败: {type(e).__name__}: {e}\n   💡 请检查网络连接") from e

    def publish_changes(self, file_updates: list, commit_message: str):
        """
        核心方法：一次性提交多个文件 (One Commit)
        file_updates 结构: [{"path": "路径", "content": "内容"}, ...]
        """
        if not file_updates:
            return

        repo = self.repo
        
        # 1. 获取默认分支 (main 或 master) 及其最新的 Commit
        default_branch = repo.default_branch
        ref = repo.get_git_ref(f"heads/{default_branch}")
        latest_commit = repo.get_git_commit(ref.object.sha)
        base_tree = latest_commit.tree

        # 2. 构建 Tree 元素列表
        element_list = []
        for file in file_updates:
            # 处理路径：如果有 target_folder，拼接上去
            full_path = (file.get("path") or "").strip()
            # 防御：如果传入了绝对路径风格（/foo 或 \foo），避免 join 时丢失 target_folder
            full_path = full_path.lstrip("/\\")
            if self.target_folder:
                full_path = os.path.join(self.target_folder, full_path)

            full_path = full_path.replace("\\", "/").strip("/")

            # 创建 Blob (文件对象)，处理编码
            blob = repo.create_git_blob(file["content"], "utf-8")

            # 创建 Tree 元素
            element = InputGitTreeElement(
                path=full_path,
                mode='100644', # 100644 表示普通文件
                type='blob',
                sha=blob.sha
            )
            element_list.append(element)

        # 3. 创建新的 Tree (基于旧的 Tree)
        try:
            new_tree = repo.create_git_tree(element_list, base_tree)
        except GithubException as e:
            raise RuntimeError(f"❌ GitHub Tree 创建失败: {e.data.get('message', str(e))}\n   💡 可能是文件路径格式错误") from e

        # 4. 创建新的 Commit
        try:
            new_commit = repo.create_git_commit(commit_message, new_tree, [latest_commit])
        except GithubException as e:
            raise RuntimeError(f"❌ GitHub Commit 创建失败: {e.data.get('message', str(e))}") from e

        # 5. 更新分支引用 (git push)
        try:
            ref.edit(new_commit.sha)
        except GithubException as e:
            if e.status == 403:
                raise RuntimeError("❌ GitHub Push 权限不足\n   💡 请确保 Token 具有仓库写入权限 (repo scope)") from e
            else:
                raise RuntimeError(f"❌ GitHub Push 失败: {e.data.get('message', str(e))}") from e

        logger.info(f"✅ [Batch Push] 成功推送 {len(file_updates)} 个文件。Commit SHA: {new_commit.sha[:7]}")
