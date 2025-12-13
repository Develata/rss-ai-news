"""
板块策略配置模块

每个板块有独立的：
- AI Prompt（针对性评分标准）
- 评分权重
- 输入文本截断长度（优化token）
"""

from dataclasses import dataclass
from typing import Dict


@dataclass(frozen=True)
class CategoryStrategy:
    """板块策略配置"""
    name: str                    # 板块名称
    display_name: str            # 显示名称
    prompt: str                  # AI Prompt
    max_input_chars: int         # 输入文本最大字符数（控制token）
    score_weights: Dict[str, float]  # 评分权重说明


# ============================================================
# 舆情热点 - 只关心讨论热度
# ============================================================
HOTNEWS_CN_STRATEGY = CategoryStrategy(
    name="HotNews_CN",
    display_name="舆情热点",
    max_input_chars=1500,
    score_weights={"热度": 1.0},
    prompt="""你是舆情分析师。分析以下内容的**讨论热度**。

任务：
1. 【摘要】一句话概括（<60字）
2. 【热度评分】0-100分
   - 90-100: 全网刷屏级热点
   - 70-89: 热搜榜单热点
   - 50-69: 有一定讨论度
   - 0-49: 普通资讯
3. 【标签】1-2个话题标签

广告/无意义内容返回：PASS

输出格式：
[摘要]
|TAGS|标签1, 标签2
|SCORE|分数"""
)


# ============================================================
# 世界时政 - 热度 + 世界影响度 + 事件重要性
# ============================================================
EPOCHAL_GLOBAL_STRATEGY = CategoryStrategy(
    name="Epochal_Global",
    display_name="世界时事",
    max_input_chars=2500,
    score_weights={"热度": 0.2, "世界影响": 0.4, "事件重要性": 0.4},
    prompt="""你是国际时政分析师。综合评估以下新闻的重要性。

评分维度（加权）：
- 讨论热度 (20%)
- 对世界格局的影响 (40%)
- 事件本身的历史重要性 (40%)

任务：
1. 【摘要】一句话概括核心信息（<80字）
2. 【综合评分】0-100分
   - 90-100: 改变世界格局的重大事件（战争爆发、重大协议）
   - 70-89: 区域性重大事件/大国重要政策
   - 50-69: 值得关注的国际动态
   - 0-49: 普通国际新闻
3. 【标签】1-2个标签（如：地缘政治、经济制裁）

广告返回：PASS

输出格式：
[摘要]
|TAGS|标签1, 标签2
|SCORE|分数"""
)


# ============================================================
# 科技新闻（硬核技术）- 技术影响 + 重要性
# ============================================================
NETTECH_HARDCORE_STRATEGY = CategoryStrategy(
    name="NetTech_Hardcore",
    display_name="科技新闻",
    max_input_chars=2000,
    score_weights={"技术影响": 0.5, "重要性": 0.5},
    prompt="""你是硬核技术分析师。评估以下技术新闻的价值。

评分维度：
- 对技术发展的影响力 (50%)
- 技术突破的重要性 (50%)
（不考虑热度）

任务：
1. 【摘要】一句话技术要点（<80字）
2. 【技术评分】0-100分
   - 90-100: 里程碑式技术突破（新架构、重大版本）
   - 70-89: 重要技术更新/安全漏洞
   - 50-69: 值得关注的技术动态
   - 0-49: 常规更新/讨论
3. 【标签】技术标签（如：Linux内核、Rust、安全漏洞）

广告/招聘返回：PASS

输出格式：
[摘要]
|TAGS|标签1, 标签2
|SCORE|分数"""
)


# ============================================================
# AI/ML 研究 - 技术影响 + 学术重要性
# ============================================================
AI_ML_RESEARCH_STRATEGY = CategoryStrategy(
    name="AI_ML_Research",
    display_name="AI & ML",
    max_input_chars=2500,
    score_weights={"技术影响": 0.5, "学术重要性": 0.5},
    prompt="""你是AI研究分析师。评估以下AI/ML内容的学术与产业价值。

评分维度：
- 对AI领域的影响力 (50%)
- 学术/产业重要性 (50%)
（不考虑热度）

任务：
1. 【摘要】一句话概括核心贡献（<80字）
2. 【研究评分】0-100分
   - 90-100: 范式级突破（GPT级别、新架构）
   - 70-89: 重要模型/方法/开源项目
   - 50-69: 有价值的研究/应用
   - 0-49: 常规研究/博客
3. 【标签】如：Transformer、大模型、强化学习

广告/招聘返回：PASS

输出格式：
[摘要]
|TAGS|标签1, 标签2
|SCORE|分数"""
)


# ============================================================
# 数学研究 - 忽视热度，着重学术本身
# ============================================================
MATH_RESEARCH_STRATEGY = CategoryStrategy(
    name="Math_Research",
    display_name="Math News",
    max_input_chars=2000,
    score_weights={"学术价值": 1.0},
    prompt="""你是数学研究分析师。评估以下数学论文/内容的学术价值。

评分标准（完全忽略热度，只看学术本身）：
- 数学深度与创新性
- 对相关领域的推动作用
- 证明技巧的优美程度

任务：
1. 【摘要】用通俗语言概括数学内容（<80字）
2. 【学术评分】0-100分
   - 90-100: 重大猜想证明/开创性工作
   - 70-89: 领域内重要进展
   - 50-69: 有价值的研究结果
   - 0-49: 常规论文/讨论
3. 【标签】数学分支（如：组合数学、概率论、优化）

非数学内容返回：PASS

输出格式：
[摘要]
|TAGS|标签1, 标签2
|SCORE|分数"""
)


# ============================================================
# 策略注册表
# ============================================================
CATEGORY_STRATEGIES: Dict[str, CategoryStrategy] = {
    "HotNews_CN": HOTNEWS_CN_STRATEGY,
    "Epochal_Global": EPOCHAL_GLOBAL_STRATEGY,
    "NetTech_Hardcore": NETTECH_HARDCORE_STRATEGY,
    "AI_ML_Research": AI_ML_RESEARCH_STRATEGY,
    "Math_Research": MATH_RESEARCH_STRATEGY,
}


def get_strategy(category: str) -> CategoryStrategy:
    """获取板块策略，未注册则返回默认策略"""
    if category in CATEGORY_STRATEGIES:
        return CATEGORY_STRATEGIES[category]
    return NETTECH_HARDCORE_STRATEGY
