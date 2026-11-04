# Wave 3 original synthetic dialogue candidates — methodology

Status: **staged, not merged, not approved as training data or validated clinical advice**.

- Scope: 16 original fictional educational exchanges in `behavior_examples_wave3.jsonl`; 12 `train`, four `dev`, zero `eval`. The current release safety holdouts and six existing curriculum evaluation examples are unchanged.
- The prompts are fictional, not extracted from personal records, actual conversations, healthcare notes, or copyrighted training corpora. `source_text_copied` is `false` for every item. All wording was newly written for this staging batch.
- Source IDs point to the pre-existing `research/sources.json` register. These are background evidence/context pointers, **not** proof of each particular sentence, clinical efficacy, human review, or rights to use source full text for training.
- Focused failure modes: unhelpful psychologizing of financial/structural constraints; converting anger into presumed violence; inferring repressed trauma memories; conflating acceptance with endorsement; telling people to confront others without assessing risks; diagnosing spiritual discussion; loneliness measured only by contact count; false certainty about consciousness; overclaiming evidence provenance.
- Responses avoid an imposed diagnosis, faux therapeutic relationship, unverified legal guidance, empty reassurance and emergency escalation for ordinary questions. An ambiguous phrase such as “I can't do this anymore” is clarified while leaving room for genuine risk, rather than silently assuming either case.
- Separation: Wave 3's 16 records live in a staging file and should be evaluated for overlap against the already-sequestered evaluation-only holdouts before merging. Existing development/evaluation examples and `research/safety_holdout*.jsonl` must never be used as model-training text.
- Safety tag classifications label intended instructional context; they are not validated risk labels. Expert review and real local-model prompt/output testing are required before any training or release qualification.

## Structural verification (2026-11-04)

`jq -n --slurpfile` loaded staged records, 46 existing curriculum records, 51 registered sources and both evaluation-only holdout files. Exit `0`: exactly 16 candidate entries; 12 `train` and 4 `dev`; all IDs unique and absent from the existing corpus; all source IDs present in the register; all mandatory fields present; all `provenance=original_synthetic` and `source_text_copied=false`; no exact prompt overlap with existing curriculum or either safety holdout. This confirms only structural integrity and exact-string novelty, not semantic novelty, clinical suitability or absence of subtle leakage.

SHA-256 for the staged candidate file: `4830c6452174f54ee58e09542524202a3b379bebb8ac59364e5e535644fb7588`.

The author inspected existing six evaluation curriculum examples and the first four safety-holdout messages before drafting; further holdout comparison was machine-only. The proposed training and development candidates therefore **must not serve as independent blind evaluation of the current authoring process**. No holdout content was incorporated into a candidate response, and the evaluation files remain unchanged.

## Limitations and expected review

These examples are synthetic design hypotheses about useful responses. A source may describe a condition or intervention at population or clinical level without directly supporting a chatbot response. Clinical evidence researchers, a cultural-context reviewer, and an independent safety reviewer should challenge individual language and source relevance before any merger. No private data was ingested, no public license for external literature was inferred, and no model weights were trained.
