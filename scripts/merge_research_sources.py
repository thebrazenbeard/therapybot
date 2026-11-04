"""Validate and merge reviewed source-pointer batches, offline.

This is a metadata merge, not a scientific, clinical, licensing or URL audit.
By default, nothing is written; --apply updates the source register atomically.
"""

import argparse
import json
import os
import re
import tempfile
from pathlib import Path
from urllib.parse import urlsplit


ROOT = Path(__file__).resolve().parent.parent
CURRENT = ROOT / "research" / "sources.json"
REQUIRED = (
    "id", "title", "issuer", "date", "retrieved", "type", "url", "topics",
    "summary", "limitations", "rights", "authors", "verification_method",
)


def _url_key(value):
    parsed = urlsplit(value)
    if parsed.scheme != "https" or not parsed.hostname or parsed.username or parsed.password:
        raise ValueError("Source URL must use HTTPS without credentials")
    return value.rstrip("/").lower()


def _valid_record(source):
    if not isinstance(source, dict):
        raise ValueError("Source entry must be an object")
    for field in REQUIRED:
        if not source.get(field):
            raise ValueError(f"Source {source.get('id', '<unidentified>')}: missing {field}")
    if not re.fullmatch(r"[a-z0-9][a-z0-9-]+", source["id"]):
        raise ValueError(f"Invalid source ID: {source['id']!r}")
    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", str(source["retrieved"])):
        raise ValueError(f"Invalid retrieval date: {source['id']}")
    if not isinstance(source["topics"], list) or not all(
        isinstance(topic, str) and topic.strip() for topic in source["topics"]
    ):
        raise ValueError(f"Invalid topic list: {source['id']}")
    if source.get("source_content_included") is not False:
        raise ValueError(f"Copied third-party content not permitted: {source['id']}")
    if source.get("model_training_rights") != "not-cleared":
        raise ValueError(f"Uncleared model-training rights must stay explicit: {source['id']}")
    if len(source["summary"]) > 1000:
        raise ValueError(f"Source summary too long for a short original paraphrase: {source['id']}")
    return _url_key(source["url"])


def merge_sources(current, batches):
    """Reject ID/URL collisions; never silently replace existing metadata."""
    if not isinstance(current, list):
        raise ValueError("Current register must be a list")
    result = list(current)
    ids, urls = set(), set()
    for source in result:
        url = _valid_record(source)
        if source["id"] in ids or url in urls:
            raise ValueError(f"Existing register has a duplicate: {source['id']}")
        ids.add(source["id"])
        urls.add(url)
    additions = []
    for batch in batches:
        if not isinstance(batch, list):
            raise ValueError("Staged source batch must be a list")
        for source in batch:
            url = _valid_record(source)
            if source["id"] in ids or url in urls:
                raise ValueError(f"Source ID or URL already registered: {source['id']}")
            ids.add(source["id"])
            urls.add(url)
            additions.append(source)
    result.extend(additions)
    return result, len(additions)


def merge_files(current_path, batch_paths, *, apply=False):
    current = json.loads(Path(current_path).read_text(encoding="utf-8"))
    batches = [json.loads(Path(path).read_text(encoding="utf-8")) for path in batch_paths]
    result, count = merge_sources(current, batches)
    if apply:
        # Replace only the named source register; preserve old file on failure.
        parent = Path(current_path).parent
        fd, temporary = tempfile.mkstemp(prefix=".therapybot-sources-", suffix=".json", dir=parent)
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as handle:
                json.dump(result, handle, ensure_ascii=False, indent=2)
                handle.write("\n")
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(temporary, current_path)
        finally:
            if os.path.exists(temporary):
                os.unlink(temporary)
    return len(current), count, len(result)


def main():
    parser = argparse.ArgumentParser(description="Offline metadata-only source merge")
    parser.add_argument("batches", nargs="+", type=Path)
    parser.add_argument("--current", type=Path, default=CURRENT)
    parser.add_argument("--apply", action="store_true", help="write checked additions to the register")
    args = parser.parse_args()
    before, added, total = merge_files(args.current, args.batches, apply=args.apply)
    print(f"source register: {before} existing + {added} staged = {total}; "
          f"mode={'APPLIED' if args.apply else 'DRY-RUN'}; not a rights/scientific audit")


if __name__ == "__main__":
    main()
