class ParsedItem:
    def __init__(
        self, title, link, summary, content_text, content_hash, source_name, category, created_at
    ):
        self.title = title
        self.link = link
        self.summary = summary
        self.content_text = content_text
        self.content_hash = content_hash
        self.source_name = source_name
        self.category = category
        self.created_at = created_at


class PseudoEntry:
    def __init__(self, title, link, summary):
        self.title = title
        self.link = link
        self.summary = summary
