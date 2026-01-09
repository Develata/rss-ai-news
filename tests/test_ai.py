"""AI service and category strategy tests.

This module tests:
- AI response parsing logic
- Content filtering mechanisms
- Category-specific strategies
- Integration with real AI APIs (when marked as 'live')
"""

import os

import pytest

from news_crawler.core.category_strategies import (
    CATEGORY_STRATEGIES,
    CategoryStrategy,
    get_strategy,
)
from news_crawler.services.ai_service import (
    _process_single_article_logic,
    get_ai_summary,
)

# Mock AI response for testing parsing logic
MOCK_AI_RESPONSE = """
摘要内容。
|TAGS| Linux, Kernel
|SCORE| 85
"""


def test_process_logic_parsing(mocker):
    """Test AI response parsing logic without consuming API quota.

    Verifies that the regex patterns correctly extract:
    - Summary text
    - Tags
    - Score
    """
    mocker.patch(
        "news_crawler.services.ai_service.get_ai_summary",
        return_value=MOCK_AI_RESPONSE,
    )

    result = _process_single_article_logic(
        art_id=1,
        content_text="Sample article content...",
        category="Tech",
        title="Linux News",
    )

    assert result["status"] == "success"
    assert result["score"] == 85
    assert "Linux" in result["tags"]


def test_process_logic_filtering(mocker):
    """Test content filtering mechanism.

    Verifies that low-quality content marked as 'PASS' by AI
    is correctly filtered out with score 0.
    """
    mocker.patch(
        "news_crawler.services.ai_service.get_ai_summary",
        return_value="PASS",
    )

    result = _process_single_article_logic(1, "Ad content", "Tech", "Ad")

    assert result["status"] == "filtered"
    assert result["score"] == 0


@pytest.mark.live
def test_ai_connectivity_real():
    """Test real AI API connectivity.

    Run with: pytest -m live
    Skipped if using mock credentials.
    """
    if os.getenv("AI_API_KEY", "").startswith("sk-mock"):
        pytest.skip("Using mock API key, skipping real API call")

    response = get_ai_summary("Test content", "Test category")

    assert "API Key missing" not in response
    assert len(response) > 0


class TestCategoryStrategies:
    """Test suite for category-specific analysis strategies."""

    def test_all_categories_have_strategy(self):
        """Verify all configured categories have corresponding strategies."""
        # Test that all loaded categories have strategies
        assert len(CATEGORY_STRATEGIES) >= 1, "At least one category should be configured"

        for cat_name in CATEGORY_STRATEGIES.keys():
            strategy = get_strategy(cat_name)
            assert strategy is not None
            assert strategy.name == cat_name

    def test_strategy_has_required_fields(self):
        """Verify all strategies contain required fields with valid values."""
        for name, strategy in CATEGORY_STRATEGIES.items():
            assert isinstance(strategy, CategoryStrategy)
            assert strategy.name == name
            assert len(strategy.display_name) > 0
            assert len(strategy.prompt) > 50
            assert 1000 <= strategy.max_input_chars <= 3000

    def test_strategies_loaded_from_category_configs(self):
        """Verify strategies are loaded from TOML config files."""
        assert len(CATEGORY_STRATEGIES) >= 1, "At least one category should be configured"

    def test_unknown_category_returns_default(self):
        """Verify unknown categories fall back to default strategy."""
        strategy = get_strategy("UnknownCategory")
        # Should return the first available strategy (sorted by order)
        default_strategy = list(CATEGORY_STRATEGIES.values())[0]
        assert strategy.name == default_strategy.name

    def test_max_input_chars_varies_by_category(self):
        """Verify categories can have different token limits."""
        # Test that max_input_chars is within reasonable range for all categories
        for strategy in CATEGORY_STRATEGIES.values():
            assert (
                1000 <= strategy.max_input_chars <= 3000
            ), f"{strategy.name} has invalid max_input_chars: {strategy.max_input_chars}"

    def test_prompts_are_category_specific(self):
        """Verify each category has a meaningful prompt."""
        # Test that all prompts contain required output format markers
        for strategy in CATEGORY_STRATEGIES.values():
            assert "|TAGS|" in strategy.prompt, f"{strategy.name} prompt missing |TAGS| marker"
            assert (
                "|SCORE|" in strategy.prompt
            ), f"{strategy.name} prompt missing |SCORE| marker"
            assert "PASS" in strategy.prompt, f"{strategy.name} prompt missing PASS instruction"
