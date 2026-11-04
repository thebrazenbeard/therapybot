# Wave 3 independent clinical/trauma source-pointer audit

**Date:** 2026-11-04. **Reviewer:** distinct native research-review subagent (same provider/model family, **not** a clinician). **Scope:** `research/clinical_sources_wave3.json` and `research/trauma_sources_wave3.json`, their method notes, and the existing 51-source registry. No review of personal records, model outputs or therapeutic efficacy.

## Preregistered question and methods (frozen before source checks)

**Question:** Are the 20 staged bibliographic pointer records structurally appropriate, unique, conservatively rights-labeled, and materially consistent with at least five authoritative publisher/DOI records? **Hypothesis:** each source can be merged as a bibliographic pointer only; **falsifiers:** duplicate IDs/URLs, claimed training permission, copied third-party passage, misidentified edition/publisher/year, materially distorted evidence type or clinical summary, omitted reproduction constraints. **Stopping rule:** inspect all 20 metadata records for schema/collisions/rights and verify a minimum of five high-stakes examples against publisher or DOI sources; log access failures separately.

- `A1`, confirmatory: parse the 20 staged JSON records, check required fields, rights flags, duplicate IDs/URLs (within and vs. existing 51), and high-level consistency.
- `A2`, confirmatory: inspect at least five original publisher/DOI pages for exact title/edition/year/reproduction restrictions, recording page evidence or retrieval failures.
- `A3`, confirmatory: evaluate whether summary and limitations remain narrow enough to be indexed as pointer-only metadata without implying delivered psychotherapy or training rights.
- `A4`, confirmatory: inspect method logs for limitations, unverified sections, license ambiguity, and clear separations of kinds of evidence.

**Evidence standard:** `SOURCE_INSPECTION` or DOI metadata is not full-text analysis; inaccessible pages are recorded `INCONCLUSIVE`, not implied verified. Any merge disposition remains independent of legal, clinical or human review.

## Evidence log

### A1 — structural and scope checks — CONFIRMATORY, PASS (metadata only)

- Input fingerprints (SHA-256): clinical JSON `75200a280f11748cd71ba7309e437e3e9d101807391c71adb2f58c3ac048a099`; trauma JSON `28ec7d792c5732daa50d5ba9c0b36d3901ee209a0b10589a5837ce993d3a7990`.
- `jq -s` checking 20 staged records against existing `research/sources.json` returned: 20 IDs and 20 URLs unique within batches; zero ID or URL collisions against the pre-wave 51; zero missing required fields; zero `model_training_rights` other than `not-cleared` or `source_content_included` other than `false`. Exit `0`.
- `python scripts/merge_research_sources.py research/clinical_sources_wave3.json research/trauma_sources_wave3.json` exited `0`: `source register: 51 existing + 20 staged = 71; mode=DRY-RUN; not a rights/scientific audit`.
- This script is a structural validator. It does **not** establish that all 20 URLs remain live or clinically accurate.

### A2 — primary-source cross-checks — CONFIRMATORY, qualified

Independent reviewer retrieved the following official publisher pages on 2026-11-04; descriptions paraphrased rather than copied:

