"""Bounded, local-only discovery of curated source *metadata*.

Retrieval is lexical relevance, not a verification that a generated statement
is supported by a paper or guideline. Imported metadata is untrusted text.
"""

import json
import re
import unicodedata
from pathlib import Path
from urllib.parse import urlsplit


SOURCES_PATH = Path(__file__).parent / "sources.json"
RESEARCH_PATH = Path(__file__).parent.parent / "research" / "sources.json"

_WORD = re.compile(r"[^\W\d_]+", re.UNICODE)
_STOP = frozenset({
    "about", "after", "again", "also", "and", "are", "because", "been",
    "before", "being", "but", "can", "could", "does", "for", "from",
    "had", "has", "have", "how", "into", "its", "just", "more", "not",
    "now", "our", "out", "should", "some", "than", "that", "the",
    "their", "them", "there", "these", "they", "this", "those", "was",
    "were", "what", "when", "where", "which", "who", "why", "will",
    "with", "would", "you", "your",
})
_SHORT_CLINICAL = frozenset({"ai", "act", "cbt", "dbt", "ocd", "ptsd", "emdr", "adhd"})
_PROVENANCE_TEXT = ("model_training_rights", "authors", "verification_method",
                    "publication_date_precision", "section_anchor", "source_license")
_PROVENANCE_FLAGS = ("source_content_included",)
# Recognizable role delimiters and direct attempts to override instructions
# are grounds to drop a source record, not to obey it. This is defense-in-depth,
# NOT a comprehensive LLM prompt-injection defense.
_PROMPT_ATTACK = re.compile(
    r"(?:^|\n)\s*(?:system|developer|assistant)\s*:|"
    r"<\|(?:im_start|system|assistant|developer)\|>|"
    r"\b(?:ignore|disregard|override)\b.{0,100}\b(?:previous|system|developer|safety|instruction|policy)\b",
    re.IGNORECASE,
)


def _terms(value):
    normalized = unicodedata.normalize("NFKC", str(value)).casefold()
    return {token for token in _WORD.findall(normalized)
            if token not in _STOP and (len(token) >= 3 or token in _SHORT_CLINICAL)}


def _usable(record):
    if not isinstance(record, dict):
        return False
    if any(not isinstance(record.get(key), str) or not record[key].strip()
           for key in ("id", "title", "summary", "url")):
        return False
    if len(record["title"]) > 500 or len(record["summary"]) > 2000:
        return False
    if any(ch.isspace() or ord(ch) < 32 for ch in record["url"]):
        return False
    if not isinstance(record.get("topics"), list) or any(not isinstance(t, str) for t in record["topics"]):
        return False
    try:
        url = urlsplit(record["url"])
    except ValueError:
        return False
    if url.scheme != "https" or not url.hostname or url.username or url.password:
        return False
    searchable_text = "\n".join((record["title"], record["summary"], *record["topics"]))
    if _PROMPT_ATTACK.search(searchable_text):
        return False
    # These fields may become visible to local retrieval or future adapters.
    # Never use source metadata as a grant of training or redistribution rights.
    for key in _PROVENANCE_TEXT:
        value = record.get(key)
        if value is None and key == "section_anchor":
            continue
        if key in record and (not isinstance(value, str) or len(value) > 1000 or
                              any(ord(ch) < 32 or ord(ch) == 127 for ch in value) or
                              _PROMPT_ATTACK.search(value)):
            return False
    if ("model_training_rights" in record and
            record["model_training_rights"] != "not-cleared"):
        return False
    if ("source_content_included" in record and
            record["source_content_included"] is not False):
        return False
    return True


def _load(path):
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, list):
        raise ValueError(f"Source register is not a list: {path.name}")
    return data


def sources():
    items = []
    by_id = {}
    by_url = {}
    registers = [_load(SOURCES_PATH)]
    if RESEARCH_PATH.is_file():
        # Only checked-in source metadata/original summaries, never private
        # documents or third-party article bodies, enter this retrieval path.
        registers.append(_load(RESEARCH_PATH))
    for register in registers:
        for item in register:
            if not _usable(item):
                continue
            sid = item["id"].casefold()
            canonical_url = item["url"].rstrip("/").casefold()
            existing = by_url.get(canonical_url)
            if existing is not None and (sid not in by_id or by_id[sid] is existing):
                # Keep the short curated title, original synopsis and stable ID,
                # but do not silently lose richer research provenance when the
                # same public source URL appears under a research alias.
                for key in (*_PROVENANCE_TEXT, *_PROVENANCE_FLAGS):
                    if key in item and existing.get(key) is None:
                        existing[key] = item[key]
            elif sid not in by_id and existing is None:
                items.append(item)
                by_id[sid] = item
                by_url[canonical_url] = item
    for item in items:
        # No rights assertion in a short curated entry is not permission.
        item.setdefault("model_training_rights", "not-cleared")
    return items


def search(query, limit=3):
    if not isinstance(query, str) or type(limit) is not int or limit <= 0:
        return []
    words = _terms(query[:1000])
    if not words:
        return []
    ranked = []
    for src in sources():
        title = _terms(src["title"])
        topic = _terms(" ".join(src["topics"]))
        summary = _terms(src["summary"])
        score = (4 * len(words & title)
                 + 5 * len(words & topic)
                 + len(words & summary))
        # Multi-term combinations relevant to the question rank ahead of
        # generic one-word matches. Never claim this is passage-level support.
        matched = words & (title | topic | summary)
        if len(matched) > 1:
            score += 2 * (len(matched) - 1)
        if score:
            ranked.append((-score, src["id"].casefold(), src))
    return [item for _, _, item in sorted(ranked)[:min(limit, 10)]]
