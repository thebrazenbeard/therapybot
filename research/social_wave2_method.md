# Sociology evidence wave 2 — research record (2026-11-04)

## Frozen question and scope (pre-retrieval)

Which six to ten **additional** authoritative, non-duplicative sources can improve TherapyBot's coverage of social determinants, isolation, abusive relationships, poverty, stigma, discrimination, disability and culturally responsive support without converting group research into individual diagnosis or silently copying training text?

## Hypotheses and falsifiers

- **S1:** Recent first-party public-health material covers modifiable structural and social contexts insufficiently addressed in `research/sources.json`. Prediction: at least two official pages with supported scope statements and new URLs. Falsifier: all candidates are duplicates or do not support the stated scope.
- **S2:** Peer-reviewed primary observational and review literature can provide more nuanced association/limits for discrimination, socioeconomic adversity and social connection. Prediction: at least four independently checkable DOI/official article entries with study type and applicability limitations. Falsifier: titles, author/date, evidence design or DOI cannot be verified.
- **S3:** An appropriately grounded support bot should not translate population correlations into personal causes. Prediction: every selected record can be summarized with a concrete non-causal or scope limitation. Falsifier: a record would require unsupported personalized inference or imply that structural harm is merely an individual's cognitive error.

## Planned methods and stopping

- **SC1 confirmatory:** inspect existing source IDs and URLs; reject duplicates and note schema.
- **SC2 confirmatory:** search current WHO/CDC/HHS and peer-reviewed primary DOI/publication pages; inspect source metadata and abstract/section descriptions.
- **SC3 confirmatory:** create source records matching existing JSON metadata; no third-party article bodies, no private data, training rights `not-cleared`.
- **SC4 confirmatory:** parse JSON and verify unique IDs/URLs against baseline and that each record contains provenance fields; report exact command/output.
- **SC5 exploratory:** seek a falsifying independent read of source claims and limitations; if no independent reviewer available, explicitly leave this unverified.
- Stop when 6–10 nonduplicate records are logged or when authoritative retrieval is blocked; no assertion of model training/clinical efficacy or universal validity.

## Evidence log (append-only after retrieval)

- P1, baseline source schema and 32 IDs: `research/sources.json`, inspected 2026-11-04. No internet evidence yet.

## Retrieval evidence — 2026-11-04

- E1, WHO primary page `https://www.who.int/publications/i/item/9789240107588` (web ref `turn49view0`): title, 6 May 2025, report type, Overview's equity/resource context; text anchor `# World report on social determinants of health equity`.
- E2, WHO primary page `https://www.who.int/publications/i/item/978240112360` (web ref `turn49view1`): title, 30 June 2025, 213-page commission report, Overview's isolation/connection scope; text anchor `# From loneliness to social connection`.
- E3, HHS primary `https://www.hhs.gov/surgeongeneral/reports-and-publications/connection/index.html` (web ref `turn53search0`) and linked 2023 advisory `https://www.hhs.gov/sites/default/files/surgeon-general-social-connection-advisory.pdf` (web ref `turn53search6`): advisory title, 2023 date, social/community scope. Link rather than ingest PDF.
- E4, CDC primary `https://www.cdc.gov/mental-health/about/` (web ref `turn49view7`): lines 85–105 enumerate societal drivers including discrimination, housing, employment, violence and social isolation; explicitly says risk factors are not deterministic.
- E5, CDC primary `https://www.cdc.gov/intimate-partner-violence/about/index.html` (web ref `turn53search1`): updated Aug. 19 2026, definitions and potential psychological effects. No individual situation classification implied.
- E6, PubMed PMID 25910392 `https://pubmed.ncbi.nlm.nih.gov/25910392/` (web refs `turn48search0`, `turn53search3`): Holt-Lunstad et al. 2015, DOI 10.1177/1745691614568352, observational mortality meta-analysis.
- E7, PubMed PMID 40643383 `https://pubmed.ncbi.nlm.nih.gov/40643383/` (web ref `turn50view0`): Jespersen et al. 2025, DOI 10.1093/epirev/mxaf011, SES/depression systematic review and meta-analysis.
- E8, PubMed PMID 39306008 `https://pubmed.ncbi.nlm.nih.gov/39306008/` (web refs `turn50view4`, `turn53search2`): Maletta et al., online Sep. 2024 / published Jan. 2025, DOI 10.1016/j.jad.2024.09.128; observational self-report cohort limitations.
- E9, PubMed PMID 41411028 `https://pubmed.ncbi.nlm.nih.gov/41411028/` (web ref `turn50view2`): Rubin-McGregor & Hunger, Aug. 2026, DOI 10.1037/rep0000643; N=5115 observational design.
- E10, PubMed PMID 42064325 `https://pubmed.ncbi.nlm.nih.gov/42064325/` (web ref `turn51view0`): Bora et al., Mar. 2026, DOI 10.1017/gmh.2026.10183; randomized-trials systematic review, heterogeneous outcomes.

## Scope and rights conclusions

SC1–SC3: ten candidate metadata records drafted with original short summaries, no source bodies, no known duplicated IDs/URLs in the baseline index. These **do not** validate any diagnosis, establish causal explanations for users, license training, or qualify TherapyBot for release. Third-party text redistribution and training rights are explicitly unconfirmed.

SC5: independent content verification has **not** yet been performed by a second reviewer. Root integration and hostile review are still needed before asserting that every summary accurately reflects its source.

## Validation result

- SC4 CONFIRMATORY, PASS, exit code 0: ran a read-only `python -c` JSON/schema/deduplication check comparing `social_sources_wave2.json` with the baseline `sources.json`. Decisive stdout: `PASS: 10 unique source records; no duplicate baseline IDs/URLs; schema and rights boundary valid`.
- SC1–SC4 closed; SC5 independently reviewed status remains **OPEN**. This is structural and initial authoring validation only, not independent scientific correctness review.
