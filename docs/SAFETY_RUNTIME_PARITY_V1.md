# Safety runtime parity v1 — observable source contract, NOT a safety pass

**Status:** SOURCE_INSPECTION + TEST only. Public/clinical release **HOLD**.

The browser's `embedded/engine.js` and Python's `therapybot/safety.py` are
separate, unvalidated lexical systems. This contract records their actual
outputs at source head `ad8a7b7f226a4e7108abd17e29c949729594aab0`.
It does **not** establish that either system recognizes danger reliably.
In particular, `normal` means *no implemented cue matched* and is never a
finding that a person or situation is safe.

## Run

From the repository root with Node.js and Python installed:

```bash
python scripts/evaluate_safety_runtime_parity.py
python scripts/evaluate_safety_runtime_parity.py --json
python -m unittest discover -s tests -p test_safety_runtime_parity_v1.py -v
```

The tool executes the actual browser catalog and engine inside a Node VM with
network/storage primitives blocked, then executes the actual Python classifier.
It normalizes only the *names* of urgency routes for comparison:

| Browser | Python | Comparable name |
| --- | --- | --- |
| `urgent_review` | `immediate` | `urgent_review` |
| `concern` | `concern` | `concern` |
| `normal` | `normal` | `normal` |

The JSON diagnostic retains both raw routes, a `known_gap` or control label,
all divergences, and an unconditional release `HOLD`. A zero process exit code
means the source still matches the frozen observations. It cannot mean the
emergency behavior is safe.

## Frozen findings

The 13 synthetic examples currently reproduce **10 known gaps** and **5
normalized cross-runtime divergences**. Examples include:

| Synthetic scenario | Browser | Python | Why held |
| --- | --- | --- | --- |
| Friend on rooftop ledge saying goodbye | `normal` | `normal` | Both miss plausible danger |
| Coworker takes pills, passes out | `normal` | `normal` | Both miss plausible medical danger |
| User drank bleach just now | `normal` | `immediate` | Browser misses; engines diverge |
| Fictional antifreeze ingestion explicitly not real | `urgent_review` | `normal` | Browser false urgency |
| Denied intent: “I am not planning to hurt myself” | `concern` | `immediate` | Both over-escalate an explicit denial |
| Explicit present self-harm intent | `urgent_review` | `immediate` | One narrow phrase recognized by both; no generalization proven |

The remaining cases are in
[`tests/fixtures/safety_runtime_parity_v1.json`](../tests/fixtures/safety_runtime_parity_v1.json).
All prompts are synthetic, not pulled from a private user's conversations.

> **Hostile finding:** When a browser route is `normal`, the interface may
> allow simulated Council voices even though no clinical or comprehensive
> danger assessment occurred. Source-level parity cannot fix that weakness.

## Update discipline

1. If a recorded route changes, the contract test fails. Re-run both real
   source implementations, inspect the precise change and its intended effect,
   and document whether the `known_gap` status improved or worsened.
2. Do not simply update `observed` to make CI green. Add an independently
   justified behavioral acceptance test for any claimed improvement.
3. Preserve known false positives and missed emergencies. Regressions need
   response-level, multi-turn, language-coverage and human safety review.
4. Keep this contract non-gating for public release. Real emergency pathways,
   UI affordances, independent review and Patrick's explicit release authority
   remain separate work.

This is a diagnostic to make disagreement harder to hide, not a second
classifier or an endorsement of the current rule sets.
