# Independent sociology source audit — 2026-11-04

**Verdict: `partially-confirmed`.** The ten proposed `research/social_sources_wave2.json` records are credible **bibliographic pointers with original short summaries**, and the key subject, publisher, journal, DOI and study design claims are supported by the linked first-party WHO/CDC/HHS pages or original PubMed study records. I did **not** review full article methods/data, certify any item for model training, or establish that TherapyBot can safely apply these findings to individuals.

**Review subject:** `research/social_sources_wave2.json`, SHA-256 `2b016705fb51e9e7cdfd6d3c269ad67a275e353af05709f47a31d58dc00da474`. Independently reviewed the authoring note, source records, publisher/official abstracts, and local dry-run merge. Source research was retrospective to this reviewer (not a preregistered experiment); this is an independent **source-summary audit**, not independent clinical peer review.

## Traceable observations

| Record ID | Primary evidence inspected | Assessment |
| --- | --- | --- |
| `who-health-equity-report-2025` | [WHO report, dated 6 May 2025](https://www.who.int/publications/i/item/9789240107588) | Supported as **general health-equity** report; not a mental-health-specific treatment or causal study. |
| `who-social-connection-report-2025` | [WHO Commission, dated 30 June 2025](https://www.who.int/publications/i/item/978240112360) | Supported global policy synthesis; distinct from a proof of AI companionship efficacy. |
| `hhs-surgeon-general-connection-2023` | [HHS Surgeon General Social Connection advisory](https://www.hhs.gov/surgeongeneral/reports-and-publications/connection/index.html) | Correct 2023 advisory and broad population-level claims. |
| `cdc-mental-health-social-risk-2026` | [CDC About Mental Health, Aug. 20, 2026](https://www.cdc.gov/mental-health/about/) | Scope and listed drivers confirmed. **Minor metadata precision correction**: use date `2026-08-20`, `publication_date_precision: day`, and revise verification method's assertion that exact update day is unrecorded. |
| `cdc-intimate-partner-violence-2026` | [CDC IPV, Aug. 19, 2026](https://www.cdc.gov/intimate-partner-violence/about/index.html) | Definitions of physical/sexual abuse, stalking and psychological aggression supported. `coercive_control` is a topical paraphrase of exerting control, not a separate diagnosis or validated classification. |
| `holt-lunstad-isolation-mortality-meta-2015` | [Original PubMed abstract PMID 25910392](https://pubmed.ncbi.nlm.nih.gov/25910392/) | Correct authors/DOI/meta-analysis of **observational mortality**, not mental-health treatment or chatbot outcomes. |
| `jespersen-ses-depression-meta-2025` | [Original PubMed abstract PMID 40643383](https://pubmed.ncbi.nlm.nih.gov/40643383/) | Correct systematic review/meta-analysis, association across SES measures, and caveats. |
| `maletta-discrimination-mental-health-cohort-2025` | [Original PubMed abstract PMID 39306008](https://pubmed.ncbi.nlm.nih.gov/39306008/) | Correct UK longitudinal self-report study and 2024 online/2025 issue chronology. Generalization beyond cohort is uncertain. |
| `rubin-mcgregor-disability-discrimination-2026` | [Original PubMed abstract PMID 41411028](https://pubmed.ncbi.nlm.nih.gov/41411028/) | Correct authors/DOI and 5,115-person U.S. historical national survey analysis. **Clarify** that 2026 is publication date, not collection of fresh 2026 disability survey data; only adults with physical disabilities were included. |
| `bora-help-seeking-review-2026` | [Original PubMed abstract PMID 42064325](https://pubmed.ncbi.nlm.nih.gov/42064325/) | Correct RCT-only systematic review and distinction among attitudes, intentions and behavior; review synthesis is heterogeneous. |

## Reproducible structural probe

`python scripts/merge_research_sources.py research/social_sources_wave2.json` (read-only/default dry run), exit code **0**:

`source register: 32 existing + 10 staged = 42; mode=DRY-RUN; not a rights/scientific audit`

This supports **structural acceptance only**. The staging batch's own source text and the external research summaries are not model-training rights; all ten source records correctly preserve `model_training_rights: not-cleared` and `source_content_included: false`.

## Hostile objections and recommended dispositions

> **Structural suffering is not a thinking error.** Group studies do not authorize TherapyBot to diagnose a person, tell them they are misperceiving abuse or discrimination, or imply that breathing exercises solve housing insecurity. Context must come from the user's report, not demographic guessing.

> **Social connection is not compulsory contact.** WHO/CDC/HHS population findings do not imply that chosen solitude is pathological, that family is safe, or that automated companionship substitutes for consensual real-world support.

> **Publication date is not data freshness.** The 2026 disability study uses the second wave of a historical national survey. Display an explicit source vintage distinction if summarizing it to users.

> **No training clearance or clinical efficacy.** Links and original paraphrases can support reference discovery; they do not license retrieval of whole papers or supervised fine-tuning, or establish model-output clinical safety.

**Recommendation:** Accept the ten metadata links after the two narrow date/vintage clarifications (CDC record and disability-study note); preserve the other caveats. This is a partial independent confirmation of link/abstract-level metadata, **not** a full-text methods review. Public interactive TherapyBot release remains held.
