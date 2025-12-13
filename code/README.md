# news_crawler

一个可自部署的新闻采集 + AI 摘要 + GitHub Pages 日报发布脚本。

## 1. 配置

- 复制并填写环境变量：
  - `cp .env.example .env`

## 2. 安装依赖

- 直接安装依赖（最简单）：
  - `pip install -r requirements.txt`

- 或者安装为可执行包（推荐，标准化）：
  - `pip install -e .`

说明：项目会使用 `python-dotenv` 自动加载同目录下的 `.env`。

## 3. 运行

- 标准运行方式（推荐）：
  - `python -m news_crawler ingest`
  - `python -m news_crawler publish`

- 安装为命令后：
  - `news-crawler ingest`
  - `news-crawler publish`

- 兼容旧入口（仍可用）：
  - `python main_ingest.py`
  - `python main_publish.py`

## 4. 测试

- 离线测试（默认，不会真实联网）：
  - `pytest`
- 真实联网测试：
  - `pytest -m live`
