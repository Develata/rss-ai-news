import os
from datetime import datetime, timezone

from github import Github
from github.GithubException import UnknownObjectException

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
            raise ValueError("❌ 缺少 GITHUB_TOKEN 或 REPO_NAME 环境变量")

        self.g = Github(token)
        self.repo = self.g.get_repo(repo_name)

        logger.info(f"🐙 已连接 GitHub 仓库: {repo_name}")
        logger.info(
            f"📂 目标文件夹设置为: {self.target_folder if self.target_folder else '(仓库根目录)'}"
        )

    def push_markdown(self, filename, content):
        if self.target_folder:
            full_path = os.path.join(self.target_folder, filename)
        else:
            full_path = filename

        full_path = full_path.replace("\\", "/")

        current_time = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
        message = f"🤖 Bot Update: {current_time}"

        try:
            contents = self.repo.get_contents(full_path)
            self.repo.update_file(contents.path, message, content, contents.sha)
            logger.info(f"✅ [Update] 文件已更新: {full_path}")

        except UnknownObjectException:
            try:
                self.repo.create_file(full_path, message, content)
                logger.info(f"✅ [Create] 新文件已创建: {full_path}")
            except Exception as create_error:
                logger.error(
                    f"❌ [Create Failed] 创建文件失败: {full_path} | Error: {create_error}"
                )

        except Exception as e:
            logger.error(f"❌ [Push Failed] 操作异常: {full_path} | Error: {e}")
