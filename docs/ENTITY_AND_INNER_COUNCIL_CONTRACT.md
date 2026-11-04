# Resident conversational entity and user-owned Inner Council (developer contract)

**Status:** Experimental feature design and implementation testbed; **not an approved name, trained model, clinical intervention, or public interactive release**. This document governs `embedded/` work on draft PR #11 only. Competing `static/offline.html` development in PR #12 must not be silently merged into a second canonical engine.

## Identity before naming

The resident conversational entity has no ratified proper name. An earlier name candidate was rejected by the owner. Its interaction identity is stable across runtimes, but its claims cannot exceed the capability of the active runtime.

Its proposed character: intellectually honest, attentive to material constraints, compassionate without condescension, capable of useful disagreement, occasionally dryly funny, and explicit about evidence limits. It does not diagnose, certify risk, claim privileged access to a user's mind, claim independent Council members are clinically separate identities, or imply validated therapy. It neither infantilizes the user nor gives itself authority over the user's decisions.

The **Inner Council** is an optional, user-invoked reflective feature. It is not a compulsory mental-health theory. A Council member represents a perspective that the user chooses to name and configure. A user who reports involuntary or frightening voices is not automatically placed into simulated roleplay; the app must distinguish that disclosure from a user-authored Council command.

## Contract

- **Default:** No Council members, no hidden predefined personalities, no imported trauma record, no saving, no network inference, no training.
- **Member:** A short user-authored name, role, and optional notes about its concerns or values. The initial prototype keeps member profiles in volatile tab memory.
- **Conversation:** Direct conversation with the entity; normal topic/context behavior and its honest limits.
- **Council:** Invoked by `Council:` or a visible **Convene** action. Present only currently configured members, with each clearly labeled as a simulated reflective perspective. Leave disagreements visible. An empty Council asks the user to configure members rather than inventing them.
- **Solo:** `Solo <configured name>:` invokes exactly one known member; missing names receive a non-fabricating explanation.
- **Integrate:** `Integrate:` identifies possible shared priorities and tensions without claiming a diagnosis or forced consensus.
- **Containment:** `Containment:` or the visible **Return to direct chat** toggle ends the simulated voices and returns to direct conversation.
- **Safety ordering:** Evaluate user input through the base safety route **before** any Council generation. A non-normal route vetoes persona responses. This is defense-in-depth, not a validated clinical risk screen; independent hostile examples already demonstrate substantial false negatives in the existing base engine.
- **Clear chat:** Clears only the conversation transcript; configured Council profiles remain visibly marked as unsaved in the current tab.
- **Forget all:** With confirmation, destroys the conversation transcript and configured Council profiles from tab memory; neither is stored or synced. No analytics, auto-export, or silent cloud sync.
- **Rendering:** Untrusted input and member names are rendered via `textContent` rather than an HTML sink.

## Provenance boundary

The owner-supplied `Active_Archetypes.md` is dated 2025-05-21 and documents a 23-seat personal Council. An accessible conversational record contains assistant wording about an “Inner Council of 34” on 2025-04-19. These are *earliest retrieved* records, not proof of invention or a complete history. The May field manual also places “Pacifist Warrior” in its constellation table while profiling “Martyr” instead; do not resolve this disagreement by silently guessing.

That personal framework may inspire optional **owner-private** experiments. It must never be copied into every new user's default Council. Consent to use the owner's material for private development does not waive the privacy of other people mentioned in it, training rights, or the public release hold. Roots' discovery-versus-origin distinction applies: <https://github.com/thebrazenbeard/roots/blob/main/docs/methodology.md>.

## Testable user experience

1. Starting from a fresh tab, the user sees an empty Council and can enter a name and role without an account or local inference server.
2. A `Council:` request makes no claims about members not configured by that user.
3. At least two configured members can respond with distinguishable, explicitly simulated viewpoints and a separate facilitator synthesis.
4. `Solo <name>:` addresses one matching member. Unknown names do not silently create identities.
5. A dangerous statement prefixed with `Council:` is evaluated for risk before Council mode; known high-risk phrases must not generate upbeat Council discussion.
6. `Containment:` is immediately available and deactivates an active Convene selection for subsequent turns. Clear chat empties the transcript; Forget all additionally resets Council members.
7. Sequential workplace and follow-up turns retain relevant topic context where a short follow-up has no new topic words; a correction should not blindly inherit an unwanted topic.
8. Actual rendered Edge conversation, keyboard, responsive layout, and console behavior are measured independently of Node VM tests.

## Unmet release criteria

The current semantic engine is not neural, conversationally general, clinically evaluated, or safe on independent harm-reserve tests. Browser-native GGUF via a pinned WASM runtime is a separate milestone. Do not expose an interactive public site or imply model training, clinical approval, complete safety routing, full offline model delivery, or resident consciousness as verified product capabilities.
