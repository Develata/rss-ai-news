from __future__ import annotations

import os
import urllib.parse
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path


def _getenv(name: str, default: str | None = None) -> str | None:
    value = os.getenv(name)
    if value is None:
        return default
    value = value.strip()
    return value if value != "" else default


def _getenv_int(name: str, default: int) -> int:
    raw = _getenv(name)
    if raw is None:
        return default
    try:
        return int(raw)
    except ValueError:
        return default


def _getenv_float(name: str, default: float) -> float:
    raw = _getenv(name)
    if raw is None:
        return default
    try:
        return float(raw)
    except ValueError:
        return default


@dataclass(frozen=True)
class RuntimeSettings:
    tz: str
    no_proxy: str
    log_dir: str


@dataclass(frozen=True)
class NetworkSettings:
    azure_proxy: str | None
    rsshub_base_url: str | None


@dataclass(frozen=True)
class DatabaseSettings:
    backend: str
    uri: str | None
    sqlite_path: str
    host: str | None
    port: int
    user: str | None
    password: str | None
    name: str
    sslmode: str | None

    def build_uri(self) -> str | None:
        if self.uri:
            return self.uri

        backend = (self.backend or "postgres").strip().lower()
        if backend == "sqlite":
            raw_path = (self.sqlite_path or "./data/news_crawler.db").strip()
            if raw_path == ":memory:":
                return "sqlite+pysqlite:///:memory:"
            path = Path(raw_path).expanduser()
            if not path.is_absolute():
                path = (Path.cwd() / path).resolve()
            # sqlite URI: 绝对路径需要 4 个斜杠
            return f"sqlite+pysqlite:///{path.as_posix()}"

        if not (self.host and self.user and self.password):
            return None
        safe_pass = urllib.parse.quote_plus(self.password)
        ssl = self.sslmode or "require"
        return f"postgresql://{self.user}:{safe_pass}@{self.host}:{self.port}/{self.name}?sslmode={ssl}"


@dataclass(frozen=True)
class MailSettings:
    host: str | None
    port: int
    user: str | None
    password: str | None
    to: str | None
    from_name: str
    to_name: str


@dataclass(frozen=True)
class AISettings:
    base_url: str | None
    api_key: str | None
    model: str | None
    max_workers: int
    base_delay: float
    max_retries: int


@dataclass(frozen=True)
class GitHubSettings:
    token: str | None
    repo_name: str | None
    target_folder: str


@dataclass(frozen=True)
class Settings:
    runtime: RuntimeSettings
    network: NetworkSettings
    db: DatabaseSettings
    mail: MailSettings
    ai: AISettings
    github: GitHubSettings


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    runtime = RuntimeSettings(
        tz=_getenv("TZ", "Asia/Shanghai") or "Asia/Shanghai",
        no_proxy=_getenv("NO_PROXY", "127.0.0.1,localhost") or "127.0.0.1,localhost",
        log_dir=_getenv("LOG_DIR", "./logs") or "./logs",
    )

    network = NetworkSettings(
        azure_proxy=_getenv("AZURE_PROXY"),
        rsshub_base_url=_getenv("RSSHUB_BASE_URL"),
    )

    db = DatabaseSettings(
        backend=_getenv("DB_BACKEND", "postgres") or "postgres",
        uri=_getenv("DB_URI"),
        sqlite_path=_getenv("DB_SQLITE_PATH", "./data/news_crawler.db") or "./data/news_crawler.db",
        host=_getenv("DB_HOST"),
        port=_getenv_int("DB_PORT", 5432),
        user=_getenv("DB_USER"),
        password=_getenv("DB_PASS"),
        name=_getenv("DB_NAME", "postgres") or "postgres",
        sslmode=_getenv("DB_SSLMODE"),
    )

    mail = MailSettings(
        host=_getenv("MAIL_HOST"),
        port=_getenv_int("MAIL_PORT", 465),
        user=_getenv("MAIL_USER"),
        password=_getenv("MAIL_PASS"),
        to=_getenv("MAIL_TO"),
        from_name=_getenv("MAIL_FROM_NAME", "AI情报员") or "AI情报员",
        to_name=_getenv("MAIL_TO_NAME", "订阅者") or "订阅者",
    )

    ai = AISettings(
        base_url=_getenv("AI_URL"),
        api_key=_getenv("AI_API_KEY"),
        model=_getenv("AI_MODEL"),
        max_workers=_getenv_int("AI_MAX_WORKERS", 1),
        base_delay=_getenv_float("AI_BASE_DELAY", 12.0),
        max_retries=_getenv_int("AI_MAX_RETRIES", 3),
    )

    github = GitHubSettings(
        token=_getenv("GITHUB_TOKEN"),
        repo_name=_getenv("REPO_NAME"),
        target_folder=(_getenv("TARGET_FOLDER", "") or "").strip("/"),
    )

    return Settings(
        runtime=runtime,
        network=network,
        db=db,
        mail=mail,
        ai=ai,
        github=github,
    )
