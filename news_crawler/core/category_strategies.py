"""板块 AI 策略（动态加载）。

策略来源：news_crawler/categories/*.toml 的 [ai] 配置。
保留 get_strategy / CategoryStrategy 以兼容现有服务代码。
"""

from __future__ import annotations

from dataclasses import dataclass

from news_crawler.core.category_config_loader import get_category_config_map


@dataclass(frozen=True)
class CategoryStrategy:
    """板块策略配置"""
    name: str                    # 板块名称
    display_name: str            # 显示名称
    prompt: str                  # AI Prompt
    max_input_chars: int         # 输入文本最大字符数（控制token）
    # 评分权重已被简化掉（统一由 prompt 产出 |SCORE|）。


def _build_strategies() -> dict[str, CategoryStrategy]:
    out: dict[str, CategoryStrategy] = {}
    for key, cfg in get_category_config_map().items():
        out[key] = CategoryStrategy(
            name=key,
            display_name=cfg.ai.display_name,
            prompt=cfg.ai.prompt,
            max_input_chars=cfg.ai.max_input_chars,
        )
    return out


CATEGORY_STRATEGIES = _build_strategies()


def get_strategy(category: str) -> CategoryStrategy:
    """获取板块策略，未注册则返回默认策略"""
    if category in CATEGORY_STRATEGIES:
        return CATEGORY_STRATEGIES[category]
    if not CATEGORY_STRATEGIES:
        raise RuntimeError(
            "No category strategies loaded. Please add TOML files under news_crawler/categories/."
        )
    # 默认：优先用 NetTech_Hardcore，否则随便挑一个
    if "NetTech_Hardcore" in CATEGORY_STRATEGIES:
        return CATEGORY_STRATEGIES["NetTech_Hardcore"]
    return next(iter(CATEGORY_STRATEGIES.values()))
