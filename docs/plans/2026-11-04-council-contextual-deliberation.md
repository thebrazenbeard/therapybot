# Contextual Inner Council Pilot Implementation Plan

> **For agentic workers:** Use the host's available task-by-task implementation workflow. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make simulated Council perspectives contrast bounded work and relationship decisions without echoing user-authored profile instructions as speech.

**Architecture:** Keep the existing public `TherapyBotCouncil.respond(input)` API and independent base safety veto. Use the base engine's *actual* topic state to select a small fixed topic-by-lens argument table. Only distinct lenses receive a conditional synthesis; unsupported topics retain a transparent generic reflection.

**Tech Stack:** Classic browser JavaScript; Python `unittest` invoking Node VM with network/storage APIs prohibited.

**Execution checkpoint:** Both tasks implemented in this isolated branch. The 134-test Python suite and JavaScript syntax checks passed; the updated Puppeteer browser script remains unexecuted on this Linux runner. Public mental-health release stays on hold.

## Global Constraints

- No external inference, persistence, default Council members, new identities, clinical advice or public release.
- User-created member names remain labels only in the UI; generated speech uses `Perspective N`.
- User-created roles, focus, notes, questions, and topic text never become generated stance sentences.
- Safety and unsupported-language routes take precedence; the lexical base engine is unvalidated and has known misses.
- Avoid copying PR #12's competing dialogue engine; this is a bounded PR #11 experiment.

---

### Task 1: Verified contextual lens positions

**Files:**
- Modify: `embedded/council.js` (`safeBase`, `perspective`, pilot template table)
- Test: `tests/test_embedded_council.py`

**Interfaces:**
- Consumes: `TherapyBotEmbedded.respond({message,history})` and `TherapyBotCouncil.respond(input)`.
- Produces: `perspective(member,index,topic)` with existing `{id,name,role,text}` speaker shape.

- [ ] **Step 1: Add focused failing tests**: normal work and relationship requests with identical Evidence/Practical members yield topic-specific distinct text; caller-forged `baseResult.state.topic` cannot choose a false frame; unknown topic has no fabricated work or relationship advice; non-normal safety route still returns base response.
- [ ] **Step 2: Verify failure** with `python -m unittest tests.test_embedded_council -q`; expect contextual and forged-topic assertions to fail on the static-lens baseline.
- [ ] **Step 3: Implement** a fixed work/relationships × Evidence/Practical/Values/Protective/Alternatives table; use independently obtained base topic, discard caller-controlled topic claims, keep the established safe fallback for all other topics.
- [ ] **Step 4: Re-run focused tests**; expected all pass without changed speaker schema or profile amplification.
- [ ] **Step 5: Run the full suite** using `python -m unittest discover -s tests -q` and JS syntax checks; expected zero regressions.
- [ ] **Step 6: Commit** this independently passing deliverable with `git add embedded/council.js tests/test_embedded_council.py` and a narrowly scoped commit message.

### Task 2: Conditional contrast and consistent modes

**Files:**
- Modify: `embedded/council.js` (`council`, `solo`, `integration`)
- Test: `tests/test_embedded_council.py`

**Interfaces:**
- Consumes: verified topic and existing generated speaker roles/text from Task 1.
- Produces: `facilitator` with explicit possible tension only when at least two distinct lenses have pilot arguments; otherwise no invented disagreement.

- [ ] **Step 1: Add focused failing tests**: different lenses on a supported topic yield distinct stances and conditional tension; identical lens categories do not claim tension; Solo and Integration use the same pilot topic frame; unsupported topic admits limits; adversarial member names/notes/roles do not appear as generated arguments.
- [ ] **Step 2: Verify failure** with `python -m unittest tests.test_embedded_council -q`; expect missing-context/false-synthesis assertions to fail.
- [ ] **Step 3: Implement** a bounded pairwise topic tension table independent of profile text; preserve the existing first-four speaker cap and standalone Containment mode.
- [ ] **Step 4: Re-run focused tests**, expected all pass.
- [ ] **Step 5: Run all Python tests, Node syntax, and `git diff --check`**, expected passes. Do not assert behavioral or clinical qualification.
- [ ] **Step 6: Commit** test and implementation changes on the isolated branch; no push or deployment.

## Unresolved product decisions

- Whether future neural model output may supply arguments instead of bounded templates remains a separate review and consent gate.
- How users should choose between one question per perspective and longer multi-round deliberation requires real-user feedback; the pilot keeps one round.
