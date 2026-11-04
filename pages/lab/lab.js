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
    setBusy(true);
    const current = epoch;
    try {
      const result = await session.turn({ message: message, mode: 'direct', timeoutMs: 15000 });
      if (current !== epoch) return;
      if (result && result.status === 'ok' && typeof result.reply === 'string') {
        append('TherapyBot', result.reply, 'Unvalidated safety route: ' + result.safety.route + '. This is not clinical advice.');
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
  createSession();
  reset();
})();
