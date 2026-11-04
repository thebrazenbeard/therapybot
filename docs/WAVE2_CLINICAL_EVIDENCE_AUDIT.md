# Independent clinical-source metadata audit — 2026-11-04

## Frozen question and scope

Are the nine new source pointers in `research/clinical_sources_wave2.json` accurately identified, nonduplicative, conservatively characterized, and suitable for the **metadata** register, without implying full-text licensing, autonomous therapeutic efficacy, or clinical-source verification beyond actual access?

This audit is independent of the source-record author's assignment, but not a credentialed clinical review. No private records are in scope.

### Pre-registered hypotheses and falsifiers

- **A1:** Each source exists on its stated official/primary platform with matching topic, title/year and URL. Falsifier: unrelated/dead link, inaccurate date/title, or inaccessible evidence for a precise assertion.
- **A2:** Each summary and limitation avoids transferring clinician recommendations to unqualified chatbot treatment or diagnostic claims. Falsifier: unsupported claims of proven chatbot effectiveness, suicide prediction, or unqualified generalization.
- **A3:** Each source has unique ID/URL and explicit rights restrictions. Falsifier: collision, bulk copyrighted text, training rights presented as cleared.

### Methods and stopping rules

- **CA-1 confirmatory:** Validate schema, IDs, URLs and rights against baseline `research/sources.json` and new tranche, preserve output and command.
- **CA-2 exploratory:** Look up all nine official/primary source pages via web-search snippets or open; check titles, year and crucial methodological distinctions, explicitly recording inaccessible direct pages.
- **CA-3 confirmatory:** Review every summary/limitation against observed primary content and issue a per-record verdict; distinguish the metadata's suitability from deeper claim-to-guideline verification.
- Stop after all nine source records are classified, with specific corrections or evidence gaps listed. No records should be merged or altered by this reviewer.

## Evidence and findings (append below; no pre-registration changes)

### Evidence log

- **CA-E1, exact source artifact.** `research/clinical_sources_wave2.json`, SHA-256 `a15ac73a8012ba9c32e2dfee27689d9c291ccae58782f52dfff2a623f22d270f`; author's method note SHA-256 `feb55b42b766bf9585e205ce85fe9c6a2e3e489a8a46e97e13e3f81a7f835dd7`. Read 2026-11-04. No source PDF or patient record committed in these files.
- **CA-E2, confirmatory local execution.** `python scripts/merge_research_sources.py research/clinical_sources_wave2.json` exit `0`: `source register: 32 existing + 9 staged = 41; mode=DRY-RUN; not a rights/scientific audit`. The tool rejects duplicate IDs/URLs and missing or falsely cleared rights, but does **not** validate scientific claims or HTTPS availability.
- **CA-E3, official VA/DoD direct page retrieval.** [PTSD/acute stress 2023](https://healthquality.va.gov/HEALTHQUALITY/guidelines/MH/ptsd/), [MDD 2022](https://www.healthquality.va.gov/HEALTHQUALITY/guidelines/MH/mdd/index.asp), [suicide risk 2024](https://www.healthquality.va.gov/guidelines/MH/srb/); official pages returned title/year, clinical scope and clinician-judgment disclaimers on 2026-11-04.
- **CA-E4, indexed NICE official sources but direct access blocked.** Official search results for [CG178 psychosis](https://www.nice.org.uk/guidance/cg178) showed 2014 publication and last review July 2025; [CG113 anxiety/panic](https://www.nice.org.uk/guidance/cg113) showed 2011 origin and June 2020 amendment; [CG185 bipolar](https://www.nice.org.uk/guidance/cg185) showed 2014 publication and 2 September 2025 update. Each direct `open` attempt returned **HTTP 403** in this audit, so exact full guideline passages were **not** independently retrieved.
- **CA-E5, public-health original source.** [SAMHSA 2014 framework PDF](https://library.samhsa.gov/sites/default/files/sma14-4884.pdf) retrieved; page 11 enumerates safety, transparency, peer support, collaboration, empowerment/voice/choice, and cultural/historical/gender issues. This is a framework for organizations, not a chatbot outcomes study.
- **CA-E6, WHO publication.** [WHO Guidelines on mental health at work](https://www.who.int/publications-detail-redirect/9789240053052) retrieved, dated 28 September 2022, covering organizational/worker/manager/return-to-work support. Official publication uses the title **“Guidelines on mental health at work”**; the drafted record prefixes `WHO` to the title. This is a minor bibliographic correction, not a substantive error.
- **CA-E7, PubMed primary index.** [Kong et al., PMID 40885141](https://pubmed.ncbi.nlm.nih.gov/40885141/), publication date 2025, DOI `10.1016/j.psychres.2025.116701`, ten RCTs. Abstract's authors rate depression effects low certainty, anxiety effects moderate, psychological-flexibility effects high. The full journal article and its own evidence appendix were not reviewed here.
- **CA-E8, cross-file duplicate scan.** `rg -n 'va-dod|kong-act|nice-psychosis|samhsa-trauma|who-mental-health-work|nice-anxiety-panic|nice-bipolar' therapybot/sources.json research/sources.json` showed no matching existing IDs. This supplements CA-E2's normalized ID/URL check against the 32-record research register.

### Per-record results

| ID | Metadata assessment | Important qualification |
| --- | --- | --- |
| `va-dod-ptsd-asd-2023` | **Confirmed** at official landing-page level | Correct year, scope and clinician-only disclaimer; no 34-recommendation evidence audit. |
| `va-dod-major-depression-2022` | **Confirmed** at official landing-page level | Correct year and clinician context; no recommendation-by-recommendation strength review. |
| `va-dod-suicide-risk-2024` | **Confirmed** at official landing-page level | Correct 2024 guidance; no evidence this validates TherapyBot's classifier. |
| `nice-psychosis-schizophrenia-cg178` | **Partially confirmed** | Official indexed title/date/surveillance consistent; direct NICE content fetch failed 403. |
| `nice-anxiety-panic-cg113` | **Partially confirmed** | Official indexed 2011/2020 dates consistent; no direct content review in this audit. |
| `nice-bipolar-cg185-2025update` | **Partially confirmed** | Official indexed 2014 original/2025 update consistent; no independent full guideline read. |
| `samhsa-trauma-informed-2014` | **Confirmed** at framework-description level | Framework principles match page 11, but no proof of AI treatment efficacy. |
| `who-mental-health-work-2022` | **Confirmed with minor correction** | Change `title` to exact WHO title “Guidelines on mental health at work”; retain issuer WHO. |
| `kong-act-depression-meta-2025` | **Confirmed** at indexed abstract level | Ten RCTs and relative certainty correctly caveated; no independent risk-of-bias reassessment. |

### Verdict: **partially-confirmed**

The nine records are suitable **as cautiously worded, link-only research metadata candidates** after the minor WHO title correction, provided the merge is described as **bibliographic indexing** rather than training clearance, clinical-source section validation, or safe model behavior. The three NICE entries have independently indexed official bibliographic evidence but direct page access failed; preserve that lower verification ceiling and their existing caveats.

**Unanswered:** Full recommendation-level provenance and review dates, independent clinical content approval, licensing/training permissions, actual retrieval grounding of generated responses, and representative patient-population outcomes remain open. `source_license: unverified` and `model_training_rights: not-cleared` must remain restrictive even when a document has a permissive distribution license.

> **Hostile challenge:** A working URL and an accurate summary do not mean a local model can safely interpret clinical guidelines. A source pointer cannot be promoted to therapy efficacy, risk prediction, prescribing authority or permission to train weights.
