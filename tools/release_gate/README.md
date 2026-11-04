# Browser safety release-gate probe — source only

This diagnostic executes the actual pages/lab/lab.js with a stubbed browser DOM and stubbed generic rules provider. It captures the resident outputGate and drives actual form submit handling to measure pre-provider emergency routing. It is intentionally not a clinical judge.

All fixtures are original synthetic test sentences. No patient transcripts, private trauma data, external model weights, network calls, or credentials.

## Commands

- node --test tools/release_gate/probe.test.cjs : proves test harness and fixture structure.
- node tools/release_gate/probe.cjs : emits detailed scored findings; returns exit 0 even when the PRODUCT fails, for diagnostics.
- node tools/release_gate/probe.cjs --enforce : exits 2 when any fixture fails, providing a fail-closed check for future release gates.

## Honest evidence

Evidence class SOURCE_EXECUTED_WITH_STUBBED_BROWSER_DOM. The generic provider is deliberately stubbed; multi-turn conversational quality is NOT tested. Neural model token generation, real Edge/Firefox operation, clinical validity, visitor privacy and public origin are NOT tested. The lexical outputGate cannot be qualified as a semantic filter through synthetic regex fixtures.

The independently researched study by Arnaiz-Rodriguez et al., Between Help and Harm, JMIR Mental Health 2026, DOI 10.2196/88435, identifies dangerous weaknesses on indirect/ambiguous crises and formulaic responses. Our small original fixture set targets those specific failure patterns plus fiction/history and third-party context; it does NOT cover that study's six-category taxonomy or replicate any of its expert validation. No external dataset was copied and no clinician qualification is claimed.

Release verdict is ALWAYS HOLD_PENDING_INDEPENDENT_QUALIFICATION regardless of fixture pass counts: these checks are a narrow negative falsification probe, not an affirmative license to deploy.

## Follow-up

Treat each failed neural-output case as a request for a qualified independent review mechanism, not an invitation to keep extending fragile keyword lists. Independently test current third-party harm, fiction, history, stop/clear, multi-turn semantics and browser behavior. Preserve this frozen fixture set and use fresh unseen cases against any proposed correction.
