# Clinical source-expansion wave — 2026-11-04

This is a **bibliographic exploration**, not a pre-registered clinical trial, prospective confirmatory experiment, endorsement, or legal clearance. It extends TherapyBot's existing metadata-only collection without downloading source bodies or incorporating patient text. The root research log's frozen TherapyBot/T'Kal-in-ket question predates this wave; these nine records are exploratory additions to its evidence base.

## Selection and source inspection

| Record ID | Primary source inspected | Observation and evidence ceiling |
| --- | --- | --- |
| `va-dod-ptsd-asd-2023` | https://healthquality.va.gov/HEALTHQUALITY/guidelines/MH/ptsd/ | Official title/year, clinician disclaimer, and three modules inspected. Guidelines require clinical judgment. |
| `va-dod-major-depression-2022` | https://www.healthquality.va.gov/HEALTHQUALITY/guidelines/MH/mdd/index.asp | Official MDD guideline landing confirmed 2022. No recommendation-by-recommendation grading check performed here. |
| `va-dod-suicide-risk-2024` | https://www.healthquality.va.gov/guidelines/MH/srb/ | Official 2024 suicide-risk guideline listing confirmed. Not a chatbot classifier validation dataset. |
| `nice-psychosis-schizophrenia-cg178` | https://www.nice.org.uk/guidance/cg178 | Official NICE overview title and 2014 publication; 2025 surveillance review noted. No symptom-to-diagnosis rules extracted. |
| `nice-anxiety-panic-cg113` | https://www.nice.org.uk/guidance/cg113/chapter/recommendations | Official NICE recommendations and 2020 amendment references, original 2011 guideline. Medication details deliberately omitted. |
| `nice-bipolar-cg185-2025update` | https://www.nice.org.uk/guidance/cg185 ; https://www.ncbi.nlm.nih.gov/books/NBK547001/ | NICE direct open returned HTTP 403 in one retrieval; publication/update metadata cross-checked via official search result and NCBI mirror. **Lower verification confidence** until direct NICE page is available. |
| `samhsa-trauma-informed-2014` | https://library.samhsa.gov/sites/default/files/sma14-4884.pdf ; https://www.samhsa.gov/mental-health/trauma-violence/trauma-informed-approaches-programs | 2014 SAMHSA primary framework and updated official overview indexed; SAMHSA page direct open returned 403. Six principles are organizational guidance, not outcome trials. |
| `who-mental-health-work-2022` | https://www.who.int/publications-detail-redirect/9789240053052 | WHO official 28 September 2022 publication page for work-related policy and intervention guidance. |
| `kong-act-depression-meta-2025` | https://pubmed.ncbi.nlm.nih.gov/40885141/ ; https://doi.org/10.1016/j.psychres.2025.116701 | PubMed PMID, author list and abstract inspected; ten trials, review authors rated depression effect certainty low. Does not validate chatbot-led ACT. |

All records have `retrieved=2026-11-04`, original short summaries, explicit uncertainties, `source_content_included=false`, `source_license=unverified` and `model_training_rights=not-cleared`. Links are **reference pointers, not a license to train or redistribute**.

## Next falsifiable integration checks

1. An independent reviewer should verify exact title/publication date, URL and summary against each source, including the NICE pages that returned 403 in this wave.
2. Source IDs and normalized URLs must not collide with `research/sources.json` or another concurrently authored evidence tranche.
3. Every cited TherapyBot answer should distinguish clinical recommendations for professionals from nonclinical support and include verifiable claim-to-section provenance; this is **not** achieved by metadata integration alone.
4. Model response testing must show no autonomous diagnosis, medication prescribing, or unsafe reassurance in held-out synthetic dialogs; a metadata check cannot establish this.

## Known gaps

- No source full text retained; no source-content hashing or exact section quotation permission determined.
- No formal GRADE verification across all nine sources and no representative evidence review on access for under-resourced populations.
- Observational bibliographic inspection and official-page retrieval are evidence of provenance, not evidence of clinical efficacy or model-training rights.
