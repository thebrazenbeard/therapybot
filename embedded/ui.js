/* Local, repository-contained development interface. No network, telemetry or persistence. */
(() => {
  'use strict';

  const byId = (id) => document.getElementById(id);
  const form = byId('conversation-form');
  const messageField = byId('message');
  const log = byId('conversation-log');
  const sendButton = byId('send-message');
  const clearButton = byId('clear-chat');
  const status = byId('engine-status');
  const feedback = byId('form-feedback');

  // Conversation context is intentionally a volatile JavaScript array.
  // No localStorage, sessionStorage, IndexedDB, cookies or API requests.
  let history = [];
  let generation = 0;
  let sending = false;

  const make = (tag, className, content) => {
    const el = document.createElement(tag);
    if (className) el.className = className;
    if (content !== undefined) el.textContent = String(content);
    return el;
  };

  function engineAvailable() {
    return Boolean(window.TherapyBotEmbedded && typeof window.TherapyBotEmbedded.respond === 'function');
  }

  function updateAvailability() {
    const available = engineAvailable();
    status.textContent = available ? 'Embedded semantic · ready' : 'Engine unavailable';
    status.classList.toggle('error', !available);
    sendButton.disabled = sending || !available;
    if (!available) setFeedback('Bundled engine.js was not loaded. Open the complete embedded/ folder to use this experiment.', true);
  }

  function setFeedback(text, error = false) {
    feedback.textContent = text;
    feedback.classList.toggle('error', error);
  }

  function sourceAnchor(source) {
    if (!source || typeof source !== 'object') return null;
    let url;
    try { url = new URL(String(source.url || '')); } catch { return null; }
    if (url.protocol !== 'https:') return null;
    const anchor = make('a', '', source.title || url.hostname);
    anchor.href = url.href;
    anchor.rel = 'noopener noreferrer';
    anchor.target = '_blank';
    return anchor;
  }

  function appendMessage(role, content, result = null) {
    const welcome = byId('welcome');
    if (welcome) welcome.remove();
    const isUser = role === 'user';
    const article = make('article', 'message ' + (isUser ? 'message--user' : 'message--assistant'));
    const label = make('span', 'message-label', isUser ? 'You' : 'TherapyBot · embedded');
    const text = make('div', 'message-content', content);
    article.append(label, text);

    if (result && !isUser) {
      const topic = typeof result.state?.topic === 'string' ? result.state.topic : null;
      const route = typeof result.safety?.route === 'string' ? result.safety.route : null;
      const parts = ['Experimental · not clinically validated'];
      if (topic) parts.push('Topic: ' + topic);
      if (route && route !== 'normal') {
        parts.push('Safety route: ' + route + ' (unvalidated)');
        article.classList.add('message--warning');
      }
      article.append(make('div', 'message-meta', parts.join(' · ')));

      if (Array.isArray(result.sources) && result.sources.length) {
        const citations = make('div', 'message-sources');
        citations.setAttribute('aria-label', 'Suggested source links');
        for (const source of result.sources.slice(0, 5)) {
          const anchor = sourceAnchor(source);
          if (anchor) citations.append(anchor);
        }
        if (citations.childElementCount) article.append(citations);
      }
    }
    log.append(article);
    log.scrollTop = log.scrollHeight;
  }

  function welcomeBack() {
    const container = make('div', 'welcome-panel');
    container.id = 'welcome';
    container.append(make('div', 'welcome-mark', '✳'));
    container.append(make('h3', '', 'A clean page.'));
    container.append(make('p', '', 'This in-memory conversation is cleared. You can start another thought whenever you like.'));
    log.append(container);
  }

  function clearChat() {
    generation += 1;
    history = [];
    log.replaceChildren();
    welcomeBack();
    messageField.value = '';
    setFeedback('Conversation cleared from this tab. Nothing was saved.');
    messageField.focus();
  }

  async function sendMessage(event) {
    event.preventDefault();
    if (sending) return;
    const message = messageField.value.trim();
    if (!message) return;
    if (!engineAvailable()) return updateAvailability();

    const epoch = generation;
    sending = true;
    sendButton.disabled = true;
    setFeedback('Thinking with the bundled semantic engine…');
    appendMessage('user', message);
    messageField.value = '';

    try {
      const result = await Promise.resolve(window.TherapyBotEmbedded.respond({
        message,
        history: history.slice(-10),
        style: byId('style').value,
        depth: byId('depth').value,
      }));
      if (epoch !== generation) return;
      if (!result || typeof result.reply !== 'string' || result.engine !== 'embedded-semantic') {
        throw new Error('Unexpected embedded-engine response format.');
      }
      appendMessage('assistant', result.reply, result);
      history.push({ role: 'user', content: message }, { role: 'assistant', content: result.reply });
      if (history.length > 12) history = history.slice(-12);
      setFeedback(result.supportedTopic ? 'Structured topic response · review the sources and limits.' : 'Limited topic coverage · do not rely on this as professional guidance.');
    } catch (error) {
      if (epoch === generation) {
        appendMessage('assistant', 'The bundled engine could not complete that reply. No remote service was contacted.');
        if (!messageField.value) messageField.value = message;
        setFeedback(error instanceof Error ? error.message : 'Embedded engine failed.', true);
      }
    } finally {
      sending = false;
      updateAvailability();
      messageField.focus();
    }
  }

  form.addEventListener('submit', sendMessage);
  // Button is intentionally not a native submit control. If the local script
  // fails to initialize, a browser must not put sensitive text into a file URL.
  sendButton.addEventListener('click', sendMessage);
  clearButton.addEventListener('click', clearChat);
  messageField.addEventListener('keydown', (event) => {
    if (event.key === 'Enter' && (event.ctrlKey || event.metaKey)) {
      event.preventDefault();
      form.requestSubmit();
    }
  });
  document.querySelectorAll('[data-suggestion]').forEach((button) => {
    button.addEventListener('click', () => {
      messageField.value = button.dataset.suggestion || '';
      messageField.focus();
    });
  });

  updateAvailability();
})();
