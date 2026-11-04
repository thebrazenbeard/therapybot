# Clinical source wave 3 — provenance and limits

**Date:** 2026-11-04. **Operator:** native clinical research subagent `/root/wave3_clinical`. **Status:** candidate metadata for independent review; no production ingest until root approves.

This wave located ten distinct external reference pointers not present in the 51-entry source inventory observed at start. The staged JSON includes only URLs, bibliographic metadata, and independently authored short descriptions; no full guideline, book, review, transcript, prompt or patient record was copied. Every record has `model_training_rights: not-cleared` and `source_content_included: false`.

## Frozen question and methods

Preregistered before the later searches in the external scratch record `therapybot_wave3_clinical_research_log.md`. Methods C1: baseline registry inventory; C2: official publisher/DOI searches capped at ten; C3: metadata staging and JSON, schema and duplicate checks. Predictions were about discoverability and audience scope—not TherapyBot efficacy.

## Traceable evidence

| Candidate source ID | Official publisher evidence | Evidence type and limitation |
|---|---|---|
| `who-doing-what-matters-stress-2020` | [WHO 9789240003927](https://www.who.int/publications/i/item/9789240003927), 29 April 2020; inspected page title/date/overview | Illustrated self-help guide; WHO programme evidence cannot transfer to a bot |
| `who-self-help-delivery-manual-2026` | [WHO 9789240120785](https://www.who.int/publications/i/item/9789240120785), 1 June 2026; inspected publisher overview | Implementation manual for providers and programme managers; not automated clinical qualification |
| `nice-child-adolescent-depression-ng134` | [NICE NG134](https://www.nice.org.uk/guidance/ng134), original 25 June 2019; official search-indexed recommendations | Youth clinical guideline; direct chapter retrieval returned HTTP 403, so section-level confirmation pending |
| `cochrane-psychosocial-adult-self-harm-2021` | [Cochrane CD013668](https://www.cochrane.org/evidence/CD013668_psychosocial-interventions-adults-who-self-harm), 22 April 2021; publisher DOI/authors | Systematic review of trials; no justification for autonomous suicide-risk prediction |
| `who-unicef-foundational-helping-2025` | [WHO 9789240105935](https://www.who.int/publications/i/item/9789240105935), 10 July 2025; official audience/scope | Human-helper training and supervision, not evidence that model responses are safe |
| `who-unicef-equip-competencies-2026` | [WHO 9789240121041](https://www.who.int/publications/i/item/9789240121041), 20 May 2026; official date/overview | Workforce competency-assessment compendium, not AI chatbot clinical validation |
| `cochrane-cbt-older-anxiety-2024` | [Cochrane CD007674](https://www.cochrane.org/evidence/CD007674_cognitive-behavioural-therapy-and-third-wave-approaches-anxiety-and-related-disorders-older-people), 8 July 2024; publisher abstract and authors | Systematic review; 21 trials / 1,234 participants; long-term effects uncertain, low certainty in several comparisons |
| `who-psychological-first-aid-2011` | [WHO 9789241548205](https://www.who.int/publications/i/item/9789241548205), 2 October 2011; publisher overview and [official PDF rights page](https://iris.who.int/bitstream/handle/10665/44615/9789241548205_eng.pdf?sequence=1) | Humane crisis-response field guide; 2011 PDF states all rights reserved; not emergency-service substitution |
| `who-community-mental-health-rights-2021` | [WHO 9789240025707](https://www.who.int/publications/i/item/9789240025707/), 9 June 2021; official normative guidance overview | Rights-based service system guidance; not intervention RCT and not legal advice |
| `nice-eating-disorders-ng69` | [NICE NG69](https://www.nice.org.uk/guidance/ng69), original 23 May 2017; last updated 16 Dec 2020; official indexed page | Clinical guideline; direct chapter retrieval HTTP 403; physical-risk decisions and professional treatment remain outside a chatbot |

**Citation-level verification only:** Official publisher descriptions were examined, not original controlled-trial datasets, all guideline sections or exhaustive included studies. Where NICE's chapter was blocked, exact recommendations remain *unverified*, despite search-indexed text providing title, publication date, and scope. Publication pages can change; each record carries retrieval date.

## Cautions for downstream use

1. Many sources concern *human professionals* and supervised programmes. It would be a serious inference error to label them proof that TherapyBot delivers CBT/ACT/DBT, assesses risk, or practices psychotherapy.
2. WHO peer-support/rights principles and self-help techniques have distinct functions; neither should be merged into diagnoses or forced wellness interventions for ordinary philosophy/religion conversations.
3. Children, young people, adults, and older adults are not interchangeable study populations. Preserve age, country, follow-up, outcome and trial-quality limitations.
4. External documents remain **not cleared for model training** even where the publisher hosts a freely accessible PDF or notes a limited Creative Commons license. This staging contains no third-party full text.
5. `source_license` is `unverified` except a clearly printed 2011 WHO rights notice; do not extrapolate licenses between documents.

## Planned integration checks

After independent clinical/provenance review: merge with repository's reviewed source-merger in dry-run mode, check duplicate ID, URL, SHA, and metadata structure, then apply explicit merge. Revalidate the entire research register and keep a frozen old/new count. This research pass does not itself merge, train, release, or certify.

## Verdict

**Researcher observation:** Ten official publisher source pointers exist and are new relative to the baseline 51 URLs. **Independent review:** pending. **Clinical safety, efficacy, license clearance and model-training readiness:** not established.
