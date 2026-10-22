import json
import urllib.request

from app.collectors.base import BaseCollector, CollectedItem
from app.utils.security import validate_safe_url


class APICollector(BaseCollector):
    """Collector for structured JSON feeds and REST API responses."""

    def __init__(self, timeout_seconds: int = 10, raw_json: str | None = None):
        self.timeout_seconds = timeout_seconds
        self.raw_json = raw_json

    def collect(self, target_url: str) -> list[CollectedItem]:
        validate_safe_url(target_url)

        if self.raw_json:
            json_str = self.raw_json
        else:
            req = urllib.request.Request(
                target_url,
                headers={
                    "User-Agent": "ProblemIntelligenceOS/2.3 (+https://github.com/afzl-raza/problem-intelligence-os)",
                    "Accept": "application/json",
                }
            )
            with urllib.request.urlopen(req, timeout=self.timeout_seconds) as response:
                json_str = response.read().decode("utf-8", errors="replace")

        return self.parse_json(json_str, target_url)

    def parse_json(self, json_str: str, target_url: str) -> list[CollectedItem]:
        try:
            data = json.loads(json_str)
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON payload: {e}")

        items: list[CollectedItem] = []

        if isinstance(data, list):
            item_list = data
        elif isinstance(data, dict):
            item_list = data.get("items") or data.get("data") or data.get("results") or [data]
        else:
            item_list = []

        for entry in item_list:
            if not isinstance(entry, dict):
                continue

            title = entry.get("title") or entry.get("name") or "API Item"
            content = entry.get("content") or entry.get("description") or entry.get("summary") or entry.get("text") or str(entry)
            source_url = entry.get("url") or entry.get("link") or target_url
            published_at = entry.get("published_at") or entry.get("created_at") or entry.get("date")

            items.append(
                CollectedItem(
                    title=str(title),
                    content=str(content),
                    source_url=str(source_url) if source_url else target_url,
                    published_at=str(published_at) if published_at else None,
                    raw_metadata={"raw_entry": entry}
                )
            )

        return items
