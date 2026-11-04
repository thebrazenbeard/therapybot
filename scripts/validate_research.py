"""Offline validation of source metadata and original synthetic examples.

Valid data is not proof of scientific accuracy, copyright clearance, or
clinical safety. This checks structural and privacy/provenance invariants.
"""

import json
import re
import sys
from collections import Counter
from pathlib import Path

if __package__:
    from .merge_research_sources import _valid_record
else:
    from merge_research_sources import _valid_record


ROOT = Path(__file__).resolve().parent.parent
SOURCES = ROOT / "research" / "sources.json"
EXAMPLES = ROOT / "research" / "behavior_examples.jsonl"
HOLDOUT = ROOT / "research" / "safety_holdout.jsonl"
HOLDOUT_WAVE2 = ROOT / "research" / "safety_holdout_wave2.jsonl"
# Public, developer-visible canaries exercise known failure patterns. They
# are not blinded or independent holdout evidence, but must stay out of seeds.
CANARIES_WAVE3 = ROOT / "research" / "safety_canaries_wave3.jsonl"


def _normalize_prompt(value):
    """Catch near-identical prompts separated only by punctuation/spacing.

    This is a deterministic exact-token canonicalization, *not* a semantic
    leakage detector; meaning-preserving paraphrases remain outside its reach.
    """
    return re.sub(r"[\W_]+", " ", str(value).casefold(), flags=re.UNICODE).strip()


def validate():
    problems = []
    sources = json.loads(SOURCES.read_text(encoding="utf-8"))
    if not isinstance(sources, list):
        sources = []
    if len(sources) < 12:
        problems.append("Need at least 12 researched source records")
    ids = set()
    urls = set()
    for index, source in enumerate(sources):
        label = f"source[{index}]"
        if not isinstance(source, dict):
            problems.append(f"{label}: entry must be an object")
            continue
        try:
            source_url = _valid_record(source)
        except ValueError as exc:
            problems.append(f"{label}: {exc}")
            source_url = None
        sid = source.get("id")
        if isinstance(sid, str) and sid in ids:
            problems.append(f"duplicate source id {sid}")
        if isinstance(sid, str):
            ids.add(sid)
        if source_url in urls:
            problems.append(f"{label}: duplicate source URL")
        if source_url is not None:
            urls.add(source_url)

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
        if not isinstance(item, dict):
            problems.append("example record must be an object")
            continue
        name = item.get("id", "<missing id>")
        if not isinstance(name, str) or not name.strip():
            problems.append("example record has missing or invalid id")
            continue
        if name in example_ids:
            problems.append(f"duplicate example id {name}")
        example_ids.add(name)
        split = item.get("split")
        counts[split if isinstance(split, str) else "<invalid>"] += 1
        if not isinstance(split, str) or split not in {"train", "dev", "eval"}:
            problems.append(f"{name}: invalid split {split}")
        if item.get("provenance") != "original_synthetic" or item.get("source_text_copied") is not False:
            problems.append(f"{name}: examples must be original and contain no copied source passage")
        for field in ("topic", "user", "ideal_response", "safety_tag"):
            if not isinstance(item.get(field), str) or len(item[field].strip()) < 5:
                problems.append(f"{name}: missing or too-short {field}")
        prompt = _normalize_prompt(item.get("user", ""))
        if prompt in prompts:
            problems.append(f"duplicate synthetic prompt for {name}")
        prompts.add(prompt)
        refs = item.get("source_ids", [])
        if not isinstance(refs, list) or not refs:
            problems.append(f"{name}: missing source_ids")
        elif any(not isinstance(ref, str) or ref not in ids for ref in refs):
            problems.append(f"{name}: unknown source ID")
        if isinstance(item.get("ideal_response"), str) and len(item["ideal_response"]) > 2500:
            problems.append(f"{name}: unexpectedly long training response")
    if len(examples) < 25 or counts["train"] < 15 or counts["dev"] < 4 or counts["eval"] < 5:
        problems.append("At least 25 examples and train/dev/eval coverage 15/4/5 required")

    # This independent adversarial holdout is explicitly quarantined from
    # training data. Preserve historical observed outcomes even after fixes.
    holdout_ids = set()
    holdout_prompts = set()
    for holdout_path in (HOLDOUT, HOLDOUT_WAVE2, CANARIES_WAVE3):
        if not holdout_path.exists():
            problems.append(f"missing evaluation-only holdout: {holdout_path.name}")
            continue
        for line_no, line in enumerate(holdout_path.read_text(encoding="utf-8").splitlines(), 1):
            if not line.strip():
                continue
            try:
                case = json.loads(line)
            except json.JSONDecodeError:
                problems.append(f"{holdout_path.name} line {line_no}: invalid JSON")
                continue
            if not isinstance(case, dict):
                problems.append(f"{holdout_path.name} line {line_no}: holdout must be an object")
                continue
            case_id = case.get("id")
            if not isinstance(case_id, str) or not case_id:
                problems.append(f"{holdout_path.name} line {line_no}: missing or invalid ID")
                continue
            if case_id in holdout_ids or case_id in example_ids:
                problems.append(f"{holdout_path.name} line {line_no}: missing or duplicate ID")
            holdout_ids.add(case_id)
            if case.get("provenance") != "original_synthetic" or case.get("use") != "evaluation_only":
                problems.append(f"{case_id}: holdout must remain original and evaluation-only")
            expected = case.get("expected")
            if not isinstance(expected, str) or expected not in {"immediate", "concern", "normal"}:
                problems.append(f"{case_id}: invalid expected safety route")
            observed = case.get("observed")
            if "observed" in case and (not isinstance(observed, str) or observed not in {"immediate", "concern", "normal"}):
                problems.append(f"{case_id}: invalid safety route")
            text_prompt = case.get("message")
            if not isinstance(text_prompt, str) or len(text_prompt.strip()) < 8:
                problems.append(f"{case_id}: missing synthetic message")
            else:
                normalized_prompt = _normalize_prompt(text_prompt)
                if normalized_prompt in prompts:
                    problems.append(f"{case_id}: evaluation prompt leaked into train/dev/eval seed")
                if normalized_prompt in holdout_prompts:
                    problems.append(f"{case_id}: duplicate held-out evaluation prompt")
                holdout_prompts.add(normalized_prompt)
    return problems, len(sources), len(examples), dict(counts)


if __name__ == "__main__":
    errors, source_count, example_count, splits = validate()
    print(f"Research metadata: {source_count} external records; {example_count} original synthetic examples; splits={splits}")
    if errors:
        for error in errors:
            print("ERROR:", error, file=sys.stderr)
        sys.exit(1)
    print("PASS structural/provenance checks; NOT a clinical, rights or scientific validation")
