from __future__ import annotations

import logging
import os
from collections.abc import Mapping
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Any

import tomllib

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class ReportConfig:
    title_prefix: str
    folder: str
    description: str
    max_items: int = 10
    excerpt_max_titles: int = 15
    excerpt_prompt: str | None = None
    badge_enabled: bool = True


@dataclass(frozen=True)
class AIConfig:
    display_name: str
    prompt: str
    max_input_chars: int


@dataclass(frozen=True)
class CategoryConfig:
    key: str
    order: int
    rss: dict[str, str]
    ai: AIConfig
    report: ReportConfig


def _as_table(value: Any, where: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise ValueError(f"Invalid config: expected table at {where}")
    return value


def _as_str(value: Any, where: str) -> str:
    if not isinstance(value, str) or value.strip() == "":
        raise ValueError(f"Invalid config: expected non-empty string at {where}")
    return value.strip()


def _as_int(value: Any, where: str, *, minimum: int | None = None, default: int | None = None) -> int:
    if value is None:
        if default is None:
            raise ValueError(f"Invalid config: expected int at {where}")
        return default
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError(f"Invalid config: expected int at {where}")
    if minimum is not None and value < minimum:
        raise ValueError(f"Invalid config: expected {where} >= {minimum}")
    return value


def _as_bool(value: Any, where: str, *, default: bool) -> bool:
    if value is None:
        return default
    if not isinstance(value, bool):
        raise ValueError(f"Invalid config: expected bool at {where}")
    return value


def _as_opt_str(value: Any, where: str) -> str | None:
    if value is None:
        return None
    if not isinstance(value, str):
        raise ValueError(f"Invalid config: expected string at {where}")
    value = value.strip()
    return value if value else None


def _package_categories_dir() -> Path:
    """
    优先从环境变量 CONFIG_DIR 读取配置路径。
    如果未设置或路径不存在，则回退到包内的默认路径。

    这样可以在 Docker 部署时挂载外部配置目录，无需重建镜像。
    """
    # 1. 优先读取环境变量
    custom_dir = os.getenv("CONFIG_DIR")
    if custom_dir:
        custom_path = Path(custom_dir).resolve()
        if custom_path.exists() and custom_path.is_dir():
            logger.info(f"Using external config directory: {custom_path}")
            return custom_path
        else:
            logger.warning(f"CONFIG_DIR set but path does not exist: {custom_path}")

    # 2. 回退到包内默认路径
    default_path = Path(__file__).resolve().parents[1] / "categories"
    logger.info(f"Using default package config directory: {default_path}")
    return default_path


def _load_one(path: Path) -> CategoryConfig:
    data = tomllib.loads(path.read_text(encoding="utf-8"))

    cat = _as_table(data.get("category"), f"{path.name}.[category]")
    rss = _as_table(data.get("rss"), f"{path.name}.[rss]")
    ai = _as_table(data.get("ai"), f"{path.name}.[ai]")
    report = _as_table(data.get("report"), f"{path.name}.[report]")

    key = _as_str(cat.get("key"), f"{path.name}.[category].key")
    order = _as_int(cat.get("order"), f"{path.name}.[category].order", default=100)

    rss_map: dict[str, str] = {}
    for name, url in rss.items():
        rss_map[_as_str(name, f"{path.name}.[rss].<name>")] = _as_str(
            url, f"{path.name}.[rss].{name}"
        )

    ai_cfg = AIConfig(
        display_name=_as_str(ai.get("display_name"), f"{path.name}.[ai].display_name"),
        prompt=_as_str(ai.get("prompt"), f"{path.name}.[ai].prompt"),
        max_input_chars=_as_int(
            ai.get("max_input_chars"), f"{path.name}.[ai].max_input_chars", minimum=100, default=2000
        ),
    )

    report_cfg = ReportConfig(
        title_prefix=_as_str(report.get("title_prefix"), f"{path.name}.[report].title_prefix"),
        folder=_as_str(report.get("folder"), f"{path.name}.[report].folder"),
        description=_as_str(report.get("description", ""), f"{path.name}.[report].description"),
        max_items=_as_int(report.get("max_items"), f"{path.name}.[report].max_items", minimum=1, default=10),
        excerpt_max_titles=_as_int(
            report.get("excerpt_max_titles"),
            f"{path.name}.[report].excerpt_max_titles",
            minimum=1,
            default=15,
        ),
        excerpt_prompt=_as_opt_str(report.get("excerpt_prompt"), f"{path.name}.[report].excerpt_prompt"),
        badge_enabled=_as_bool(report.get("badge_enabled"), f"{path.name}.[report].badge_enabled", default=True),
    )

    return CategoryConfig(
        key=key,
        order=order,
        rss=rss_map,
        ai=ai_cfg,
        report=report_cfg,
    )


@lru_cache(maxsize=1)
def load_category_configs() -> list[CategoryConfig]:
    root = _package_categories_dir()
    if not root.exists():
        raise RuntimeError(f"Category config dir not found: {root}")

    configs: list[CategoryConfig] = []
    seen: set[str] = set()

    for path in sorted(root.glob("*.toml")):
        if path.name.startswith("_"):
            continue

        try:
            cfg = _load_one(path)
            if cfg.key in seen:
                raise ValueError(f"Duplicate category key: {cfg.key}")
            seen.add(cfg.key)
            configs.append(cfg)
        except ValueError as e:
            # 配置验证错误（格式错误、字段校验失败等）
            logger.error(f"Config validation error in {path.name}: {e}")
            logger.info(f"Hint: Check TOML format and required fields in {path.name}")
            continue
        except Exception as e:
            # 其他错误（文件读取、解析等）
            logger.error(f"Config load error in {path.name}: {type(e).__name__}: {e}")
            logger.debug(f"File path: {path}")
            continue

    configs.sort(key=lambda c: (c.order, c.key))

    if not configs:
        logger.warning(f"No valid category config files loaded from: {root}")
        logger.info("Ensure directory contains .toml files (not starting with underscore)")

    return configs


@lru_cache(maxsize=1)
def get_category_config_map() -> dict[str, CategoryConfig]:
    return {c.key: c for c in load_category_configs()}


def get_category_config(category_key: str) -> CategoryConfig | None:
    return get_category_config_map().get(category_key)
