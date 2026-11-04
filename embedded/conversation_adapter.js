/*
 * Experimental TherapyBot browser conversation boundary.
 * This is orchestration, NOT a neural model, clinical safety gate, or
 * authenticated sandbox for a provider supplied by other JavaScript.
 * It has no network or storage API calls and never loads a remote provider.
 */
(function (root) {
  'use strict';

  const KINDS = Object.freeze(['bounded-semantic', 'in-browser-neural']);
  const MODES = Object.freeze(['direct', 'council', 'solo', 'integration', 'containment']);
  const MAX_HISTORY = 24;
  const MAX_MESSAGE = 8000;
  const MAX_REPLY = 12000;
  const ROUTES = Object.freeze(['normal', 'concern', 'urgent_review', 'immediate', 'unknown']);
  const PROVIDER_CONCERN = 'A configured provider flagged a possible concern, but its words and safety label have not been independently verified. If anyone is in immediate danger, contact local emergency services.';
  const PROVIDER_URGENT = 'A configured provider flagged possible immediate danger, but I cannot assess urgency or intent. If anyone may be in immediate danger, contact local emergency services now. In the U.S., you can call or text 988 for crisis support.';
  const PROVIDER_UNKNOWN = 'I cannot validate this provider\'s safety routing for this message. If someone may be in immediate danger, use local emergency services. This is not an assessment of safety.';
  const OUTPUT_REVIEW_HOLD = 'I cannot independently review this optional engine\'s output in this build, so I will not display a generated answer.';

  function validResidentResult(result) {
    return result && typeof result === 'object' && typeof result.reply === 'string' &&
      result.reply.trim() && result.safety && ROUTES.includes(result.safety.route);
  }

  function providerVeto(route) {
    return {
      reply: route === 'concern' ? PROVIDER_CONCERN :
        route === 'urgent_review' || route === 'immediate' ? PROVIDER_URGENT : PROVIDER_UNKNOWN,
      supportedTopic: false, sources: [], state: {},
      uncertainty: 'The provider route is unverified; its supplied prose has been suppressed.',
      safety: { route: ROUTES.includes(route) ? route : 'unknown', coverage: 'unvalidated' }
    };
  }

  function errorResult(status, reason) {
    return Object.freeze({ status, reason, reply: null });
  }

  function validProvider(provider) {
    return provider && typeof provider === 'object' &&
      typeof provider.respond === 'function' &&
      typeof provider.id === 'string' && /^[a-z][a-z0-9._-]{1,63}$/.test(provider.id) &&
      KINDS.includes(provider.kind) && provider.execution === 'browser-local';
  }

  function cloneHistory(history) {
    return history.map((item) => ({ role: item.role, content: item.content }));
  }

  function sourcePointers(result) {
    const sources = Array.isArray(result.sources) ? result.sources : [];
    const ids = [];
    for (const item of sources.slice(0, 12)) {
      const id = typeof item === 'string' ? item : item && item.id;
      if (typeof id === 'string' && /^[a-z0-9][a-z0-9_-]{0,63}$/.test(id) && !ids.includes(id)) ids.push(id);
    }
    return ids;
  }

  function presentationFrom(result) {
    const state = result && typeof result.state === 'object' ? result.state : {};
    const safeText = (value, limit) => typeof value === 'string' ? value.slice(0, limit) : '';
    const speakers = (Array.isArray(result.speakers) ? result.speakers : []).slice(0, 4)
      .filter((speaker) => speaker && typeof speaker === 'object')
      .map((speaker) => Object.freeze({
        // PR15's authored-label separation relies on a stable member ID to
        // show the label as UI metadata, never as a generated voice.
        id: typeof speaker.id === 'string' && /^[a-zA-Z0-9_-]{1,32}$/.test(speaker.id) ? speaker.id : '',
        name: safeText(speaker.name, 48), role: safeText(speaker.role, 100),
        text: safeText(speaker.text || speaker.content, MAX_REPLY)
      }));
    return Object.freeze({
      introduction: safeText(result.introduction, MAX_REPLY),
      facilitator: safeText(result.facilitator, MAX_REPLY),
      speakers: Object.freeze(speakers),
      topic: safeText(state.topic, 80),
      councilMode: safeText(state.councilMode, 20),
      supportedTopic: result.supportedTopic === true,
      uncertainty: safeText(result.uncertainty, 1500)
    });
  }

  function createSession(options) {
    const config = options && typeof options === 'object' ? options : {};
    const providers = Array.isArray(config.providers) ? config.providers : [];
    const registry = new Map();
    for (const provider of providers) {
      if (!validProvider(provider) || registry.has(provider.id)) {
        throw new TypeError('Invalid or duplicate browser-local provider definition');
      }
      registry.set(provider.id, provider);
    }
    const defaultProviderId = config.defaultProviderId || null;
    if (defaultProviderId !== null && !registry.has(defaultProviderId)) {
      throw new TypeError('Default provider must be explicitly registered');
    }
    const council = config.council && typeof config.council.respond === 'function' ? config.council : null;
    const outputGate = typeof config.outputGate === 'function' ? config.outputGate : null;
    const bundledCouncil = council && root.TherapyBotCouncil &&
      council.respond === root.TherapyBotCouncil.respond;
    // Capture the bundled resident check before an optional provider is invoked.
    // Same-realm JavaScript is NOT an authenticated sandbox.
    const residentRespond = root.TherapyBotEmbedded && typeof root.TherapyBotEmbedded.respond === 'function'
      ? root.TherapyBotEmbedded.respond : null;
    let history = [];
    let active = null;
    let sequence = 0;
    let disposed = false;

    function cancelActive() {
      sequence += 1;
      if (active) {
        active.controller.abort();
        active = null;
      }
    }

    function clear() {
      cancelActive();
      history = [];
    }

    function dispose() {
      clear();
      disposed = true;
    }

    async function turn(request) {
      if (disposed) return errorResult('unavailable', 'Session disposed.');
      if (active) return errorResult('busy', 'A conversation turn is already running.');
      const input = request && typeof request === 'object' ? request : {};
      const message = typeof input.message === 'string' ? input.message.trim().slice(0, MAX_MESSAGE) : '';
      if (!message) return errorResult('invalid', 'A non-empty message is required.');
      const mode = input.mode || 'direct';
      if (!MODES.includes(mode)) return errorResult('invalid', 'Unsupported conversation mode.');
      const providerId = input.providerId || defaultProviderId;
      const provider = registry.get(providerId);
      if (!provider) return errorResult('unavailable', 'Requested local engine is not installed; no cloud fallback exists.');
      // Provider/mode availability is checked after resident risk so an
      // unavailable optional model cannot suppress an independently caught cue.

      const controller = new AbortController();
      const ticket = ++sequence;
      active = { ticket, controller };
      let timer = null;
      let detach = null;
      const timeoutMs = Number.isInteger(input.timeoutMs) && input.timeoutMs >= 10 && input.timeoutMs <= 60000
        ? input.timeoutMs : 15000;
      let abortReason = 'canceled';
      if (input.signal && typeof input.signal.addEventListener === 'function') {
        const abortFromCaller = () => { abortReason = 'canceled'; controller.abort(); };
        input.signal.addEventListener('abort', abortFromCaller, { once: true });
        detach = () => input.signal.removeEventListener('abort', abortFromCaller);
        if (input.signal.aborted) controller.abort();
      }
      const abortTask = new Promise((resolve) => {
        controller.signal.addEventListener('abort', () => resolve({ aborted: true }), { once: true });
        if (controller.signal.aborted) resolve({ aborted: true });
      });
      function cancellableStep(action) {
        const task = Promise.resolve().then(action)
          .then((value) => ({ value }), () => ({ failed: true }));
        return Promise.race([task, abortTask]);
      }
      timer = setTimeout(() => { abortReason = 'timed_out'; controller.abort(); }, timeoutMs);
      try {
        const residentOutcome = await cancellableStep(() => residentRespond
          ? residentRespond({ message, history: cloneHistory(history) }) : null);
        if (residentOutcome.aborted || ticket !== sequence || controller.signal.aborted) {
          return errorResult(abortReason, 'Turn canceled or timed out. No transcript entry was retained.');
        }
        if (residentOutcome.failed || !validResidentResult(residentOutcome.value)) {
          return errorResult('unavailable', 'The resident safety check is unavailable or malformed; optional provider output was not displayed.');
        }
        const resident = residentOutcome.value;
        const residentRoute = resident.safety.route;
        const residentVeto = residentRoute !== 'normal';
        // Provider-supplied `kind` is self-attested, not a trust credential.
        // Only the identical bundled resident function is exempt from optional
        // output review. Other bounded providers are as untrusted as neural ones.
        const bundledResidentProvider = provider.kind === 'bounded-semantic' &&
          residentRespond && provider.respond === residentRespond;
        const needsOutputReview = !bundledResidentProvider;
        const needsCouncilReview = mode !== 'direct' && council && !bundledCouncil;
        if (!residentVeto) {
          if (provider.kind === 'in-browser-neural' && mode !== 'direct') {
            return errorResult('unavailable', 'This neural adapter does not support Council mode; no silent direct-chat substitution.');
          }
          if ((needsOutputReview || needsCouncilReview) && !outputGate) {
            return Object.freeze({
              status: 'ok', reply: OUTPUT_REVIEW_HOLD, providerId, kind: provider.kind,
              responseOrigin: 'output-review-hold', modeApplied: 'direct',
              safety: Object.freeze({ route: 'unknown', qualification: 'unvalidated' }),
              clinicalQualification: 'none', outputGateQualification: 'not-configured',
              providerNetworkVerified: false, providerStorageVerified: false,
              sourceClaimsVerified: false, sourceIds: Object.freeze([]),
              sourceRelation: 'background-reading-not-reply-verification',
              presentation: presentationFrom({ reply: OUTPUT_REVIEW_HOLD })
            });
          }
          if (mode !== 'direct' && !council) {
            return errorResult('unavailable', 'Inner Council adapter is not configured.');
          }
        }
        const outcome = residentVeto ? { value: resident } : await cancellableStep(() => {
          if (controller.signal.aborted) return { aborted: true };
          return provider.respond({
            message, history: cloneHistory(history), signal: controller.signal,
            depth: input.depth || 'balanced', style: input.style || 'direct'
          });
        });
        if (outcome.aborted || ticket !== sequence || controller.signal.aborted) {
          return errorResult(abortReason, 'Turn canceled or timed out. No transcript entry was retained.');
        }
        if (outcome.failed) return errorResult('error', 'The selected local engine failed. No transcript entry was retained.');
        const raw = outcome.value;
        if (!raw || typeof raw !== 'object' || typeof raw.reply !== 'string' || !raw.reply.trim()) {
          return errorResult('error', 'Local engine returned an invalid reply.');
        }
        // Resident non-normal routes veto provider before invocation. A neural
        // label is always unknown; a bounded provider's non-normal label can
        // raise caution but cannot inject prose into its safety response.
        const route = residentVeto ? residentRoute :
          provider.kind === 'in-browser-neural' ? 'unknown' :
          raw.safety && ROUTES.includes(raw.safety.route)
            ? raw.safety.route : 'unknown';
        let result = !residentVeto && provider.kind === 'bounded-semantic' && route !== 'normal'
          ? providerVeto(route) : raw;
        if (!residentVeto && needsOutputReview && result === raw) {
          const gateOutcome = await cancellableStep(() => outputGate({
            message, candidateReply: raw.reply, providerId, history: cloneHistory(history),
            signal: controller.signal
          }));
          if (gateOutcome.aborted || ticket !== sequence || controller.signal.aborted) {
            return errorResult(abortReason, 'Turn canceled while the candidate reply was being reviewed.');
          }
          if (gateOutcome.failed) return errorResult('error', 'The experimental output gate failed.');
          const verdict = gateOutcome.value;
          if (!verdict || verdict.allow !== true) {
            return errorResult('suppressed', 'The experimental output gate did not approve this response.');
          }
        }
        if (mode !== 'direct' && route === 'normal' && provider.kind === 'bounded-semantic') {
          const councilOutcome = await cancellableStep(() => council.respond({
            message, history: cloneHistory(history),
            mode, members: Array.isArray(input.members) ? input.members.map((m) => ({ ...m })) : [],
            baseResult: raw, signal: controller.signal
          }));
          if (councilOutcome.aborted || ticket !== sequence || controller.signal.aborted) {
            return errorResult(abortReason, 'Turn canceled while Council reflection was pending.');
          }
          if (councilOutcome.failed) return errorResult('error', 'Council reflection failed.');
          result = councilOutcome.value;
          if (!result || typeof result.reply !== 'string' || !result.reply.trim()) {
            return errorResult('error', 'Council returned an invalid reflection.');
          }
          // An injected Council is also a pluggable output source, even if it
          // receives a bundled resident result. Review its final prose too.
          if (needsCouncilReview) {
            const gateOutcome = await cancellableStep(() => outputGate({
              message, candidateReply: result.reply, providerId,
              history: cloneHistory(history), stage: 'council', signal: controller.signal
            }));
            if (gateOutcome.aborted || ticket !== sequence || controller.signal.aborted) {
              return errorResult(abortReason, 'Turn canceled while Council output was being reviewed.');
            }
            if (gateOutcome.failed || !gateOutcome.value || gateOutcome.value.allow !== true) {
              return errorResult('suppressed', 'The experimental output gate did not approve Council output.');
            }
          }
        }
        const reply = result.reply.slice(0, MAX_REPLY);
        const sources = sourcePointers(result);
        const presentation = presentationFrom(result);
        // Council abstention can strengthen a normal base result to unknown.
        // A malformed Council result must never silently inherit "normal".
        const finalRoute = result === raw ? route :
          result.safety && ['normal', 'concern', 'urgent_review', 'immediate', 'unknown'].includes(result.safety.route)
            ? result.safety.route : 'unknown';
        const responseOrigin = residentVeto ? 'resident-safety' :
          result !== raw && route !== 'normal' ? 'provider-warning-veto' :
          result !== raw ? 'inner-council' : 'selected-provider';
        const response = Object.freeze({
          status: 'ok', reply, providerId, kind: provider.kind,
          responseOrigin,
          modeApplied: presentation.councilMode || 'direct',
          safety: Object.freeze({ route: finalRoute, qualification: 'unvalidated' }),
          presentation,
          sourceIds: Object.freeze(sources),
          sourceRelation: 'background-reading-not-reply-verification',
          clinicalQualification: 'none',
          outputGateQualification: needsOutputReview || needsCouncilReview ? 'unspecified-experimental' : 'not-applicable',
          providerNetworkVerified: false,
          providerStorageVerified: false,
          sourceClaimsVerified: false
        });
        history.push({ role: 'user', content: message }, { role: 'assistant', content: reply });
        if (history.length > MAX_HISTORY) history = history.slice(-MAX_HISTORY);
        return response;
      } catch (_error) {
        return errorResult('error', 'The local conversation adapter failed without a transcript write.');
      } finally {
        if (timer !== null) clearTimeout(timer);
        if (detach) detach();
        if (active && active.ticket === ticket) active = null;
      }
    }

    return Object.freeze({
      turn, clear, dispose,
      snapshot: () => cloneHistory(history),
      registeredProviders: () => Array.from(registry.keys())
    });
  }

  root.TherapyBotConversationAdapter = Object.freeze({ version: '0.1-experimental', createSession });
})(typeof window !== 'undefined' ? window : globalThis);
