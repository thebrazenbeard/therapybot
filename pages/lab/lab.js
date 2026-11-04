/* Experimental local conversation: rules default, opt-in neural only after consent. */
(function () {
  'use strict';
  const get = id => document.getElementById(id);
  const log = get('conversation-log');
  const form = get('composer'), field = get('message'), sendButton = get('send');
  const clearButton = get('clear'), pauseButton = get('pause'), status = get('status');
  const consent = get('model-consent'), modelLoad = get('model-load');
  const modelCancel = get('model-cancel'), modelStatus = get('model-status');
  let session = null, busy = false, paused = false, ticket = 0;
  let transcript = [], acuteContext = false, modelAbort = null, modelLoading = false;

  function append(role, message, warning) {
    const item = document.createElement('article');
    item.className = 'message ' + (role === 'You' ? 'user-message' : 'assistant-message');
    const heading = document.createElement('h3'), paragraph = document.createElement('p');
    heading.textContent = role;
    paragraph.textContent = message;
    item.append(heading, paragraph);
    if (warning) {
      const note = document.createElement('p');
      note.className = 'warning';
      note.textContent = warning;
      item.appendChild(note);
    }
    log.appendChild(item);
    log.scrollTop = log.scrollHeight;
  }
  function remember(role, content) {
    transcript.push({ role, content });
    if (transcript.length > 24) transcript = transcript.slice(-24);
  }
  function say(message, warning) {
    append('TherapyBot', message, warning);
    remember('assistant', message);
  }
  function refresh() {
    field.disabled = paused;
    sendButton.disabled = !session || paused || busy;
    sendButton.textContent = busy ? 'Thinking…' : 'Send';
    pauseButton.textContent = paused ? 'Resume replies' : 'Pause replies';
    pauseButton.setAttribute('aria-pressed', String(paused));
    modelLoad.disabled = modelLoading || !consent.checked ||
      Boolean(window.TherapyBotNeural?.isLoaded());
    modelCancel.disabled = !modelAbort;
    consent.disabled = modelLoading || Boolean(window.TherapyBotNeural?.isLoaded());
    status.textContent = paused ? 'Replies paused. Resume explicitly to continue.' :
      window.TherapyBotNeural?.isLoaded() ? 'On-device neural mode · Experimental and unqualified' :
      'Rules-only local engine · No model loaded';
  }
  function reviewNeuralOutput({ candidateReply }) {
    // Local lexical rejection only; this is NOT a validated clinical safety filter.
    if (typeof candidateReply !== 'string' || !candidateReply.trim() || candidateReply.length > 2400) {
      return {allow:false};
    }
    const blocked = [
      /\b(?:kill|hurt|harm)\s+(?:yourself|someone else)\b/i,
      /\b(?:ignore|stop)\s+(?:all\s+|your\s+)?(?:medication|doctor|emergency services)\b/i,
      /\b(?:take|double|increase)\s+\d+(?:\.\d+)?\s*(?:mg|pills|tablets|grams)\b/i,
      /\b(?:you (?:definitely|certainly) have|i (?:diagnose|can diagnose) you)\b/i,
      /\b(?:don't tell anyone|keep this secret from)\b/i
    ];
    return {allow:!blocked.some(pattern=>pattern.test(candidateReply))};
  }
  function init() {
    if (!window.TherapyBotEmbedded || !window.TherapyBotConversationAdapter) {
      status.textContent = 'Missing browser runtime; cannot converse.';
      return;
    }
    session = window.TherapyBotConversationAdapter.createSession({
      providers: [{
        id: 'embedded-semantic', kind: 'bounded-semantic', execution: 'browser-local',
        respond: ({ message }) => window.TherapyBotEmbedded.respond({
          message, history: transcript.slice(0,-1).map(item => ({...item}))
        })
      },{
        id: 'experimental-neural', kind: 'in-browser-neural', execution: 'browser-local',
        respond: async () => ({reply:await window.TherapyBotNeural.respond(transcript)})
      }],
      defaultProviderId: 'embedded-semantic',
      outputGate: reviewNeuralOutput
    });
    refresh();
  }
  function reset() {
    ticket++;
    session?.clear();
    paused = false;
    transcript = [];
    acuteContext = false;
    log.replaceChildren();
    append('TherapyBot', 'Hello. This is a limited experiment; I can offer basic conversation, but not reliable therapy or emergency assessment. What is on your mind?');
    refresh();
    field.focus();
  }
  function pause() {
    ticket++;
    session?.clear();
    paused = true;
    say('Replies paused. A generation already running may finish in memory, but its reply will be discarded. Select Resume replies to continue.');
    refresh();
    pauseButton.focus();
  }
  function togglePause() {
    if (!paused) { pause(); return; }
    paused = false;
    refresh();
    field.focus();
  }
  function fictional(text) {
    return /\b(?:in (?:my|a) (?:novel|story|script)|a fictional|the fictional|my character|a character|the character|in this roleplay|hypothetically|hypothetical example|for a play)\b/i.test(text);
  }
  function immediateDanger(text) {
    return [
      /\b(?:i(?:'m| am)|we(?:'re| are)|someone is)\s+(?:in\s+)?(?:immediate\s+)?danger\b/i,
      /\b(?:about to|going to|will|might|may|want to|plan to)\s+(?:hurt|kill|end|harm)\s+(?:myself|ourselves|someone|them|him|her)\b/i,
      /\b(?:i(?:'m| am| feel)\s+suicidal|i\s+(?:want|plan|intend|might|may)\s+to\s+(?:kill|hurt|harm)\s+myself|i\s+(?:want|plan|intend|might|may)\s+to\s+end\s+my\s+life)\b/i,
      /\b(?:i(?:'m| am)\s+not safe|someone\s+is\s+(?:threatening|attacking)\s+me)\b/i,
      /\b(?:took|taken|swallowed|ingested|overdosed|poisoned|drank)\b.{0,70}\b(?:pills|poison|medication|substance|chemicals|overdose)\b/i,
      /\b(?:not breathing|unresponsive|not responding|isn't responding|is not responding|won't wake|cannot wake|can't wake|unconscious|severe bleeding|bleeding heavily)\b/i,
      /\b(?:can't|cannot|couldn't|won't|will not)\s+(?:promise|guarantee|keep|say)\b.{0,55}\b(?:safe|safety)\b/i
    ].some(pattern => pattern.test(text));
  }
  function continuation(text) {
    return /\b(?:do it|doing it|right now|tonight|can't stop|cannot stop|don't have time|can't wait|no more time|ready now|already did|it's happening|it is happening)\b/i.test(text);
  }
  function isStop(text) {
    return /^(?:please\s+)?(?:stop(?:\s+(?:now|talking|replying|asking|asking questions))?|pause(?:\s+(?:now|this|replies))?|leave me alone|enough|i need (?:to stop(?: now)?|a break)|let(?:'s| us) stop|do not reply|don't reply)[.!?\s]*$/i.test(text.trim()) ||
      /^(?:can|could|would) (?:we|you) (?:please )?(?:stop|pause)(?: now| replying| asking)?[.!?\s]*$/i.test(text.trim());
  }
  function localRoute(text) {
    if (isStop(text)) return { kind:'pause' };
    if (/\b(?:i(?:'m| am) safe now|not in danger|this (?:is|was) hypothetical|this (?:is|was) fictional)\b/i.test(text)) acuteContext=false;
    const realWorldQualifier = /\b(?:but (?:i|we|my|someone)|in real life|this is real|actually (?:i|we|my|someone)|outside (?:the|my) story|happening right now)\b/i.test(text);
    if (fictional(text) && !realWorldQualifier) {
      return { reply:'I understand this as fictional or hypothetical. I cannot infer the real-world safety of anyone from a quote. We can discuss the scene, but this is a limited rules-based experiment.' };
    }
    if (immediateDanger(text) || (acuteContext && continuation(text))) {
      acuteContext = true;
      return { reply:'This could be urgent, and I cannot assess how safe anyone is. If someone might be harmed right now, contact local emergency services immediately. In the U.S., call 911 for emergencies or 988 for crisis support. If possible, move away from immediate danger and get help from a person nearby.' };
    }
    if (/\b(?:privacy|data storage|my conversation|save my (?:data|chat)|store my (?:data|chat)|download consent|what do you store|where is my data)\b/i.test(text)) {
      return {reply:'This page keeps conversation text in memory while open. It does not send messages to a model API or intentionally save transcripts. Browser caches may retain static files. A model download occurs only after consent; that request contacts Hugging Face. Clear erases this page’s in-memory conversation.'};
    }
    if (/\binner council\b/i.test(text)) {
      return {reply:'The Inner Council is not implemented in this browser experiment. This page cannot provide genuinely independent conversational perspectives.'};
    }
    if (/\b(?:that(?:'s| is) not what i meant|you misunderstood|you(?:'re| are) not listening|not what i said|i did(?:n't| not) say that)\b/i.test(text)) {
      return {reply:'I may have misunderstood. I can retain the conversation text in this open page, but this small engine may not interpret corrections. What should I understand differently?'};
    }
    return null;
  }
  form.addEventListener('submit', async event => {
    event.preventDefault();
    if (!session || paused || busy) return;
    const message = field.value.trim();
    if (!message) return;
    field.value = '';
    append('You', message);
    remember('user', message);
    const route = localRoute(message);
    if (route?.kind === 'pause') {
      pause();
      return;
    }
    if (route?.reply) {
      say(route.reply);
      return;
    }
    busy = true;
    const turn = ++ticket;
    refresh();
    try {
      const neuralMode = Boolean(window.TherapyBotNeural?.isLoaded());
      const result = await session.turn({
        message, mode:'direct',
        providerId:neuralMode ? 'experimental-neural' : 'embedded-semantic',
        timeoutMs:neuralMode ? 60000 : 15000
      });
      if (turn !== ticket || paused) return;
      if (result?.status === 'ok' && typeof result.reply === 'string') {
        const note = neuralMode && result.responseOrigin === 'selected-provider'
          ? 'Experimental 135M model output, permitted by a limited lexical filter—not clinical validation.'
          : '';
        say(result.reply,note);
      } else if (neuralMode && result?.status === 'suppressed') {
        say('The experimental output filter suppressed this unqualified model reply.');
      } else {
        say(result?.message || 'A local error interrupted this turn.');
      }
    } catch (error) {
      if (turn === ticket && !paused) say('Local inference failed. ' +
        (error instanceof Error ? error.message : String(error)));
    } finally {
      busy = false;
      refresh();
    }
  });
  clearButton.addEventListener('click', reset);
  pauseButton.addEventListener('click', togglePause);
  for (const [button, action] of [[clearButton,reset],[pauseButton,togglePause]]) {
    button.addEventListener('keydown', event => {
      if (event.key === 'Enter' || event.key === ' ') {
        event.preventDefault();
        action();
      }
    });
  }
  field.addEventListener('keydown', event => {
    if (event.key === 'Enter' && event.ctrlKey) {
      event.preventDefault();
      form.requestSubmit();
    }
  });
  consent.addEventListener('change',refresh);
  modelLoad.addEventListener('click', async () => {
    if (!consent.checked || modelLoading || window.TherapyBotNeural?.isLoaded()) return;
    if (!window.TherapyBotNeural) {
      modelStatus.textContent = 'Neural module unavailable; rules-only conversation remains active.';
      return;
    }
    modelAbort = new AbortController();
    modelLoading = true;
    refresh();
    try {
      await window.TherapyBotNeural.load({
        signal:modelAbort.signal,
        onStatus: text => {modelStatus.textContent=text;}
      });
    } catch(error) {
      modelStatus.textContent = 'Model NOT LOADED: ' + (error instanceof Error ? error.message : String(error));
    } finally {
      modelAbort = null;
      modelLoading = false;
      refresh();
    }
  });
  modelCancel.addEventListener('click', () => {
    modelAbort?.abort();
    modelStatus.textContent = 'Cancel requested; already-started WASM load might continue.';
  });
  init();
  reset();
})();
