# 文件路径：/app/tests/test_ai.py
import pytest
import os
from unittest.mock import MagicMock

from news_crawler.services.ai_service import _process_single_article_logic, get_ai_summary
from news_crawler.core.category_strategies import (
    get_strategy,
    CATEGORY_STRATEGIES,
    CategoryStrategy,
)

# 模拟的 AI 返回内容 (包含摘要、Tags、Score)
MOCK_AI_RESPONSE = """
摘要内容。
|TAGS| Linux, Kernel
|SCORE| 85
"""

def test_process_logic_parsing(mocker):
    """
    [单元测试] 测试正则解析逻辑是否正确
    不消耗 API 额度，通过 Mock 模拟 AI 返回
    """
    # 1. Mock get_ai_summary 函数
    mocker.patch('news_crawler.services.ai_service.get_ai_summary', return_value=MOCK_AI_RESPONSE)

    # 2. 运行逻辑
    result = _process_single_article_logic(
        art_id=1,
        content_text="原文内容...",
        category="Tech",
        title="Linux News"
    )

    # 3. 断言 (机器自动检查，不需要人眼看)
    assert result["status"] == "success"
    assert result["score"] == 85
    assert "Linux" in result["tags"]

def test_process_logic_filtering(mocker):
    """
    [单元测试] 测试广告过滤逻辑
    """
    mocker.patch('news_crawler.services.ai_service.get_ai_summary', return_value="PASS")
    
    result = _process_single_article_logic(1, "广告", "Tech", "Ad")
    assert result["status"] == "filtered"
    assert result["score"] == 0

@pytest.mark.live
def test_ai_connectivity_real():
    """
    [真实测试] 真正调用 API
    运行命令: pytest -m live
    """
    if os.getenv("AI_API_KEY", "").startswith("sk-mock"):
        pytest.skip("使用的是 Mock Key，跳过真实 API 调用")
        
    response = get_ai_summary("测试文本", "测试")
    assert "API Key missing" not in response
    assert len(response) > 0


# ============================================================
# 策略模块测试
# ============================================================

class TestCategoryStrategies:
    """测试分类策略模块"""

    def test_all_categories_have_strategy(self):
        """确保所有板块都有对应策略"""
        expected_categories = [
            "HotNews_CN",
            "Epochal_Global", 
            "NetTech_Hardcore",
            "AI_ML_Research",
            "Math_Research",
        ]
        for cat in expected_categories:
            strategy = get_strategy(cat)
            assert strategy is not None
            assert strategy.name == cat

    def test_strategy_has_required_fields(self):
        """测试策略包含所有必要字段"""
        for name, strategy in CATEGORY_STRATEGIES.items():
            assert isinstance(strategy, CategoryStrategy)
            assert strategy.name == name
            assert len(strategy.display_name) > 0
            assert len(strategy.prompt) > 50
            assert 1000 <= strategy.max_input_chars <= 3000
            assert isinstance(strategy.score_weights, dict)

    def test_unknown_category_returns_default(self):
        """未知分类应返回默认策略"""
        strategy = get_strategy("UnknownCategory")
        assert strategy.name == "NetTech_Hardcore"

    def test_max_input_chars_varies_by_category(self):
        """不同板块应有不同的token限制"""
        hotnews = get_strategy("HotNews_CN")
        epochal = get_strategy("Epochal_Global")
        math = get_strategy("Math_Research")
        
        # 舆情热点用最短的截断（1500）
        assert hotnews.max_input_chars < epochal.max_input_chars
        # 世界时政用最长的截断（2500）
        assert epochal.max_input_chars >= math.max_input_chars

    def test_prompts_are_category_specific(self):
        """每个板块的prompt应包含特定关键词"""
        hotnews = get_strategy("HotNews_CN")
        math = get_strategy("Math_Research")
        ai = get_strategy("AI_ML_Research")
        
        assert "热度" in hotnews.prompt
        assert "学术" in math.prompt
        assert "AI" in ai.prompt or "ML" in ai.prompt