#!/usr/bin/env bash
set -euo pipefail

# Ensure logs directory exists
mkdir -p /app/logs

# Export environment variables to a file for cron to source
# This ensures cron jobs can access Docker environment variables
printenv | grep -E '^(DB_|MAIL_|AI_|GITHUB_|AZURE_|REPO_|TARGET_|TZ|PYTHONPATH|NO_PROXY)' > /etc/environment

# Also create a shell-sourceable env file for cron jobs
echo '#!/bin/bash' > /app/.docker_env
printenv | grep -E '^(DB_|MAIL_|AI_|GITHUB_|AZURE_|REPO_|TARGET_|TZ|PYTHONPATH|NO_PROXY)' | sed 's/^/export /' >> /app/.docker_env
chmod +x /app/.docker_env

echo "[✅ entrypoint] Environment variables exported for cron"
echo "[✅ entrypoint] Starting cron daemon..."

# Start cron in foreground (PID 1) so container stays alive
exec cron -f
