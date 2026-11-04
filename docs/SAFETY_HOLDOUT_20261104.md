# TherapyBot independent safety-routing holdout — 2026-11-04

This is a read-only adversarial research checkpoint, **not** a clinical study or a passed safety gate. A separate independent reviewer composed 34 synthetic prompts that did not appear in the existing `tests/test_safety.py` fixture set and executed them against `therapybot.safety.classify` without modifying the classifier. No private conversations, medical records, or copied clinical prose were used. The exact cases, independently assigned expected routes, and actual program routes are in [`research/safety_holdout.jsonl`](../research/safety_holdout.jsonl).

## Reproduction and evidence level

- Repository source: `therapybot/safety.py`, unchanged across main commits `ab52ec4` and `4319fdf`; test conducted in the shared checkout on 2026-11-04.
- Executed `classify(message)` once for each synthetic case using a fresh Python process (no context passed). All prompts were authored for adversarial testing and have no connection to real users.
- Expected labels were the reviewer's qualitative judgments about *routing urgency*, **not clinician consensus or prospective suicide/violence risk predictions**. `normal` means no crisis-specific routing was expected for a standalone educational or historical question; it does not mean a person is safe.
- The observed labels are code-execution evidence; clinical effectiveness, complete coverage, model response quality, and future real-world behavior remain unverified.

## Actual results

| Expected route | Cases | Expected route returned | Mismatch |
| --- | ---: | ---: | ---: |
| Immediate | 13 | 1 | 12 |
| Concern | 9 | 1 | 8 |
| Normal educational, historical, or hypothetical | 12 | 9 | 3 |
| **Total** | **34** | **11** | **23** |

The highest-priority failures are **12 immediate-risk disclosures classified `normal`**. They include direct physical self-endangerment, acute injury, third-party medical emergencies, and imminent violence. Eight additional concerning disclosures returned `normal`, including possible severe mood instability, unwanted intrusive thoughts, unusual experiences accompanied by distress, medication uncertainty, and passive thoughts of death. Three ordinary historical or educational prompts triggered unwanted crisis routing, including one past overdose described as resolved years earlier.

The root-cause class is incomplete language generalization, not merely a missing isolated phrase. The main application invokes the local language model for a `normal` route; with the model offline it may return HTTP 503 rather than its static crisis message. A `concern` route prepends a generic caution to an otherwise unreviewed model completion, so no independent post-generation safety gate exists.

> **Hostile-review verdict:** A regression fix for all 23 known mismatches would establish only that these exact formulations pass. The system cannot be represented as reliably recognizing crises, delivering psychotherapy, or replacing medical assessment. This remains a release blocker for any claim of clinically safe unattended support.

## How to use this artifact

1. Keep these exact samples in an **evaluation-only quarantine**, never in the model's train/dev corpus. Because the set is now public, future qualification also needs genuinely unseen cases.
2. When the classifier changes, retain the `expected` field but re-execute it and record new observed results against the precise source SHA and environment; do not silently rewrite this historical result.
3. Review both false negatives and inappropriate escalation of historical, philosophical, fictional, and academic discussion. Preserve explicit non-diagnostic boundaries and access to emergency resources independently of model availability.
4. Add independent evaluation of full generated responses and human clinical oversight before any efficacy or safety claim. This corpus contains no intervention instructions or training authorization.

Public guidance baseline: [NIMH Understanding Psychosis](https://www.nimh.nih.gov/health/publications/understanding-psychosis) discusses varied possible causes and the need for appropriate assessment; [NICE NG225](https://www.nice.org.uk/guidance/ng225/chapter/recommendations) emphasizes individualized psychosocial assessment and advises against using risk scores as suicide prediction. Those documents are external context, **not validation of these labels**.

Blotter event `#3861` records the initial read-only finding. Clinical release remains blocked.
