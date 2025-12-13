# ====================================================
# 1. RSS 源配置 (数据采集池)
# ====================================================
# 策略说明：
# 1. [直连]: 官方提供的标准 RSS，由 Python 爬虫直接通过代理抓取 (性能最高)。
# 2. [RSSHub]: 官方无 RSS 或反爬严重的网站，由 RSSHub (Puppeteer) 抓取并转换。
# ====================================================

RSS_CATEGORIES = {
    "HotNews_CN": {
        "Zhihu_Daily": "{RSSHUB}/zhihu/daily",
        "Weibo_Hot": "{RSSHUB}/weibo/search/hot",
        "Bilibili_Hot": "{RSSHUB}/bilibili/popular/all",
        "SSPai": "https://sspai.com/feed",
        "Kr36": "https://36kr.com/feed",
    },
    "Epochal_Global": {
        "Chinanews": "https://www.chinanews.com.cn/rss/china.xml",
        "Reuters_World": "{RSSHUB}/reuters/world",
        "Reuters_news": "https://ir.thomsonreuters.com/rss/news-releases.xml",
        "Zaobao_Realtime": "{RSSHUB}/zaobao/realtime/world",
        "AP_TopNews": "{RSSHUB}/apnews/topics/apf-topnews",
        "Foreign_Affairs": "https://www.foreignaffairs.com/rss.xml",
    },
    "NetTech_Hardcore": {
        "HackerNews": "https://news.ycombinator.com/rss",
        "Solidot": "http://feeds.feedburner.com/solidot",
        "OSNews": "https://www.osnews.com/feed/",
        "Phoronix": "https://www.phoronix.com/rss.php",
    },
    "Math_Research": {
        "ArXiv_Math_CO": "http://export.arxiv.org/rss/math.CO",
        "ArXiv_Math_PR": "http://export.arxiv.org/rss/math.PR",
        "ArXiv_CS_DM": "http://export.arxiv.org/rss/cs.DM",
        "ArXiv_Math_OC": "http://export.arxiv.org/rss/math.OC",
        "Terry_Tao": "https://terrytao.wordpress.com/feed/",
    },
    "AI_ML_Research": {
        "Microsoft_AI": "https://blogs.microsoft.com/ai/feed/",
        "Pytorch_Blog": "https://pytorch.org/blog/feed.xml",
        "Google_AI": "http://googleaiblog.blogspot.com/atom.xml",
        "OpenAI_Blog": "https://openai.com/blog/rss.xml",
        "DeepMind": "https://deepmind.google/blog/rss.xml",
        "NVIDIA_Blog": "https://blogs.nvidia.com/feed/",
        "HuggingFace": "https://huggingface.co/blog/feed.xml",
        "Meituan_Tech": "https://tech.meituan.com/feed/",
        "Algorithm_Way": "https://www.deeplearn.me/feed",
    },
}


# ====================================================
# Runtime overrides
# ====================================================
try:
    from news_crawler.core.settings import get_settings

    _rsshub = get_settings().network.rsshub_base_url or "http://127.0.0.1:1200"
    _rsshub = _rsshub.rstrip("/")

    for _cat, _sources in RSS_CATEGORIES.items():
        for _name, _url in list(_sources.items()):
            if "{RSSHUB}" in _url:
                _sources[_name] = _url.format(RSSHUB=_rsshub)
except Exception:
    pass


# ====================================================
# 2. 报表配置
# ====================================================

REPORT_CONFIGS = {
    "HotNews_CN": {
        "title_prefix": "舆情热点",
        "folder": "舆情热点",
        "description": "国内民众关注度极高的社会热点与科技资讯。",
    },
    "Epochal_Global": {
        "title_prefix": "世界时事",
        "folder": "世界时事",
        "description": "战争、制裁、大国博弈及国际重大新闻。",
    },
    "NetTech_Hardcore": {
        "title_prefix": "科技新闻",
        "folder": "科技新闻",
        "description": "新架构、Linux内核、芯片突破及硬核软件工程。",
    },
    "Math_Research": {
        "title_prefix": "Math News",
        "folder": "Math",
        "description": "数学专业动态、优化控制理论及顶刊摘要。",
    },
    "AI_ML_Research": {
        "title_prefix": "AI & ML",
        "folder": "AI_ML",
        "description": "全球顶级AI实验室、大模型及机器学习前沿研究。",
    },
}


# ====================================================
# 3. AI Prompts (已迁移到 category_strategies.py)
# ====================================================
# AI prompts 现在根据分类动态选择，详见 news_crawler.core.category_strategies
