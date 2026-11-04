# Wave 3 independent safety-language hostile review

**Reviewed source:** main tree at commit `358a841efd830fecb71ea9fade0aeeef8e97c204` (local equivalent `2245dc921570cd0dedbbcbab80ec4b8a17ca87d8`). **Reviewer:** a separate AI specialist, same underlying provider family; not a human clinician. No person-specific records were accessed. These are **eight transparent development canaries**, not a hidden/sealed holdout. Evaluating them does not certify safety.

The reviewer independently invoked `therapybot.safety.classify()` on novel synthetic prompts. It reproduced missed first-person imminent self-harm, ambiguous preparation, fictional-to-personal transition, and possible violence cues; an explicit denial of suicidal intent was instead escalated. Ordinary philosophical/religious questions and clearly resolved history were correctly left alone on these examples.

See `research/safety_canaries_wave3.jsonl` and run `python -m scripts.evaluate_safety_canaries --strict` from the repository root. On the reviewed baseline this returned **3/8 matches, exit 1**; five mismatches document unresolved defects. Developers can omit `--strict` for a descriptive report without implying a passing gate. These counts are not clinical accuracy estimates.

The input router is an unvalidated phrase heuristic; a `normal` route must never be presented as a determination that someone is safe. Equally, a person's distress or philosophical language must not automatically trigger crisis questioning without evidence of current danger. A classifier label cannot substitute for professional risk assessment.

**Separate P0 output defect:** `therapybot/app.py` currently relays an arbitrary model completion after concern-prefix routing; six synthetic fake-model HTTP tests pass because unsafe completion text actually propagates. A topical bibliography is not an entailment check or validated citation. Independent output constraints, source-to-claim checks and real local GGUF replay are needed; generic regex filters alone cannot qualify clinical safety.

> **Release gate:** The owner withheld public interactive release. Do not merge or deploy a public support application based on these observations, the count of green unit tests, or an unsealed synthetic score. This is an engineering defect record and handoff to the runtime/safety team, not a clinical outcome claim.
