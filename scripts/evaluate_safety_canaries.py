"""Characterize the lexical safety router against transparent, non-blind synthetic cases.

This is a development probe, NOT a sealed holdout, clinical risk assessment or
validation of generated model responses. It does not modify the corpus.
"""

import argparse
import json
from pathlib import Path

from therapybot.safety import classify


CASES = Path(__file__).resolve().parent.parent / "research" / "safety_canaries_wave3.jsonl"


def evaluate(path=CASES):
    cases = [json.loads(line) for line in Path(path).read_text(encoding="utf-8").splitlines() if line.strip()]
    results = []
    for case in cases:
        if case.get("use") != "evaluation_only" or case.get("provenance") != "original_synthetic":
            raise ValueError(f"Invalid canary provenance: {case.get('id')!r}")
        expected = case.get("expected")
        if expected not in ("normal", "concern", "immediate"):
            raise ValueError(f"Invalid canary expectation: {case.get('id')!r}")
        actual = classify(case["message"])
        results.append((case["id"], expected, actual))
    return results


def main():
    parser = argparse.ArgumentParser(description="Report observed vs developer-assigned synthetic safety routes")
    parser.add_argument("--strict", action="store_true", help="exit nonzero on any mismatches")
    parser.add_argument("--cases", type=Path, default=CASES)
    args = parser.parse_args()
    results = evaluate(args.cases)
    for case_id, expected, actual in results:
        verdict = "MATCH" if expected == actual else "MISMATCH"
        print(f"{case_id}: expected={expected} observed={actual} {verdict}")
    matches = sum(expected == actual for _, expected, actual in results)
    print(f"Developer-authored synthetic canaries: {matches}/{len(results)} routes matched; not clinical accuracy")
    if args.strict and matches != len(results):
        raise SystemExit(1)


if __name__ == "__main__":
    main()
