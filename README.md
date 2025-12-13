#RSS AI News Crawler<div align="center">

**你的私人 AI 情报官**





全自动化的信息获取、AI 深度分析与日报生成系统。

[特性] • [Docker 部署] • [本地开发] • [配置指南]

</div>

##📖 简介 | Introduction**RSS AI News** 是一个可自部署的新闻聚合与分析工具。它不仅仅是抓取 RSS，更利用大语言模型 (OpenAI / Gemini / Qwen 等) 对新闻进行**深度理解、评分和摘要**，最终生成一份高质量的 Markdown 日报并自动发布到 GitHub 仓库（可配合 GitHub Pages 展示）。

项目内置了针对不同领域的分析策略（如数学研究、硬核科技、世界时政），确保你只关注真正有价值的信息。

##✨ 特性 | Features* **🕸 多源采集**: 支持标准 RSS、RSSHub 生成的订阅源、以及特定 JSON API 接口抓取。
* **🧠 AI 驱动分析**:
* **智能评分**: 根据新闻的学术价值、技术深度或社会热度打分 (0-100)。
* **自动摘要**: 过滤标题党，提取核心信息（支持保留 LaTeX 公式）。
* **领域策略**: 内置“数学研究”、“硬核科技”、“AI & ML”、“世界时政”等差异化 Prompt 策略。


* **💾 灵活存储**: 支持 PostgreSQL（推荐）和 SQLite（开箱即用）。
* **🐳 Docker Ready**: 提供完整的 Dockerfile 和 docker-compose 配置，集成 Crontab 定时任务。
* **📊 自动发布**:
* 自动生成按日期归档的 Markdown 日报。
* 通过 Git API 自动推送到远程仓库，实现“One Commit”发布。
* 支持本地落盘备份。



##🐳 Docker 快速部署 (推荐)最简单的运行方式是使用 Docker Compose。

###1. 克隆仓库```bash
git clone https://github.com/your-username/rss-ai-news.git
cd rss-ai-news

```

###2. 配置环境变量复制示例配置文件并修改：

```bash
cp .env.example .env

```

使用文本编辑器修改 `.env` 文件。**最简配置**仅需填写以下几项：

* `AI_API_KEY`: 你的 LLM API 密钥。
* `AI_URL`: LLM 的 Base URL (例如阿里云 Qwen、OpenAI 等)。
* `GITHUB_TOKEN` & `REPO_NAME`: 用于发布日报的 GitHub 仓库信息。
* `DB_BACKEND`: 设为 `sqlite` 即可免去配置 PostgreSQL。

###3. 启动服务```bash
docker-compose up -d

```

###4. 查看运行状态容器启动后会自动运行 Crontab：

* **每 10 分钟**: 执行采集与 AI 分析 (`ingest`)。
* **每天 09:00**: 执行日报发布 (`publish`)。

查看日志：

```bash
# 日志映射在本地 logs 目录
tail -f logs/ingest.log
tail -f logs/publish.log

```

---

##🛠️ 本地开发与运行如果你想进行二次开发或不使用 Docker 运行：

###1. 安装依赖建议使用 Python 3.10+ 环境：

```bash
# 安装为可编辑模式
pip install -e .

```

###2. 初始化数据库确保 `.env` 配置正确后，运行重置脚本（注意：这会清空旧表，初次运行推荐）：

```bash
python -m news_crawler.scripts.reset_db

```

###3. 手动运行任务**执行采集与 AI 分析：**

```bash
python -m news_crawler ingest
# 或使用命令别名
news-crawler ingest

```

**执行发布：**

```bash
python -m news_crawler publish
# 或使用命令别名
news-crawler publish

```

###4. 运行测试项目包含完整的单元测试和集成测试：

```bash
# 运行单元测试（Mock API，无需联网）
pytest

# 运行真实网络测试（需要配置 .env 中的 AZURE_PROXY 等）
pytest -m live

```

---

##⚙️ 配置指南 | Configuration###核心环境变量 (.env)| 变量名 | 说明 | 示例 / 默认值 |
| --- | --- | --- |
| `DB_BACKEND` | 数据库类型 | `postgres` 或 `sqlite` |
| `DB_URI` | 数据库连接串 (Postgres) | `postgresql://user:pass@host:5432/db` |
| `AI_API_KEY` | OpenAI 兼容 API 密钥 | `sk-xxxxxxxx` |
| `AI_URL` | AI Base URL | `https://api.openai.com/v1` |
| `AI_MODEL` | 使用的模型名称 | `gpt-4o-mini`, `qwen-flash` |
| `GITHUB_TOKEN` | GitHub Personal Access Token | `ghp_xxxxxxxx` |
| `REPO_NAME` | 目标发布仓库 | `username/my-daily-news` |
| `AZURE_PROXY` | 爬虫使用的 HTTP 代理 | `http://127.0.0.1:10808` |

###修改订阅源 (RSS Feeds)订阅源配置位于源代码中，修改后需重启服务：

文件位置: `news_crawler/core/config.py`

```python
RSS_CATEGORIES = {
    "Math_Research": {
        "ArXiv_Math_CO": "http://export.arxiv.org/rss/math.CO",
        "Terry_Tao": "https://terrytao.wordpress.com/feed/",
        # ... 在此添加你的订阅源
    },
    "NetTech_Hardcore": {
        "HackerNews": "https://news.ycombinator.com/rss",
        # ...
    }
}

```

###修改 AI 策略 (Prompts)你可以为不同的板块定制不同的 AI 人格和评分标准。

文件位置: `news_crawler/core/category_strategies.py`

例如，修改 `Math_Research` 的 Prompt，让它更关注证明过程的创新性。

---

##📂 项目结构```text
.
├── news_crawler/
│   ├── core/           # 核心逻辑 (爬虫、数据库、配置、策略)
│   ├── services/       # 业务服务 (AI分析、GitHub发布、邮件通知)
│   ├── workers/        # 具体执行者 (RSS解析)
│   ├── dtos/           # 数据传输对象
│   ├── ingest.py       # 采集入口
│   └── publish.py      # 发布入口
├── tests/              # 测试用例
├── docker-compose.yml  # Docker 编排
├── Dockerfile          # 镜像构建
├── my-crontab          # 定时任务配置
└── pyproject.toml      # 项目依赖管理

```

##📄 License本项目采用 [MIT License](https://www.google.com/search?q=LICENSE) 开源。