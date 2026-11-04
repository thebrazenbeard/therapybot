# TherapyBot × T’Kal-in-ket — multi-team adversarial architecture review

**Checkpoint:** 2026-11-04. **State:** Team Member 01's frozen in-memory case reached `CLOSED / REFINE`; GitHub multi-team proceedings remain OPEN, BT2's separate Q01 remains PARTLY_ANSWERED, not SUSTAIN. No clinical qualification or general-public interactive release.

## Actual shared proceedings

- [Team Member 01's frozen T’Kal-in-ket hearing #11](https://github.com/thebrazenbeard/t-kal-in-ket/issues/11): five actual native subagent opening comments and independent Chair process audit; three single-question, directed lens exchanges with respondent answers/concessions and an explicit challenger acknowledgment. Shared OpenAI provider/model family means these are separate native work assignments, **not** separately attested Lappy/VN1/VN2 model runs or professional clinical review.
- [BT2's independently created hearing #12](https://github.com/thebrazenbeard/t-kal-in-ket/issues/12): separate ChatGPT native work and subagent positions, feature/main cross-branch tests, its own still-partly-answered Q01 and [draft source hearing PR #13](https://github.com/thebrazenbeard/t-kal-in-ket/pull/13). Team Member 01 made a [real cross-chat response](https://github.com/thebrazenbeard/t-kal-in-ket/issues/12#issuecomment-6633241748); [BT2 acknowledged it](https://github.com/thebrazenbeard/t-kal-in-ket/issues/12#issuecomment-6633306923).
- [TherapyBot architecture issue #4](https://github.com/thebrazenbeard/therapybot/issues/4) holds implementation coordination; [issue #3](https://github.com/thebrazenbeard/therapybot/issues/3) preserves the backend/vault integration conflict. [T’Kal-in-ket issue #14](https://github.com/thebrazenbeard/t-kal-in-ket/issues/14) tracks a documented zero-attack waiver API absent from its source implementation.

**Actual protocol execution:** [reproducible `tkik.core.Case` replay and exact comment receipts](https://github.com/thebrazenbeard/t-kal-in-ket/issues/11#issuecomment-6633468623). An independent procedure auditor tested pinned `tkik.core` (39/39 tests passed), registered three distinct native-subagent reviewer IDs, and replayed the sequential directed dispositions `CONCEDED`, `CONCEDED`, `ANSWERED` with matching defender identities and challenger acknowledgment. `Case.determine('REFINE', ...)` completed with exit code 0. The case digest and script hash are in that linked record. This verifies local source-code state-machine behavior, **not** independently authenticated hosts, providers, clinicians, or a durable trusted case ledger.

**Frozen reviewed subject:** TherapyBot `main@6e0be42c7ff5115965584da015972cdc12092e0d`; T’Kal-in-ket `main@b0af150c2405b519fd921bac33e5f9f1f35f92d7`; alternate TherapyBot PR #1 `5c70bfc8ad535ee6bf62ff86770c0159020ceaa1` as captured in BT2's hearing. This document is a checkpoint, not proof that those are still live heads.

## Evidence that changes the decision

| Question | Observed evidence | Consequence |
| --- | --- | --- |
| Can the existing router reliably handle varied immediate danger? | Independent qualitative synthetic holdout: main matched 11/34; 12/13 urgent-route samples returned normal. BT2's separate replay on PR #1 matched 12/34, including 0/13 immediate and 0/9 concern. | **Do not publicly launch interactive mental-health support** on either implementation. These labels are not clinician consensus or population sensitivity estimates. |
| Do unit tests establish safety? | Main had 20 passing tests and a valid 32-record source metadata register; draft feature branch 27 passing tests; neither passed the independent safety holdout. | Test classes and model-output harm evaluations stay distinct; passing a fixture does not qualify a clinician-equivalent tool. |
| Does local GGUF work? | One bounded prior VN2 synthetic TherapyBot HTTP → ModelClient → llama.cpp Granite 2B GGUF request returned HTTP 200 in about 11.6 seconds. | A single host/backend protocol success, **not** multi-host model reliability, accessibility or safe response quality. |
| Are both vault implementations interchangeable? | Main Fernet/scrypt SQLite records and PR #1 AES-GCM/scrypt records have incompatible IDs, metadata, storage shapes and API surfaces. | No automatic merge or migration; require explicit opt-in, new destination, readback, backup and rollback. |
| Is source-linked text automatically scientifically grounded/training-licensed? | Current retrieval operates on short reference summaries and topical source IDs; external training/redistribution rights not cleared. | Require claim-level evidence reviews, license register and retrieval-injection resistance. |
| Is the proposed HTML accessible on narrow screens? | Source inspection of PR #1 found CSS hides the sole Lock button ≤780px and persistent crisis card ≤1260px, with dialog focus limitations. | Independently reproduce in actual browsers/assistive tech; do not replace the existing local UI solely for appearance or features. |

## Three-lens exchange and preserved concessions

1. **Purist Logic → Pragmatism:** [challenge](https://github.com/thebrazenbeard/t-kal-in-ket/issues/11#issuecomment-6633130512); [respondent concession / conditional answer](https://github.com/thebrazenbeard/t-kal-in-ket/issues/11#issuecomment-6633169894). Current implementation is insufficient for a general-public beta; retaining Python/HTML/GGUF is a *conditional engineering choice*, not a readiness claim.
2. **Pragmatism → Bridge:** [challenge](https://github.com/thebrazenbeard/t-kal-in-ket/issues/11#issuecomment-6633198215); [respondent concession / bounded proposal](https://github.com/thebrazenbeard/t-kal-in-ket/issues/11#issuecomment-6633271353). Socially context-aware responses are not verified in current code; proposed testable behaviors include respecting explicitly stated constraints, no unsolicited demographic interpretation, no fabricated local providers and no forced sociological reframing.
3. **Bridge → Purist Logic:** [challenge](https://github.com/thebrazenbeard/t-kal-in-ket/issues/11#issuecomment-6633322672); [response](https://github.com/thebrazenbeard/t-kal-in-ket/issues/11#issuecomment-6633374966); [challenger acknowledgment](https://github.com/thebrazenbeard/t-kal-in-ket/issues/11#issuecomment-6633423363). Safe non-model learning/journal features need not await LLM clinical studies; publicly promoted interactive mental-health support does require much stronger gates.

The [clinical methodological addendum](https://github.com/thebrazenbeard/t-kal-in-ket/issues/11#issuecomment-6633337358) rejects a misleading statistical inference from zero failures in a finite, correlated synthetic sample. Numerical thresholds proposed by engineering reviewers are **unapproved test proposals**, not the owner's threshold, a measured pass or clinical effectiveness evidence. The [Advocate cross-branch review](https://github.com/thebrazenbeard/t-kal-in-ket/issues/11#issuecomment-6633349797) is source-level, not a browser accessibility certification.

## Provisional design direction (not a binding architectural decision)

1. Keep a **small, auditable, $0 Windows/Linux local application** with real HTML conversation, journal and sources; keep public Pages an informational noninteractive seed. Avoid compulsory account, survey, remote model/analytics or vault unlock before ordinary unsaved local conversation.
2. Treat the present `main` implementation as a reversible **development integration base**, not an approved public-release baseline. Evaluate importing PR #1's authenticated backup, CSP/session and UX improvements in narrow, independently tested pieces; leave incompatible encrypted data untouched until an explicitly consented migration plan passes readback/rollback tests.
3. Maintain GGUF KoboldCpp and llama.cpp adapters, benchmark model-template correctness, memory, response latency and failures on authorized real Windows/Linux hosts. Preserve helpful **no-model** functions when inference is unavailable; never silently fallback to paid/cloud APIs.
4. Expand licensed source-level retrieval with claim-specific provenance and local cache; distinguish evidence types, legal training rights and unverified philosophical/spiritual interpretations. Do not train on private user records by default or copy proprietary articles without rights.
5. Make explicit user-reported social constraints relevant without inferring personal traits, assigning diagnosis, inventing nearby services, or reducing structural hardship to a faulty thought pattern. Accessibility, culture, language and low-resource testing need separate evidence.

## Release categories and outstanding gates

- **Private developer testing:** permitted with transparent limitations and synthetic prompts, no personal-data ingestion in tests.
- **Model-independent educational/journal tools:** may be separately qualified by privacy, access, source and usability tests.
- **Public interactive AI-support beta:** **on hold by owner direction**, pending repaired crisis behavior, generated-answer harm/citation reviews, network/privacy validation, record recovery and accessible runtime tests across supported hardware and users.
- **Clinical/therapeutic service:** outside the current product claim; would require appropriately qualified human clinical evidence and governance, not an agent-panel verdict.

The owner stated to BT2, as [quoted in the verified cross-chat hearing](https://github.com/thebrazenbeard/t-kal-in-ket/issues/12#issuecomment-6633306923), that the software **would not be for public release until those issues are resolved**. The BT2 Q01 remains **PARTLY_ANSWERED** pending specific future acceptance criteria; this document must not close that question on BT2's behalf.

**Current determination:** Team Member 01's frozen in-memory case is `REFINE`, while the multi-team GitHub hearings remain open and BT2's separate question is only partly answered. Preserve all failures and dissent and allow no automatic implementation effect. A `SUSTAIN` claim would be inappropriate: no independently authenticated multi-provider quorum or clinical efficacy has been demonstrated.
