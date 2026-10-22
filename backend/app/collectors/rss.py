import urllib.request
import xml.etree.ElementTree as ET
from app.collectors.base import BaseCollector, CollectedItem
from app.utils.security import validate_safe_url


class RSSCollector(BaseCollector):
    """Collector for RSS and Atom XML feeds."""

    def __init__(self, timeout_seconds: int = 10, raw_content: str | None = None):
        self.timeout_seconds = timeout_seconds
        self.raw_content = raw_content

    def collect(self, target_url: str) -> list[CollectedItem]:
        validate_safe_url(target_url)

        if self.raw_content:
            xml_data = self.raw_content
        else:
            req = urllib.request.Request(
                target_url,
                headers={"User-Agent": "ProblemIntelligenceOS/2.3 (+https://github.com/afzl-raza/problem-intelligence-os)"}
            )
            with urllib.request.urlopen(req, timeout=self.timeout_seconds) as response:
                xml_data = response.read().decode("utf-8", errors="replace")

        return self.parse_xml(xml_data, target_url)

    def parse_xml(self, xml_data: str, fallback_url: str) -> list[CollectedItem]:
        items: list[CollectedItem] = []
        try:
            root = ET.fromstring(xml_data)
        except ET.ParseError as e:
            raise ValueError(f"Invalid XML payload: {e}")

        # Check for RSS 2.0 channel -> item
        channel = root.find("channel")
        if channel is not None:
            for item_elem in channel.findall("item"):
                title_elem = item_elem.find("title")
                desc_elem = item_elem.find("description")
                link_elem = item_elem.find("link")
                pubdate_elem = item_elem.find("pubDate")

                title = title_elem.text.strip() if title_elem is not None and title_elem.text else "Untitled Item"
                content = desc_elem.text.strip() if desc_elem is not None and desc_elem.text else title
                source_url = link_elem.text.strip() if link_elem is not None and link_elem.text else fallback_url
                pub_date = pubdate_elem.text.strip() if pubdate_elem is not None and pubdate_elem.text else None

                items.append(CollectedItem(
                    title=title,
                    content=content,
                    source_url=source_url,
                    published_at=pub_date,
                    raw_metadata={"feed_type": "rss2.0"}
                ))
            return items

        # Check for Atom entry
        namespaces = {'atom': 'http://www.w3.org/2005/Atom'}
        entries = root.findall('atom:entry', namespaces) or root.findall('entry')
        for entry in entries:
            title_elem = entry.find('atom:title', namespaces) or entry.find('title')
            content_elem = entry.find('atom:content', namespaces) or entry.find('content') or entry.find('atom:summary', namespaces) or entry.find('summary')
            link_elem = entry.find('atom:link', namespaces) or entry.find('link')
            pub_elem = entry.find('atom:published', namespaces) or entry.find('published') or entry.find('atom:updated', namespaces) or entry.find('updated')

            title = title_elem.text.strip() if title_elem is not None and title_elem.text else "Untitled Entry"
            content = content_elem.text.strip() if content_elem is not None and content_elem.text else title
            source_url = link_elem.attrib.get('href', fallback_url) if link_elem is not None else fallback_url
            pub_date = pub_elem.text.strip() if pub_elem is not None and pub_elem.text else None

            items.append(CollectedItem(
                title=title,
                content=content,
                source_url=source_url,
                published_at=pub_date,
                raw_metadata={"feed_type": "atom"}
            ))

        return items
