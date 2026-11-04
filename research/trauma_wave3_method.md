# Wave 3 trauma, dissociation and unusual-experiences reference batch

Date: 2026-11-04. Owner: Team01 trauma researcher. Status: **staged metadata, awaiting independent audit**; not incorporated into the production source register.

## Question and boundary

Which directly traceable clinical or primary-study references help TherapyBot explain trauma, memory uncertainty, dissociation and culturally/spiritually contextualized experiences without assigning diagnoses, asserting extraordinary causes, or discrediting personal disclosures?

This is a *bibliographic/evidence-metadata* batch, **not** corpus ingestion. It contains no article bodies, personal records, extracted participant cases, clinical chat transcripts, or model weights. All candidate `model_training_rights` are `not-cleared` and `source_content_included` is `false`.

## Method and deviations

- Read live `research/sources.json` (51 entries at start), then excluded matching identifiers and exact source URLs. Selected ten additional references across clinician guidelines/consensus, reviews and original cultural-formulation studies.
- Queried current public web indexes and preferred WHO/APA/ISTSS/ISSTD publisher pages, official DOI publishers and PubMed bibliographic/abstract records. The source-title, date, author and limitations fields were checked against the access level indicated on each record.
- **Research-log deviation:** Source exploration began before this method document was written; this is a retrospective method and claim ledger, not a preregistered confirmatory review. Relevance selections and narrative summaries are exploratory. A fresh independent audit is required before merge.
- Not a comprehensive systematic review. No meta-analytic weights, population inference, treatment effects, quality-grading GRADE judgments or professional clinical validation were produced.
- Stopping rule: up to ten distinct metadata entries with a primary/official URL, a specific useful limitation, and a rights quarantine. Ambiguous rights remain unverified.

## Evidence pointers

| ID | Primary source checked | Detail checked | Retrieval limits |
| --- | --- | --- | --- |
| who-stress-specific-guideline-2013 | https://www.who.int/publications/i/item/guidelines-for-the-management-of-conditions-that-are-specifically-related-to-stress | WHO page, 2013-01-01, 267-page guideline, ISBN | Did not clinically review all recommendations |
| apa-ptsd-clinical-guideline-2025 | https://www.apa.org/ptsd-guideline/ | APA states 2025 guideline and April 2025 update, distinguishes original 2017 page creation | Detailed PDF not fully appraised |
| istss-ptsd-prevention-guidelines-2018 | https://istss.org/clinical-resources/trauma-treatment/istss-prevention-and-treatment-guidelines/ | Society states 2018 guideline version, new revision forthcoming | Some evidence summaries restricted to members |
| isstd-did-treatment-guidelines-2011 | https://www.isst-d.org/publications-resources/resources-for-professionals/adult-treatment-guidelines/ | Society's 2011 citation, scope, explicit expert consensus | Not experimental efficacy proof |
| apa-dsm-cultural-formulation-interview-2013 | https://www.psychiatry.org/getmedia/5cc5329d-3bd4-4c6a-bae1-dfd0d6496f44/APA-DSM5TR-CulturalFormulationInterview.pdf | APA PDF rights notice, clinician/researcher-only exceptions, copyright 2013 | **Cannot republish or adapt instrument in TherapyBot without permission** |
| mattsson-trauma-memory-accuracy-review-2021 | https://pubmed.ncbi.nlm.nih.gov/33620914/ | Author list, PMID, DOI, 11-study review abstract | Full article not reviewed; no inference about individuals |
| sarr-icd11-complex-ptsd-assessment-review-2024 | https://onlinelibrary.wiley.com/doi/10.1002/cpp.3012 | Publisher 2024-06-18, four authors, limitations in §4.4 | Studies heterogeneous; no clinical gold standard established |
| adeponle-cultural-psychosis-reassessment-2012 | https://pubmed.ncbi.nlm.nih.gov/22302332/ | Publisher/PubMed date, DOI, authors, Canadian referral-study abstract | Specialty-clinic observational data, no randomized controls |
| adeponle-cultural-reasoning-psychosis-2015 | https://pubmed.ncbi.nlm.nih.gov/25310907/ | Publication March 2015, DOI, 23-case qualitative reasoning study | Specialty-clinic single-context qualitative evidence |
| loftus-pickrell-false-memory-experiment-1995 | https://journals.healio.com/doi/10.3928/0048-5713-19951201-07 | Original publisher authors, DOI, December 1995 date | Laboratory suggestion is not evidence any individual's report is false |

## Decision constraints for downstream use

1. Don't equate internal archetypes, metaphorical 'parts', unusual spiritual belief, dissociation, or trauma symptoms with DID, psychosis, or another diagnosis.
2. Explore phenomenology, distress, functioning, cultural meaning, alternative explanations and immediate practical safety without declaring unverified extraordinary causes as facts.
3. Do not use memory science to contradict a user's report; avoid leading questions or inducing confident recovered-memory narratives.
4. Guidelines and assessment tools are *professional* artifacts. TherapyBot can discuss them accurately but cannot claim to administer validated care or reproduce restricted questionnaire text.
5. Publisher availability and open access do not establish training, fine-tuning or redistribution rights. Independent licensing and clinical source-to-claim review remain mandatory.

## Status

Staged metadata syntax may be tested locally. Independent clinical validity, exact version completeness, licensing and claim-level section attribution are **unverified** until separate audit. No claim in this batch authorizes public interactive release.
