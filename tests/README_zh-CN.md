# 测试文档

[English](README.md) | 简体中文

本目录包含 RSS AI News Crawler 项目的测试套件。

## 测试结构

```
tests/
├── conftest.py         # 共享 fixtures 和配置
├── test_ai.py          # AI 服务和策略测试
├── test_feeds.py       # RSS 订阅源连接测试
├── test_infra.py       # 基础设施测试（代理、邮件）
└── README.md           # 英文文档
└── README_zh-CN.md     # 本文件（中文文档）
```

## 运行测试

### 快速开始

```bash
# 运行所有单元测试（默认，跳过联网测试）
pytest

# 详细输出模式
pytest -v

# 运行特定测试文件
pytest tests/test_ai.py

# 运行特定测试用例
pytest tests/test_ai.py::test_process_logic_parsing
```

### 实时测试（需要网络）

实时测试需要真实的凭证和网络连接：

```bash
# 运行所有测试（包括联网测试）
pytest -m ""

# 仅运行实时测试
pytest -m "live"

# 排除实时测试（默认行为）
pytest -m "not live"
```

**警告**：实时测试会：
- 调用真实的 API（消耗配额/费用）
- 测试代理连接
- 尝试发送邮件
- 访问外部 RSS 源

运行实时测试前，请确保 `.env` 文件配置正确。

## 测试分类

### 单元测试（默认）
- **快速**：毫秒级执行
- **隔离**：使用 Mock，无外部依赖
- **安全**：不调用 API，不需要真实凭证

示例：
- `test_process_logic_parsing()` - 测试 AI 响应解析
- `test_strategy_has_required_fields()` - 测试配置验证

### 实时测试（`@pytest.mark.live`）
- **较慢**：依赖网络延迟
- **外部依赖**：需要真实服务（AI API、SMTP、RSS 源）
- **需要凭证**：需要有效的 API 密钥/令牌

示例：
- `test_ai_connectivity_real()` - 测试真实 AI API
- `test_rss_feed_connectivity()` - 测试 RSS 源可用性
- `test_email_sending_real()` - 测试 SMTP 邮件发送

## 配置说明

### Mock 凭证

默认情况下，测试使用 `conftest.py` 中定义的 Mock 凭证：
- `AI_API_KEY=sk-mock-key`
- `MAIL_HOST=smtp.mock.com`
- 等等

这可以防止单元测试时意外调用真实 API。

### 真实凭证

对于实时测试，请确保 `.env` 文件包含有效凭证：

```env
AI_API_KEY=sk-real-key-here
AI_URL=https://api.openai.com/v1
MAIL_HOST=smtp.gmail.com
MAIL_USER=your@email.com
MAIL_PASS=your-password
```

## CI/CD 集成

GitHub Actions 工作流（`.github/workflows/ci.yml`）会运行：
1. 仅单元测试（快速，无需凭证）
2. 多个 Python 版本（3.10-3.13）
3. 代码检查（ruff）

实时测试**默认不在** CI 中运行，以避免：
- 消耗 API 配额
- 暴露凭证
- 构建时间过长

## 代码覆盖率

生成测试覆盖率报告：

```bash
# 安装 pytest-cov
pip install pytest-cov

# 运行测试并生成覆盖率报告
pytest --cov=news_crawler --cov-report=html

# 查看报告
open htmlcov/index.html  # macOS
xdg-open htmlcov/index.html  # Linux
```

## 编写新测试

### 单元测试模板

```python
def test_my_function():
    """简要说明测试内容。"""
    # 准备 (Arrange)
    input_data = "test"
    
    # 执行 (Act)
    result = my_function(input_data)
    
    # 断言 (Assert)
    assert result == expected_value
```

### 实时测试模板

```python
@pytest.mark.live
def test_external_service():
    """测试真实外部服务。"""
    if os.getenv("SERVICE_KEY", "").startswith("mock"):
        pytest.skip("使用 Mock 凭证，跳过")
    
    result = call_external_service()
    assert result is not None
```

## 故障排除

### 测试失败："Connection Error"
- 检查是否意外运行了实时测试：`pytest -m "not live"`
- 验证代理设置：`echo $AZURE_PROXY`

