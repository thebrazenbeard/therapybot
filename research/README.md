# External psychology & sociology research corpus (experimental)

- `sources.json`: curated bibliographic source pointers and original short summaries. It includes clinical guidance, systematic reviews, longitudinal social research, public-health sources and AI privacy/safety frameworks. Check the actual article for applicability, update date, evidence certainty and precise section support.
- `clinical_sources_wave2.json` and `social_sources_wave2.json`: 19 added bibliographic records, also merged into `sources.json`. Their research-method notes and independent `docs/WAVE2_*_EVIDENCE_AUDIT.md` reports document the different evidence ceilings and narrow metadata corrections. These files **do not include source bodies or establish model-training rights**.
- `behavior_examples.jsonl`: **46 original, synthetic** conversations with separate `train` (30), `dev` (10) and `eval` (6) splits; the 16 wave-2 additions have a separate author method note and independent **partially confirmed** candidate review. These are research/development examples, not real patient transcripts, copied clinical publications, or validated therapy-treatment records. No model training has occurred.
- `behavior_examples_wave2.jsonl`: a separate, corrected provenance snapshot of the 16 candidate additions (already merged above). Do not append these records a second time.
- `safety_holdout.jsonl`: **34 independent synthetic evaluation-only** adversarial cases with recorded observed routes. **23/34 did not match the independent reviewer's expected route**. This historical failure record must never enter train/dev; see `docs/SAFETY_HOLDOUT_20261104.md`.
- `safety_holdout_wave2.jsonl`: 36 fresh synthetic evaluation-only cases, expected labels frozen by a separate AI reviewer before execution; **22/36 mismatched**. The method audit only partially confirmed the evidence due to unsealed freeze chronology and nonclinician labels. Keep out of train/dev and do not compare its score to the 34-case set as a trend.
- `../scripts/validate_research.py`: deterministic structural validation with source-ID references and split/rights checks; offline, no article scraping.
- `../scripts/merge_research_sources.py`: offline source-batch validation and collision detection, dry-run by default; its explicit `--apply` mode merges **new, unregistered** records. This is not an automatic license or accuracy validator.

All external sources are explicitly labeled `model_training_rights: not-cleared`. No external source body is bundled for fine-tuning. The synthetic examples may be candidates for local experiments after independent clinical, rights and model reviews; **no model training or clinical outcome has been demonstrated** by committing this folder.

## Provenance and caveats

The original examples were synthesized against cited source topics on 2026-11-04. `source_ids` indicate relevant references, not a guarantee that every sentence is supported by a linked passage. `verification_method` records the present evidence ceiling; for many official pages, claim-to-section provenance is still pending. Source URLs can change. Observational correlations are not causal or individual predictions. The repository does not include personal records or actual therapy sessions.

Run `python scripts/validate_research.py` before any training/evaluation experiment. A passing result proves only structural invariants. Maintain the held-out `eval` split: do not train on it. Review each ideal response with appropriately qualified humans before safety-sensitive deployment.
