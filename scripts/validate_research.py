"""Offline validation of source metadata and original synthetic examples.

Valid data is not proof of scientific accuracy, copyright clearance, or
clinical safety. This checks structural and privacy/provenance invariants.
"""

import json
import re
import sys
from collections import Counter
from pathlib import Path
from urllib.parse import urlsplit


ROOT = Path(__file__).resolve().parent.parent
SOURCES = ROOT / "research" / "sources.json"
EXAMPLES = ROOT / "research" / "behavior_examples.jsonl"


def validate():
    problems = []
    sources = json.loads(SOURCES.read_text(encoding="utf-8"))
    if not isinstance(sources, list) or len(sources) < 12:
        problems.append("Need at least 12 researched source records")
    ids = set()
    for index, source in enumerate(sources):
        label = f"source[{index}]"
        for field in ("id", "title", "issuer", "date", "retrieved", "type", "url", "topics", "summary", "limitations", "rights", "model_training_rights", "authors", "source_license", "verification_method"):
            if not source.get(field) and field != "source_license":
                problems.append(f"{label}: missing {field}")
        sid = source.get("id")
        if sid in ids:
            problems.append(f"duplicate source id {sid}")
        ids.add(sid)
        url = urlsplit(source.get("url", ""))
        if url.scheme != "https" or not url.hostname:
            problems.append(f"{label}: source URL must be HTTPS")
        if source.get("source_content_included") is not False:
            problems.append(f"{label}: copied source bodies are not allowed")
        if source.get("model_training_rights") != "not-cleared":
            problems.append(f"{label}: do not assume third-party training rights")
        if not isinstance(source.get("topics"), list) or not source["topics"]:
            problems.append(f"{label}: topics must be nonempty list")
        if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", str(source.get("retrieved", ""))):
            problems.append(f"{label}: retrieval date must be YYYY-MM-DD")

    examples = []
    for line_no, line in enumerate(EXAMPLES.read_text(encoding="utf-8").splitlines(), 1):
        if line.strip():
            try:
                examples.append(json.loads(line))
            except json.JSONDecodeError as exc:
                problems.append(f"example line {line_no}: invalid JSON: {exc.msg}")
    counts = Counter()
    example_ids = set()
    prompts = set()
    for item in examples:
        name = item.get("id", "<missing id>")
        if name in example_ids:
            problems.append(f"duplicate example id {name}")
        example_ids.add(name)
        split = item.get("split")
        counts[split] += 1
        if split not in {"train", "dev", "eval"}:
            problems.append(f"{name}: invalid split {split}")
        if item.get("provenance") != "original_synthetic" or item.get("source_text_copied") is not False:
            problems.append(f"{name}: examples must be original and contain no copied source passage")
        for field in ("topic", "user", "ideal_response", "safety_tag"):
            if not isinstance(item.get(field), str) or len(item[field].strip()) < 5:
                problems.append(f"{name}: missing or too-short {field}")
        prompt = str(item.get("user", "")).casefold().strip()
        if prompt in prompts:
            problems.append(f"duplicate synthetic prompt for {name}")
        prompts.add(prompt)
        refs = item.get("source_ids", [])
        if not isinstance(refs, list) or not refs:
            problems.append(f"{name}: missing source_ids")
        elif any(ref not in ids for ref in refs):
            problems.append(f"{name}: unknown source ID")
        if len(item.get("ideal_response", "")) > 2500:
            problems.append(f"{name}: unexpectedly long training response")
    if len(examples) < 25 or counts["train"] < 15 or counts["dev"] < 4 or counts["eval"] < 5:
        problems.append("At least 25 examples and train/dev/eval coverage 15/4/5 required")
    return problems, len(sources), len(examples), dict(counts)


if __name__ == "__main__":
    errors, source_count, example_count, splits = validate()
    print(f"Research metadata: {source_count} external records; {example_count} original synthetic examples; splits={splits}")
    if errors:
        for error in errors:
            print("ERROR:", error, file=sys.stderr)
        sys.exit(1)
    print("PASS structural/provenance checks; NOT a clinical, rights or scientific validation")