### 测试失败："API Key Invalid"
- 实时测试需要 `.env` 中的真实凭证
- 单元测试不应访问外部 API（检查 Mock 是否生效）

### 导入错误
```bash
# 以可编辑模式安装
pip install -e .

# 或者设置 PYTHONPATH
export PYTHONPATH=/path/to/rss-ai-news
```

## 最佳实践

1. **优先编写单元测试** - 快速、可靠、无依赖
2. **谨慎使用实时测试** - 仅用于关键集成点
3. **Mock 外部服务** - 单元测试中避免 API 调用
4. **测试边界情况** - 空输入、错误、边界条件
5. **保持测试独立** - 测试之间无共享状态
6. **使用描述性命名** - `test_parse_valid_rss_feed` 而非 `test_1`

## 测试标记说明

项目使用 pytest 标记系统来分类测试：

```python
@pytest.mark.live        # 实时测试，需要网络和凭证
@pytest.mark.unit        # 单元测试（预留，可选）
@pytest.mark.integration # 集成测试（预留，可选）
```

运行特定标记的测试：
```bash
pytest -m live           # 仅实时测试
pytest -m "not live"     # 排除实时测试（默认）
```

## 参考资源

- [Pytest 文档](https://docs.pytest.org/)（官方）
- [Python 测试最佳实践](https://realpython.com/pytest-python-testing/)
- [测试驱动开发](https://zh.wikipedia.org/wiki/%E6%B5%8B%E8%AF%95%E9%A9%B1%E5%8A%A8%E5%BC%80%E5%8F%91)

## 常见问题

### Q: 为什么默认跳过实时测试？
**A**: 实时测试会消耗 API 配额、依赖外部服务，且执行较慢。单元测试足以验证大部分逻辑。

### Q: 如何在本地运行完整测试套件？
**A**: 配置好 `.env` 后，运行 `pytest -m ""`（空标记表示运行所有测试）。

### Q: CI 失败但本地通过？
**A**: 可能原因：
- CI 使用的 Python 版本不同
- 环境变量未设置
- 依赖版本不一致

解决方法：
```bash
# 使用与 CI 相同的 Python 版本测试
pyenv install 3.10
pyenv local 3.10
pytest
```

### Q: 如何添加新的测试文件？
**A**: 遵循命名约定：
- 文件名：`test_*.py`
- 测试函数：`test_*()`
- 测试类：`Test*`

pytest 会自动发现并运行这些测试。

## 测试输出示例

### 成功的单元测试
```
$ pytest tests/test_ai.py -v
===================== test session starts =====================
tests/test_ai.py::test_process_logic_parsing PASSED      [ 10%]
tests/test_ai.py::test_process_logic_filtering PASSED    [ 20%]
tests/test_ai.py::TestCategoryStrategies::test_all_categories_have_strategy PASSED [ 30%]
...
===================== 10 passed in 0.15s =====================
```

### 跳过的实时测试
```
$ pytest tests/test_ai.py::test_ai_connectivity_real -v
===================== test session starts =====================
tests/test_ai.py::test_ai_connectivity_real SKIPPED (Using mock API key)
===================== 1 skipped in 0.02s =====================
```

### 实时测试成功
```
$ pytest tests/test_ai.py::test_ai_connectivity_real -v -m live
===================== test session starts =====================
tests/test_ai.py::test_ai_connectivity_real PASSED
===================== 1 passed in 2.34s ======================
```

## 贡献指南

编写测试时请遵循：
1. **一个测试只验证一个行为**
2. **测试名称清晰表达意图**
3. **使用 Arrange-Act-Assert 模式**
4. **为实时测试添加 `@pytest.mark.live` 装饰器**
5. **添加有意义的文档字符串**

示例：
```python
def test_parse_valid_rss_returns_entries():
    """Test that valid RSS XML is parsed into entry objects."""
    # Arrange
    valid_rss = "<rss><channel><item><title>Test</title></item></channel></rss>"
    
    # Act
    entries = parse_rss(valid_rss)
    
    # Assert
    assert len(entries) == 1
    assert entries[0].title == "Test"
```

---

**提示**：测试是代码质量的保证。投入时间编写测试，将在未来节省数倍的调试时间。
