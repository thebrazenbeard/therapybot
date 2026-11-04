# External psychology & sociology research corpus (experimental)

- `sources.json`: curated bibliographic source pointers and original short summaries. It includes clinical guidance, systematic reviews, longitudinal social research, public-health sources and AI privacy/safety frameworks. Check the actual article for applicability, update date, evidence certainty and precise section support.
- `behavior_examples.jsonl`: **30 original, synthetic** conversations with separate `train` (18), `dev` (6) and `eval` (6) splits. These were authored for TherapyBot prototyping and review; they are not real patient transcripts, not copied clinical publications, and not validated therapy treatment records.
- `../scripts/validate_research.py`: deterministic structural validation with source-ID references and split/rights checks; offline, no article scraping.

All external sources are explicitly labeled `model_training_rights: not-cleared`. No external source body is bundled for fine-tuning. The synthetic examples may be candidates for local experiments after independent clinical, rights and model reviews; **no model training or clinical outcome has been demonstrated** by committing this folder.

## Provenance and caveats

The original examples were synthesized against cited source topics on 2026-11-04. `source_ids` indicate relevant references, not a guarantee that every sentence is supported by a linked passage. `verification_method` records the present evidence ceiling; for many official pages, claim-to-section provenance is still pending. Source URLs can change. Observational correlations are not causal or individual predictions. The repository does not include personal records or actual therapy sessions.

Run `python scripts/validate_research.py` before any training/evaluation experiment. A passing result proves only structural invariants. Maintain the held-out `eval` split: do not train on it. Review each ideal response with appropriately qualified humans before safety-sensitive deployment.
