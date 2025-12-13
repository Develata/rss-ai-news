import hashlib


def compute_hash(text):
    """MD5 指纹计算"""
    if not text:
        return ""
    return hashlib.md5(text.encode("utf-8", errors="ignore")).hexdigest()


def chunker(seq, size):
    """分片生成器"""
    return (seq[pos : pos + size] for pos in range(0, len(seq), size))


def truncate_text(text: str, max_chars: int) -> str:
    """
    智能截断文本至指定字符数。
    - 优先在句号/分号等自然断点截断
    - 避免截断到单词/汉字中间
    """
    if not text or len(text) <= max_chars:
        return text or ""

    # 找到截断点附近的自然断点
    search_start = max(0, max_chars - 100)
    search_end = max_chars

    best_pos = max_chars
    # 按优先级查找断点：句号 > 分号 > 逗号 > 空格
    for delimiter in ["。", ".", "；", ";", "，", ",", " "]:
        pos = text.rfind(delimiter, search_start, search_end)
        if pos > 0:
            best_pos = pos + 1  # 包含分隔符
            break

    return text[:best_pos].strip()
