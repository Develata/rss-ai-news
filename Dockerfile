FROM python:3.10-slim

# 1. 设置时区和环境变量
ENV TZ=Asia/Shanghai
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# 1.1 pip 使用国内镜像源（默认清华），可通过 build args 覆盖
ARG PIP_INDEX_URL=https://pypi.tuna.tsinghua.edu.cn/simple
ARG PIP_TRUSTED_HOST=pypi.tuna.tsinghua.edu.cn
ENV PIP_INDEX_URL=${PIP_INDEX_URL}
ENV PIP_TRUSTED_HOST=${PIP_TRUSTED_HOST}
ENV PIP_DISABLE_PIP_VERSION_CHECK=1
ENV PIP_NO_CACHE_DIR=1
ENV PIP_PREFER_BINARY=1

RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

WORKDIR /app

# 2. 安装系统依赖
# 2.0 apt 使用国内镜像源（默认清华），可通过 build args 覆盖
ARG APT_MIRROR=mirrors.tuna.tsinghua.edu.cn

RUN set -eux; \
    if [ -f /etc/apt/sources.list.d/debian.sources ]; then \
        sed -i -E \
          -e "s|https?://deb.debian.org/debian|http://${APT_MIRROR}/debian|g" \
          -e "s|https?://deb.debian.org/debian-security|http://${APT_MIRROR}/debian-security|g" \
          -e "s|https?://security.debian.org/debian-security|http://${APT_MIRROR}/debian-security|g" \
          /etc/apt/sources.list.d/debian.sources; \
    fi; \
    if [ -f /etc/apt/sources.list ]; then \
        sed -i -E \
          -e "s|https?://deb.debian.org/debian|http://${APT_MIRROR}/debian|g" \
          -e "s|https?://deb.debian.org/debian-security|http://${APT_MIRROR}/debian-security|g" \
          -e "s|https?://security.debian.org/debian-security|http://${APT_MIRROR}/debian-security|g" \
          /etc/apt/sources.list; \
    fi; \
    apt-get update && \
    apt-get install -y --no-install-recommends \
        cron \
        procps \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# 2.1 写入全局 pip 配置（容器内手动 pip 也走同一镜像源）
RUN printf "[global]\nindex-url = %s\ntrusted-host = %s\n" "$PIP_INDEX_URL" "$PIP_TRUSTED_HOST" > /etc/pip.conf

# 3. 安装 Python 依赖
COPY pyproject.toml README.md ./

# 先安装 tomli（Python 3.10 需要）
RUN pip install --no-cache-dir tomli

# 提取依赖列表
RUN python - <<'PY' > /tmp/requirements.txt
import pathlib
import sys

# Python 3.11+ 有内置 tomllib，否则使用 tomli
if sys.version_info >= (3, 11):
    import tomllib
else:
    import tomli as tomllib

data = tomllib.loads(pathlib.Path('pyproject.toml').read_text(encoding='utf-8'))
deps = data.get('project', {}).get('dependencies', [])
print("\n".join(deps))
PY

RUN pip install --no-cache-dir -r /tmp/requirements.txt

# 3.1 安装本项目（不重复安装依赖，避免代码改动导致全量重装）
COPY news_crawler ./news_crawler
RUN pip install --no-cache-dir --no-deps .

# 4. 复制配置文件
COPY my-crontab /etc/cron.d/my-crontab
COPY entrypoint.sh /entrypoint.sh

# 5. 权限设置
RUN chmod 0644 /etc/cron.d/my-crontab && \
    crontab /etc/cron.d/my-crontab && \
    chmod +x /entrypoint.sh && \
    mkdir -p /app/logs

# 6. 健康检查
HEALTHCHECK --interval=5m --timeout=10s --start-period=30s --retries=3 \
    CMD pgrep cron > /dev/null || exit 1

ENTRYPOINT ["/entrypoint.sh"]
