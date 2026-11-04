# Browser safety release-gate probe — source only

This diagnostic executes the actual pages/lab/lab.js with a stubbed browser DOM and stubbed generic rules provider. It captures the resident outputGate and drives actual form submit handling to measure pre-provider emergency routing. It is intentionally not a clinical judge.

All fixtures are original synthetic test sentences. No patient transcripts, private trauma data, external model weights, network calls, or credentials.

## Commands

- node --test tools/release_gate/probe.test.cjs : proves test harness and fixture structure.
- node tools/release_gate/probe.cjs : emits a local-gate diagnostic; returns exit 0 when tested boundaries miss synthetic fixtures, for analysis.
- node tools/release_gate/probe.cjs --enforce : exits 2 when either local neural gate or local pre-provider routing misses a fixture.
- node tools/release_gate/engine_route_probe.cjs : separately executes the ACTUAL embedded/engine.js source and reports safety.route; no adapter stub is involved in this second check.

## Honest evidence

Evidence class SOURCE_EXECUTED_WITH_STUBBED_BROWSER_DOM. The lexical neural outputGate executes directly, but for chat turns only the pre-provider localRoute is genuinely exercised. The generic downstream adapter.turn is deliberately stubbed and always generic: a miss in this probe proves only that the local pre-provider router failed to intercept it, NOT that a downstream engine or complete product necessarily misses it. The separate engine_route_probe.cjs independently executes the actual embedded engine source (no browser) and records its safety.route; its four third-party cases currently also return normal. These are two distinct source-execution observations, NOT real integrated browser or clinical validation. Multi-turn quality, neural token generation, real Edge/Firefox behavior, clinical validity, visitor privacy and public origin are NOT tested. The lexical outputGate cannot be qualified as a semantic filter through these fixtures.

The independently researched study by Arnaiz-Rodriguez et al., Between Help and Harm, JMIR Mental Health 2026, DOI 10.2196/88435, identifies dangerous weaknesses on indirect/ambiguous crises and formulaic responses. Our small original fixture set targets those specific failure patterns plus fiction/history and third-party context; it does NOT cover that study's six-category taxonomy or replicate any of its expert validation. No external dataset was copied and no clinician qualification is claimed.

Release verdict is ALWAYS HOLD_PENDING_INDEPENDENT_QUALIFICATION regardless of fixture pass counts: these checks are a narrow negative falsification probe, not an affirmative license to deploy.

## Follow-up

Treat each failed neural-output case as a request for a qualified independent review mechanism, not an invitation to keep extending fragile keyword lists. Independently test current third-party harm, fiction, history, stop/clear, multi-turn semantics and browser behavior. Preserve this frozen fixture set and use fresh unseen cases against any proposed correction.
