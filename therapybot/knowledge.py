"""Curated, link-only evidence metadata, safe for offline keyword retrieval."""

import json
import re
from pathlib import Path


SOURCES_PATH = Path(__file__).parent / "sources.json"
RESEARCH_PATH = Path(__file__).parent.parent / "research" / "sources.json"


def sources():
    items = json.loads(SOURCES_PATH.read_text(encoding="utf-8"))
    if RESEARCH_PATH.is_file():
        # Only checked-in source metadata/original summaries, never private
        # documents or third-party article bodies, enter this retrieval path.
        ids = {item["id"] for item in items}
        urls = {item["url"].rstrip("/").lower() for item in items}
        for item in json.loads(RESEARCH_PATH.read_text(encoding="utf-8")):
            canonical_url = item["url"].rstrip("/").lower()
            if item["id"] not in ids and canonical_url not in urls:
                items.append(item)
                ids.add(item["id"])
                urls.add(canonical_url)
    return items


def search(query, limit=3):
    words = set(re.findall(r"[a-z]{3,}", str(query).lower()))
    if not words:
        return []
    ranked = []
    for src in sources():
        def terms(value):
            return set(re.findall(r"[a-z]{3,}", value.lower()))

        score = (3 * len(words & terms(src["title"]))
                 + 2 * len(words & terms(" ".join(src["topics"])))
                 + len(words & terms(src["summary"])))
        if score:
            ranked.append((score, src))
    return [item for _, item in sorted(ranked, key=lambda pair: -pair[0])[:limit]]
