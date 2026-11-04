/* Working rules-only laboratory conversation. No model, network, or persistence. */
(function () {
  'use strict';
  const log = document.getElementById('conversation-log');
  const form = document.getElementById('composer');
  const field = document.getElementById('message');
  const sendButton = document.getElementById('send');
  const clearButton = document.getElementById('clear');
  const status = document.getElementById('status');
  let session = null;
  let epoch = 0;
  let busy = false;

  function append(role, message, warning) {
    const article = document.createElement('article');
    article.className = 'message ' + (role === 'You' ? 'user-message' : 'assistant-message');
    const heading = document.createElement('h3');
    heading.textContent = role;
    const paragraph = document.createElement('p');
    paragraph.textContent = message;
    article.append(heading, paragraph);
    if (warning) {
      const note = document.createElement('p');
      note.className = 'warning';
      note.textContent = warning;
      article.appendChild(note);
    }
    log.appendChild(article);
    log.scrollTop = log.scrollHeight;
  }

  function setBusy(next) {
    busy = next;
    sendButton.disabled = next || !session;
    sendButton.textContent = next ? 'Thinking…' : 'Send';
  }

  function createSession() {
    if (!window.TherapyBotEmbedded || !window.TherapyBotConversationAdapter) {
      status.textContent = 'The local engine assets are missing; this lab cannot run.';
      setBusy(false);
      return;
    }
    session = window.TherapyBotConversationAdapter.createSession({
      providers: [{
        id: 'embedded-semantic',
        kind: 'bounded-semantic',
        execution: 'browser-local',
        respond: window.TherapyBotEmbedded.respond
      }],
      defaultProviderId: 'embedded-semantic'
    });
    status.textContent = 'Ready · Rules-only local engine · No cloud or model downloads';
    setBusy(false);
  }

  function isExplicitDanger(message) {
    return [
      /\b(?:i(?:'m| am)|we(?:'re| are)|someone is)\s+(?:in\s+)?(?:immediate\s+)?danger\b/i,
      /\b(?:about to|going to|will|might|may)\s+(?:hurt|kill|end|harm)\s+(?:myself|ourselves|someone|them|him|her)\b/i,
      /\b(?:i(?:'m| am| feel)\s+suicidal|i\s+(?:want|plan|intend|might|may)\s+to\s+(?:kill|hurt|harm)\s+myself|i\s+(?:want|plan|intend|might|may)\s+to\s+end\s+my\s+life)\b/i,
      /\b(?:i(?:'m| am)\s+not safe|someone\s+is\s+(?:threatening|attacking)\s+me)\b/i,
      /\b(?:i(?:'ve| have)\s+(?:just\s+)?(?:taken|swallowed)\s+(?:a lot of\s+)?(?:pills|poison|medication))\b/i
    ].some(pattern => pattern.test(message));
  }

  function limitedResponse(message) {
    if (isExplicitDanger(message)) return 'This may be urgent, and I cannot assess your safety. If anyone could be harmed right now, please contact local emergency services immediately. In the U.S., call 911 for emergencies or 988 for crisis support. If you can, move away from immediate danger and contact a trusted person nearby.';
    if (/^(?:please\s+)?(?:stop|pause|stop (?:talking|replying)|leave me alone|enough)[.!?\s]*$/i.test(message)) {
      return 'Okay. I will stop here. I will not continue unless you send another message. You can clear this chat whenever you want.';
    }
    if (/\binner council\b/i.test(message)) {
      return 'The Inner Council is not available in this limited browser experiment. This page has one rules-based responder, not multiple independent perspectives.';
    }
    if (/\b(?:that(?:'s| is) not what i meant|you misunderstood|you(?:'re| are) not listening|not what i said|i did(?:n't| not) say that)\b/i.test(message)) {
      return 'I may have misunderstood. I have limited context tracking, so please tell me the part I got wrong in your own words.';
    }
    return null;
  }

  function reset() {
    epoch += 1;
    if (session) session.clear();
    log.replaceChildren();
    append('TherapyBot', 'Hello. I can try to help you untangle a thought or situation, but my replies come from a limited rules-based system. What is on your mind?');
    setBusy(false);
    field.focus();
  }

  form.addEventListener('submit', async function (event) {
    event.preventDefault();
    if (!session || busy) return;
    const message = field.value.trim();
    if (!message) return;
    field.value = '';
    append('You', message);
    const bounded = limitedResponse(message);
    if (bounded !== null) {
      append('TherapyBot', bounded);
      return;
    }
    setBusy(true);
    const current = epoch;
    try {
      const result = await session.turn({ message: message, mode: 'direct', timeoutMs: 15000 });
      if (current !== epoch) return;
      if (result && result.status === 'ok' && typeof result.reply === 'string') {
        const caution = result.safety && ['urgent_review', 'immediate', 'unknown'].includes(result.safety.route)
          ? 'This prototype cannot determine whether urgent help is needed. If someone is in immediate danger, call your local emergency number.'
          : '';
        append('TherapyBot', result.reply, caution);
      } else {
        append('TherapyBot', result && result.message ? result.message : 'I could not complete that turn. Please try again.');
      }
    } catch (_) {
      if (current === epoch) append('TherapyBot', 'An unexpected local error interrupted this turn.');
    } finally {
      if (current === epoch) setBusy(false);
    }
  });
  field.addEventListener('keydown', function (event) {
    if (event.key === 'Enter' && event.ctrlKey) {
      event.preventDefault();
      form.requestSubmit();
    }
  });
  clearButton.addEventListener('click', reset);
  clearButton.addEventListener('keydown', function (event) {
    if (event.key === 'Enter' || event.key === ' ') {
      event.preventDefault();
      reset();
    }
  });
  createSession();
  reset();
})();
