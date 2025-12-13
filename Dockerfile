FROM python:3.13-slim

# 1. 设置时区和环境变量
ENV TZ=Asia/Shanghai
ENV PYTHONPATH=/app/code
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

WORKDIR /app

# 2. 安装系统依赖（slim 镜像需要额外安装 gcc 等编译工具）
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        cron \
        gcc \
        libpq-dev \
        curl \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# 3. 安装 Python 依赖
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

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
