from html.parser import HTMLParser
import urllib.request

from app.collectors.base import BaseCollector, CollectedItem
from app.utils.security import validate_safe_url


class SimpleHTMLParser(HTMLParser):
    """Clean HTML text and title extractor."""
    def __init__(self):
        super().__init__()
        self.title: str = ""
        self.meta_description: str = ""
        self.paragraphs: list[str] = []
        self.in_title: bool = False
        self.in_paragraph: bool = False
        self.current_text: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]):
        tag_lower = tag.lower()
        if tag_lower == "title":
            self.in_title = True
        elif tag_lower == "p":
            self.in_paragraph = True
            self.current_text = []
        elif tag_lower == "meta":
            attr_dict = {k.lower(): (v or "") for k, v in attrs}
            if attr_dict.get("name") == "description":
                self.meta_description = attr_dict.get("content", "")

    def handle_endtag(self, tag: str):
        tag_lower = tag.lower()
        if tag_lower == "title":
            self.in_title = False
        elif tag_lower == "p":
            self.in_paragraph = False
            p_text = "".join(self.current_text).strip()
            if p_text:
                self.paragraphs.append(p_text)

    def handle_data(self, data: str):
        if self.in_title:
            self.title += data
        elif self.in_paragraph:
            self.current_text.append(data)


class WebCollector(BaseCollector):
    """Collector for standard web page HTML documents."""

    def __init__(self, timeout_seconds: int = 10, raw_html: str | None = None):
        self.timeout_seconds = timeout_seconds
        self.raw_html = raw_html

    def collect(self, target_url: str) -> list[CollectedItem]:
        validate_safe_url(target_url)

        if self.raw_html:
            html_data = self.raw_html
        else:
            req = urllib.request.Request(
                target_url,
                headers={"User-Agent": "ProblemIntelligenceOS/2.3 (+https://github.com/afzl-raza/problem-intelligence-os)"}
            )
            with urllib.request.urlopen(req, timeout=self.timeout_seconds) as response:
                html_data = response.read().decode("utf-8", errors="replace")

        return self.parse_html(html_data, target_url)

    def parse_html(self, html_data: str, target_url: str) -> list[CollectedItem]:
        parser = SimpleHTMLParser()
        parser.feed(html_data)

        title = parser.title.strip() if parser.title else "Untitled Page"
        content = "\n\n".join(parser.paragraphs) if parser.paragraphs else parser.meta_description or title

        return [
            CollectedItem(
                title=title,
                content=content,
                source_url=target_url,
                raw_metadata={"meta_description": parser.meta_description}
            )
        ]