| Staged ID | Direct publisher evidence | Disposition |
| --- | --- | --- |
| `who-doing-what-matters-stress-2020` | [WHO publication](https://www.who.int/publications/i/item/9789240003927): title, subtitle, 29 April 2020, self-help/adversity scope | Match; no bot efficacy inference |
| `who-self-help-delivery-manual-2026` | [WHO publication](https://www.who.int/publications/i/item/9789240120785): exact 1 June 2026 title and focus on programme managers and providers | Match; not a generic chatbot protocol |
| `who-unicef-foundational-helping-2025` | [WHO/UNICEF publication](https://www.who.int/publications/i/item/9789240105935): 10 July 2025, trainers/supervisors and skills assessment | Match; human competency instrument, not chatbot validation |
| `who-psychological-first-aid-2011` | [WHO publication](https://www.who.int/publications/i/item/9789241548205): 2 October 2011; context for human field workers | Match; no emergency-service substitution |
| `who-community-mental-health-rights-2021` | [WHO publication](https://www.who.int/publications/i/item/9789240025707/): 9 June 2021, rights-oriented systems guidance | Match; normative guidance, not efficacy trial |
| `who-stress-specific-guideline-2013` | [WHO guideline](https://www.who.int/publications/i/item/guidelines-for-the-management-of-conditions-that-are-specifically-related-to-stress): 1 January 2013 | Match; old guidance caveat important |
| `apa-ptsd-clinical-guideline-2025` | [American Psychological Association](https://www.apa.org/ptsd-guideline/): current 2025 adult-PTSD revision and clinician-directed framing | Match, but staged `2025-04` month precision not confirmed from landing-page excerpt alone |
| `apa-dsm-cultural-formulation-interview-2013` | [American Psychiatric Association PDF](https://www.psychiatry.org/getmedia/5cc5329d-3bd4-4c6a-bae1-dfd0d6496f44/APA-DSM5TR-CulturalFormulationInterview.pdf): 2013 copyright, restricted permission terms, not sole diagnostic basis | Match; reproduction/modification restrictions are material |
| `istss-ptsd-prevention-guidelines-2018` | [ISTSS publisher page](https://istss.org/clinical-resources/trauma-treatment/istss-prevention-and-treatment-guidelines/): clinical audience, partly members-only evidence, newer edition forthcoming | **Improve metadata:** page also records a 19 March 2019 amendment to one early-treatment recommendation and explicit society permission for electronic copying/reuse. Staged 2018 edition year was not independently visible in the retrieved page excerpt. |
| `isstd-did-treatment-guidelines-2011` | [ISSTD publisher page](https://www.isst-d.org/publications-resources/resources-for-professionals/adult-treatment-guidelines/): 2011 third revision and expert-consensus scope | Match; expert consensus is not individual assessment nor randomized effectiveness evidence |
| `mattsson-trauma-memory-accuracy-review-2021` | [NIH/PubMed bibliographic/abstract record](https://pubmed.ncbi.nlm.nih.gov/33620914/): 2021 journal citation, DOI, eleven-study review | Match at abstract level; not validity adjudication for personal trauma narratives |
| `adeponle-cultural-psychosis-reassessment-2012` | [NIH/PubMed bibliographic/abstract record](https://pubmed.ncbi.nlm.nih.gov/22302332/): 2012, 323 Canadian service records, nonrandom cultural consultation | Match at abstract level; it does not verify any particular experience or indicate supernatural mechanisms |
| `sarr-icd11-complex-ptsd-assessment-review-2024` | [Wiley publisher record](https://onlinelibrary.wiley.com/doi/10.1002/cpp.3012): 18 June 2024, 36 studies, no gold-standard assessment | Match at publisher-summary level; not a chatbot diagnostic protocol |

**Access failures / verification ceilings:** Direct DOI resolvers for four Wiley/LWW/Psychiatric Services articles failed or returned 403 in this reviewer channel; publisher search or PubMed metadata was substituted and explicitly marked as such. NICE NG134/NG69 direct chapter retrieval was reported as 403 in the staged method: I did not independently read every clinical recommendation. I did not open every article full text, inspect the underlying randomized trials, or verify every author's affiliation.

### A3 — scientific and licensing boundary — CONFIRMATORY, PARTIALLY CONFIRMED

The twenty short summaries correctly identify the general topic and mostly distinguish guideline, human training manual, consensus, systematic review, observational work and controlled intervention evidence. Their explicit limitations prohibit diagnosis or treatment inference by an autonomous chatbot. All 20 state that model-training rights are uncleared and article bodies are excluded.

**Required narrow correction before merging:** `istss-ptsd-prevention-guidelines-2018` should record the 2019 correction notice and the explicit ISTSS restriction on electronic storage/reuse, with its `source_license` upgraded from `unverified` to a descriptive restricted-society-rights tag (not a grant). The existence of the 2018 edition is plausible but not independently dated by the fetched current landing page; if the original edition PDF cannot be verified, keep the date precision as year-only and label edition-year verification limited.

**Optional clarity correction:** `apa-ptsd-clinical-guideline-2025` should label exact April revision month as coming from a specific publisher document; the landing page independently supports 2025, not necessarily that month. Its `verification_method` already specifies April, but precision should not outrun the recorded evidence.

**Not authorized:** training on the APA cultural-interview questions or republishing its instrument without permission; importing member-only ISTSS evidence summaries; assuming all WHO PDFs have the same license; copying Cochrane or publisher full-text articles; training on NIMH/PubMed abstracts without separate rights review.

### A4 — method logs — CONFIRMATORY, PASS with disclosure

The clinical method note distinguishes publisher/abstract-level confirmation from inaccessible NICE recommendation chapters, flags 2011 WHO rights and human implementation assumptions. The trauma method note expressly states that source exploration preceded its write-up, so its study selection is retrospective/exploratory; it does not falsely claim a prospective systematic protocol. This independent audit's frozen methods were recorded before my checks.

## Overall independent verdict

**PARTIALLY CONFIRMED — eligible as bibliographic pointers after the ISTSS metadata correction; not approved as model-training content, evidence-backed conversational outputs, or clinical guidance.** Structural novelty and cautious framing are supported; limited publisher access, unstated human review, section-level source entailment, license ambiguity and the 2019 ISTSS amendment remain material qualifications. The parent integrator must perform the correction and a fresh dry-run before merging. No patient records, source bodies or private artifacts were accessed.

> **Hostile finding:** Source-count growth measures bibliography breadth, not safety. A link to a clinician guideline can be technically correct and still be completely inapplicable to an automated conversation, especially in self-harm or diagnostic contexts.

## Post-correction limited re-review (same day; not part of initial frozen sample)

The parent integrator changed **only the staged** `istss-ptsd-prevention-guidelines-2018` metadata after receiving the independent finding. I inspected that exact updated record against the [ISTSS official page](https://istss.org/clinical-resources/trauma-treatment/istss-prevention-and-treatment-guidelines/):

- `limitations` now explicitly notes the **19 March 2019 amendment** to an early-treatment recommendation, the incomplete original-2018 dating evidence, member-only evidence summaries, and forthcoming newer guidelines.
- `source_license` is now `istss-permission-required-for-electronic-reuse`; `rights` and `model_training_rights: not-cleared` remain appropriately restrictive.
- `verification_method` now accurately distinguishes publisher-page confirmation of permissions and amendment from the unconfirmed 2018 edition date.
- New trauma-batch SHA-256: `c16d8d7f59887cb171f29bf89f39112a397276ca07862c0e80da2386c8ebf662` (initial hash above remains historical, not current).
- `python scripts/merge_research_sources.py research/clinical_sources_wave3.json research/trauma_sources_wave3.json` exited `0` with `51 existing + 20 staged = 71; mode=DRY-RUN` after correction.

**Revised narrow disposition:** **PARTIALLY CONFIRMED, the identified ISTSS metadata defect remedied for pointer-only staging.** The 20 source pointers now have no known uncorrected high-impact *metadata* finding from this audit; incomplete sections/full-text checks, uncertain licensing for other records, absence of human clinical review, and lack of source-to-output entailment remain unchanged. This is **not** a comprehensive re-review of every source after the edit.
