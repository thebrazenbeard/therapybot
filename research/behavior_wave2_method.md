# TherapyBot synthetic curriculum wave 2 — method and handoff

**Created:** 2026-11-04. **Scope:** original candidate dialogue examples for nonclinical, locally evaluated support/education. No model training performed. No patient text, private project files, or third-party article passages are inputs.

## Frozen research question

Can a small set of original synthetic prompts/ideal responses illustrate context-aware, evidence-referenced but non-diagnostic mental-health education, without importing the existing evaluation holdouts or asserting that an AI reliably provides therapy?

## Preregistered hypotheses and falsifiers

- C1: Sixteen new examples (12 `train`, 4 `dev`, **zero eval**) can be original, distinct from the existing 30, source-linked, and schema-valid. **Falsifier:** duplicate prompt/ID, unrecognized source ID, copied source passage, or mismatch with schema.
- C2: Each ideal response can answer the user rather than substituting an uninvited wellness script, respect autonomy, and distinguish reports from diagnoses. **Falsifier:** coercion, diagnosis, prescription, guaranteed outcome, or dependency language.
- C3: The tranche can cover psychology and sociology without reducing structural problems to thought distortions or equating religion with illness. **Falsifier:** any context-first example erases housing, employment, disability, discrimination, cultural or trauma constraints.
- C4: Source IDs can provide pointers without being misrepresented as passage-level verification or model-training licenses. **Falsifier:** claim of validated therapy, full-text permissions, or clinical efficacy inferred from a bibliographic record.

## Planned methods and stopping

- `CUR-1` CONFIRMATORY: inspect the `research/sources.json` IDs and existing `research/behavior_examples.jsonl` schema/prompts; keep `research/safety_holdout*.jsonl` sealed as evaluation only. No source bodies used.
- `CUR-2` EXPLORATORY: author exactly sixteen source-linked short dialogue pairs with bounded response length, avoiding source quotes and context-leaking examples.
- `CUR-3` CONFIRMATORY: run a script-only schema/uniqueness/source-ID check across old/new corpus, without copying or training on existing eval/holdout text.
- `CUR-4` CONFIRMATORY: independent reviewer reads the new tranche for trauma, safety, evidence and rights concerns **before** root integrates it. Author cannot self-approve.
- Stop after candidate artifact, local schema results and independent-review handoff. Model training, public release and clinical claims remain out of scope.

## Evidence log (append-only)

- `CUR-E1` REPO SOURCE: `research/sources.json` at local wave-2 integrated candidate state, 51 bibliographic records; `research/behavior_examples.jsonl` contains 30 entries, train/dev/eval `18/6/6`. Inspected with `rg` 2026-11-04. Existing eval examples remain untouched.
- `CUR-E2` BLOTTER: latest 20 `3893–3912` read through authorized Lappy `agent_blotter list --after-seq 3880 --limit 300` in UTF-8. TherapyBot wave 2 source and safety reports are present; this does not confer rights or efficacy.

## Outcome and deviations (append below after construction)

Independent outcome: **PENDING**. This file and new JSONL remain development candidates, not verified clinical training data.

- `CUR-E3` AUTHOR ARTIFACT: `research/behavior_examples_wave2.jsonl`, SHA-256 `0a6fcd20eadc96c57939030f9316efa2f6434abb67243ccc6283a1d69d73fdef`, 16 original candidate JSONL lines, IDs `tb-w2-001` through `tb-w2-016`, 12 `train` and 4 `dev` with no new `eval`. This establishes authorship and content existence, not clinical correctness.
- `CUR-E4` CONFIRMATORY STRUCTURAL CHECK: Python `-c` offline script parsed current 51-record source register, existing 30 examples, both existing/new safety holdouts, and the 16 staged records. Exit code `0`; decisive output: `PASS: 16 new original_synthetic candidate records, train=12 dev=4, source IDs resolved, IDs/prompts distinct from 30 prior and both safety holdouts`. Checked `source_ids` membership, unique ID/prompts, provenance flags, split counts and response length. This is structural validation, not licensed training authorization or scientific fact-checking.
- `CUR-E5` SOURCE ORIENTATION: source IDs include primary/official metadata pointers to NIMH, NICE, VA/DoD, CDC, WHO, HHS, SAMHSA, and referenced systematic reviews; published summaries in `research/sources.json` are bibliographic metadata with `model_training_rights: not-cleared`. The examples are wholly original short dialogues, not source passages.

### Deviations / methodological ceiling

The duplicate-avoidance inspection displayed the *existing* `research/behavior_examples.jsonl`, including its six eval prompts, before the new cases were drafted. **No eval prompts were incorporated or reused**, but the author was exposed to that evaluation material. Thus these cases should not be advertised as independent blind evaluation of the existing examples. The two safety holdout files were compared by an offline string-matching script only; no holdout cases were copied into this tranche. The staged file does not become training-ready until a **different reviewer** assesses safety, social context, quality, originality and rights.

### Post-audit integration correction (2026-11-04, appended)

The independent reviewer documented **PARTIALLY-CONFIRMED** metadata and content candidacy in `docs/WAVE2_CURRICULUM_AUDIT.md`; this is not clinical content approval or a third-party rights clearance. The parent implementer made two source-fit corrections after that review: `tb-w2-003` now cites only `hayes-act-model-2006` (a depression ACT meta-analysis does not directly evidence grief support); `tb-w2-014` now cites only `nice-bipolar-cg185-2025update` (the generic NIMH psychotherapies page is not diagnostic authority). The corrected staged JSONL SHA-256 is `1d896546a4a2c6b64ab79960d32df51784d3af820f48fc930e651644a6f1974f`.

Sixteen corrected candidates were integrated into `research/behavior_examples.jsonl`: 46 original synthetic examples total, train/dev/eval `30/10/6`; the six existing eval examples were not modified and neither safety holdout was modified. `python scripts/validate_research.py` returned 0 and structural PASS. **No weights were trained.**
