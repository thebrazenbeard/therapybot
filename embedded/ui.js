/* Local, repository-contained development interface. No network, telemetry or persistence. */
(() => {
  'use strict';

  const byId = (id) => document.getElementById(id);
  const messageField = byId('message');
  const log = byId('conversation-log');
  const sendButton = byId('send-message');
  const clearButton = byId('clear-chat');
  const forgetAllButton = byId('clear-all');
  const status = byId('engine-status');
  const feedback = byId('form-feedback');
  const conveneButton = byId('convene-council');
  const manageButton = byId('manage-council');
  const memberSetup = byId('council-setup');
  const memberList = byId('member-list');
  const memberName = byId('member-name');
  const memberRole = byId('member-role');
  const memberNotes = byId('member-notes');
  const saveMemberButton = byId('save-member');
  const cancelEditButton = byId('cancel-member-edit');
  const memberFeedback = byId('member-feedback');

  // The adapter owns volatile conversation context; this UI still owns the
  // user-defined Council roster. Neither layer uses browser persistence.
  const conversation = window.TherapyBotConversationAdapter && window.TherapyBotEmbedded &&
    typeof window.TherapyBotConversationAdapter.createSession === 'function' &&
    typeof window.TherapyBotEmbedded.respond === 'function'
    ? window.TherapyBotConversationAdapter.createSession({
      providers: [{
        id: 'embedded-semantic', kind: 'bounded-semantic',
        execution: 'browser-local', respond: window.TherapyBotEmbedded.respond
      }],
      defaultProviderId: 'embedded-semantic',
      council: window.TherapyBotCouncil
    }) : null;
  let generation = 0;
  let sending = false;
  let members = [];
  let nextMemberId = 1;
  let editingMemberId = null;
  let councilSelected = false;
  // Keep a pre-reflow scroll snapshot. Scroll notifications can arrive after a
  // responsive layout change, and should not be mistaken for reader intent.
  let followingLatest = true;
  let stableTop = log.scrollTop;
  let stableHeight = log.scrollHeight;
  let stableViewport = log.clientHeight;
  let readingAnchor = null;
  let reflowInProgress = false;
  const bottomGap = () => log.scrollHeight - log.clientHeight - log.scrollTop;
  const snapshotScroll = () => {
    stableTop = log.scrollTop;
    stableHeight = log.scrollHeight;
    stableViewport = log.clientHeight;
  };
  const captureReadingAnchor = (anticipatedTop = log.scrollTop) => {
    // A wheel input can be immediately followed by resize before the browser
    // dispatches its scroll event. Project the selected message at that offset.
    const viewportTop = log.getBoundingClientRect().top + anticipatedTop - log.scrollTop;
    readingAnchor = null;
    for (const element of log.children) {
      const rect = element.getBoundingClientRect();
      if (rect.bottom > viewportTop + 4) {
        readingAnchor = { element, offset: rect.top - viewportTop };
        break;
      }
    }
  };
  const restoreReadingAnchor = (anchor) => {
    if (!anchor || !anchor.element.isConnected) return;
    const displacement = anchor.element.getBoundingClientRect().top -
      log.getBoundingClientRect().top - anchor.offset;
    if (Math.abs(displacement) > 1) log.scrollTop += displacement;
  };
  log.addEventListener('scroll', () => {
    if (reflowInProgress) return;
    if (log.scrollHeight !== stableHeight || log.clientHeight !== stableViewport) return;
    followingLatest = bottomGap() <= 40;
    stableTop = log.scrollTop;
    if (followingLatest) readingAnchor = null;
    else captureReadingAnchor();
  });
  // Input can precede its scroll event. Record upward reader intent synchronously
  // so a resize in the same frame cannot drag the reader to the newest reply.
  log.addEventListener('wheel', (event) => {
    if (event.deltaY < 0) {
      followingLatest = false;
      const units = event.deltaMode === 1 ? 16 : event.deltaMode === 2 ? log.clientHeight : 1;
      const anticipatedTop = Math.max(0, Math.min(log.scrollHeight - log.clientHeight,
        log.scrollTop + event.deltaY * units));
      captureReadingAnchor(anticipatedTop);
    }
  }, { passive: true });
  log.addEventListener('keydown', (event) => {
    if (['ArrowUp', 'PageUp', 'Home'].includes(event.key)) followingLatest = false;
  });
  let touchStartY = null;
  log.addEventListener('touchstart', (event) => {
    touchStartY = event.touches[0]?.clientY ?? null;
  }, { passive: true });
  log.addEventListener('touchmove', (event) => {
    if (touchStartY !== null && event.touches[0]?.clientY > touchStartY + 6) followingLatest = false;
  }, { passive: true });
  window.addEventListener('resize', () => {
    reflowInProgress = true;
    const finishReflow = () => window.requestAnimationFrame(() => {
      snapshotScroll();
      reflowInProgress = false;
    });
    // Direct scrollTo(0) can run just before resize, without a dispatched
    // scroll event. Compare the actual position against our pre-reflow anchor.
    const movedUp = bottomGap() > 40 &&
      (log.scrollTop < 40 || log.scrollTop < stableTop - 40);
    if (!followingLatest || movedUp) {
      followingLatest = false;
      // When a narrower layout has more text, widening can clamp the scroll
      // offset to its new maximum. Restore the visible message, not the raw offset.
      if (movedUp) {
        if (log.scrollTop < 40) readingAnchor = null;
        else captureReadingAnchor();
      }
      const anchor = readingAnchor;
      snapshotScroll();
      window.requestAnimationFrame(() => {
        if (!followingLatest) restoreReadingAnchor(anchor);
        snapshotScroll();
        finishReflow();
      });
      return;
    }
    window.requestAnimationFrame(() => {
      if (followingLatest && !(bottomGap() > 40 &&
        (log.scrollTop < 40 || log.scrollTop < stableTop - 40))) {
        log.scrollTo({ top: log.scrollHeight, behavior: 'instant' });
      }
      snapshotScroll();
      finishReflow();
    });
  });

  const make = (tag, className, content) => {
    const el = document.createElement(tag);
    if (className) el.className = className;
    if (content !== undefined) el.textContent = String(content);
    return el;
  };

  function engineAvailable() {
    return Boolean(conversation);
  }

  function councilAvailable() {
    return Boolean(window.TherapyBotCouncil && typeof window.TherapyBotCouncil.respond === 'function');
  }

  function updateAvailability() {
    const available = engineAvailable();
    status.textContent = available ? 'Rules only · no neural model' : 'Rules engine unavailable';
    status.classList.toggle('error', !available);
    sendButton.disabled = sending || !available;
    if (!available) setFeedback('The bundled rules module or adapter did not load. Open the complete embedded/ folder to try this rules-only experiment. No neural model is included.', true);
  }

  function setFeedback(text, error = false) {
    feedback.textContent = text;
    feedback.classList.toggle('error', error);
  }

  function setMemberFeedback(text, error = false) {
    memberFeedback.textContent = text;
    memberFeedback.classList.toggle('error', error);
  }

  function updateCouncilControls() {
    byId('council-count').textContent = members.length
      ? members.length + (members.length === 1 ? ' member' : ' members') + ' · unsaved'
      : 'No members defined';
    conveneButton.textContent = councilSelected ? 'Return to direct chat' : 'Convene';
    conveneButton.setAttribute('aria-pressed', councilSelected ? 'true' : 'false');
    messageField.placeholder = councilSelected
      ? 'What would you like your Council to consider?'
      : 'What would you like to untangle?';
  }

  function openCouncilSetup(open) {
    memberSetup.hidden = !open;
    manageButton.setAttribute('aria-expanded', open ? 'true' : 'false');
    if (open) memberName.focus();
  }

  function resetMemberEditor() {
    editingMemberId = null;
    memberName.value = '';
    memberRole.value = '';
    memberNotes.value = '';
    saveMemberButton.textContent = 'Add member';
    cancelEditButton.hidden = true;
  }

  function renderMembers() {
    memberList.replaceChildren();
    for (const member of members) {
      const item = make('li', 'member-card');
      const copy = make('div', 'member-copy');
      copy.append(make('strong', '', member.name), make('span', '', member.role));
      if (member.notes) copy.append(make('p', '', member.notes));
      const actions = make('div', 'member-card-actions');
      const edit = make('button', '', 'Edit');
      edit.type = 'button';
      edit.setAttribute('aria-label', 'Edit ' + member.name);
      edit.addEventListener('click', () => {
        editingMemberId = member.id;
        memberName.value = member.name;
        memberRole.value = member.role;
        memberNotes.value = member.notes || '';
        saveMemberButton.textContent = 'Save changes';
        cancelEditButton.hidden = false;
        openCouncilSetup(true);
        setMemberFeedback('Editing ' + member.name + '.');
      });
      const remove = make('button', '', 'Remove');
      remove.type = 'button';
      remove.setAttribute('aria-label', 'Remove ' + member.name);
      remove.addEventListener('click', () => {
        const removedPosition = members.findIndex((candidate) => candidate.id === member.id);
        members = members.filter((candidate) => candidate.id !== member.id);
        if (editingMemberId === member.id) resetMemberEditor();
        if (!members.length) councilSelected = false;
        renderMembers();
        updateCouncilControls();
        // The focused Remove button no longer exists after rerendering. Move
        // focus to the next member's Edit control, or back to Manage members.
        const editActions = memberList.querySelectorAll('.member-card-actions button:first-child');
        const nextEditAction = editActions[Math.min(removedPosition, editActions.length - 1)];
        (nextEditAction || manageButton).focus();
        setMemberFeedback(member.name + ' removed from this tab. This does not erase conversation messages.');
      });
      actions.append(edit, remove);
      item.append(copy, actions);
      memberList.append(item);
    }
  }

  // Council details have no native form submission. If JavaScript fails to
  // initialize, the button is inert and member text cannot enter a URL/body.
  saveMemberButton.addEventListener('click', () => {
    const name = memberName.value.trim();
    const role = memberRole.value.trim();
    const notes = memberNotes.value.trim();
    if (!name || !role) return setMemberFeedback('Choose both a member name and a role.', true);
    if (!/^[\p{L}\p{N}][\p{L}\p{N} .,'’_-]*$/u.test(name)) {
      return setMemberFeedback('Member names can contain letters, numbers, spaces, hyphens, underscores and simple punctuation.', true);
    }
    if (members.some((member) => member.name.toLocaleLowerCase() === name.toLocaleLowerCase() && member.id !== editingMemberId)) {
      return setMemberFeedback('That name is already in your Council. Choose a distinct name.', true);
    }
    if (editingMemberId) {
      members = members.map((member) => member.id === editingMemberId ? { id: member.id, name, role, notes } : member);
      setMemberFeedback(name + ' updated for this tab.');
    } else {
      if (members.length >= 32) return setMemberFeedback('This experiment supports at most 32 members in one tab.', true);
      members.push({ id: 'member-' + nextMemberId++, name, role, notes });
      setMemberFeedback(name + ' added to your Council in this tab.');
    }
    resetMemberEditor();
    renderMembers();
    updateCouncilControls();
    memberName.focus();
  });
  cancelEditButton.addEventListener('click', () => {
    resetMemberEditor();
    setMemberFeedback('Edit cancelled.');
    memberName.focus();
  });
  manageButton.addEventListener('click', () => openCouncilSetup(memberSetup.hidden));
  conveneButton.addEventListener('click', () => {
    if (!councilAvailable()) {
      setFeedback('The bundled Council module did not load. Keep the complete embedded/ folder together.', true);
      return;
    }
    if (!members.length && !councilSelected) {
      openCouncilSetup(true);
      setMemberFeedback('Add at least one perspective before convening your Council.');
      return;
    }
    councilSelected = !councilSelected;
    if (councilSelected) openCouncilSetup(false);
    updateCouncilControls();
    setFeedback(councilSelected
      ? 'Council selected. Your next message will invite your user-defined perspectives; this is not clinical assessment.'
      : 'Direct conversation selected.');
    messageField.focus();
  });

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
    const speakers = !isUser && Array.isArray(result?.speakers) ? result.speakers : [];
    const label = make('span', 'message-label', isUser ? 'You' : speakers.length ? 'Inner Council · rules only' : 'TherapyBot · rules only');
    article.append(label);
    if (speakers.length) {
      if (typeof result?.introduction === 'string' && result.introduction.trim()) {
        article.append(make('div', 'message-content', result.introduction));
      }
      const group = make('div', 'council-speakers');
      for (const speaker of speakers.slice(0, 40)) {
        if (!speaker || typeof speaker !== 'object') continue;
        const card = make('div', 'council-speaker');
        card.append(make('strong', 'council-speaker-name', speaker.name || 'Unnamed perspective'));
        // Display user-defined names as user-owned metadata, never as the
        // generated speaker's identity or words. textContent prevents markup.
        const profile = members.find((member) => member.id === speaker.id);
        if (profile) card.append(make('span', 'council-speaker-user-label', 'Your label: ' + profile.name));
        if (speaker.role) card.append(make('span', 'council-speaker-role', speaker.role));
        card.append(make('div', 'council-speaker-text', speaker.text || speaker.content || ''));
        group.append(card);
      }
      if (group.childElementCount) article.append(group);
      if (typeof result?.facilitator === 'string' && result.facilitator.trim()) {
        const summary = make('div', 'council-facilitator');
        summary.append(make('strong', '', 'Facilitator · experimental'), make('p', '', result.facilitator));
        article.append(summary);
      }
    } else {
      article.append(make('div', 'message-content', content));
    }

    if (result && !isUser) {
      const topic = typeof result.state?.topic === 'string' ? result.state.topic : null;
      const route = typeof result.safety?.route === 'string' ? result.safety.route : null;
      const parts = ['Rules-only response · not clinically validated'];
      if (topic) parts.push('Topic: ' + topic);
      if (result.supportedTopic !== true && (!route || route === 'unknown' || route === 'normal')) parts.push('Unsupported topic');
      if (route && route !== 'normal') {
        parts.push('Safety route: ' + route + ' (unvalidated)');
        article.classList.add('message--warning');
      }
      article.append(make('div', 'message-meta', parts.join(' · ')));

      if (Array.isArray(result.sources) && result.sources.length) {
        const citations = make('div', 'message-sources');
        citations.setAttribute('aria-label', 'Related reading, not verification of this response');
        citations.append(make('span', 'source-qualifier', 'Related reading · not verification of this reply'));
        for (const source of result.sources.slice(0, 5)) {
          const anchor = sourceAnchor(source);
          if (anchor) citations.append(anchor);
        }
        if (citations.querySelector('a')) article.append(citations);
      }
    }
    log.append(article);
    log.scrollTo({ top: log.scrollHeight, behavior: 'instant' });
    followingLatest = true;
    readingAnchor = null;
    snapshotScroll();
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
    if (conversation) conversation.clear();
    log.replaceChildren();
    welcomeBack();
    messageField.value = '';
    setFeedback('Conversation cleared. Your unsaved Council member definitions remain in this tab until refresh.');
    messageField.focus();
  }

  function requestedMode(message) {
    if (/^council\s*:/i.test(message)) return 'council';
    if (/^solo\s+[^:\n]{1,64}\s*:/i.test(message)) return 'solo';
    if (/^integrate\s*:/i.test(message)) return 'integration';
    if (/^containment\s*:/i.test(message)) return 'containment';
    return councilSelected ? 'council' : 'direct';
  }

  function presentationForUi(result) {
    const view = result.presentation || {};
    const register = Array.isArray(window.TherapyBotEmbeddedCatalog) ? window.TherapyBotEmbeddedCatalog : [];
    const sources = (result.sourceIds || []).map((id) => register.find((record) => record.id === id))
      .filter(Boolean).map((record) => ({ id: record.id, title: record.title, url: record.url }));
    return {
      reply: result.reply,
      speakers: view.speakers || [],
      introduction: view.introduction || '',
      facilitator: view.facilitator || '',
      state: { topic: view.topic || null, councilMode: view.councilMode || null },
      supportedTopic: view.supportedTopic === true,
      safety: result.safety,
      sources
    };
  }

  function forgetAll() {
    if (!window.confirm('Forget this conversation and all Inner Council members in this tab?')) return;
    clearChat();
    members = [];
    nextMemberId = 1;
    councilSelected = false;
    resetMemberEditor();
    renderMembers();
    updateCouncilControls();
    openCouncilSetup(false);
    setMemberFeedback('Council roster forgotten.');
    setFeedback('Conversation and Council members forgotten from this tab.');
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
    setFeedback('Matching this message against the bundled topics…');
    appendMessage('user', message);
    messageField.value = '';

    try {
      const result = await conversation.turn({
        message,
        mode: requestedMode(message),
        members: members.map((member) => ({ ...member })),
        style: byId('style').value,
        depth: byId('depth').value,
      });
      if (epoch !== generation) return;
      if (!result || result.status !== 'ok' || typeof result.reply !== 'string' || result.providerId !== 'embedded-semantic') {
        throw new Error(result?.reason || 'Unexpected local conversation response format.');
      }
      const shown = presentationForUi(result);
      appendMessage('assistant', shown.reply, shown);
      const councilMode = shown.state.councilMode;
      if (councilMode === 'containment') {
        councilSelected = false;
        updateCouncilControls();
      }
      // Safety labels are unvalidated lexical cues, not an assessment. Still,
      // a flagged danger must never get a dismissive "try another topic" footer
      // merely because its text lacks a matching ordinary topic.
      const safetyRoute = shown.safety && shown.safety.route;
      setFeedback(safetyRoute === 'urgent_review' || safetyRoute === 'immediate'
        ? 'An unvalidated safety rule flagged possible danger. If someone is in immediate danger, contact local emergency services. In the U.S., call or text 988 for crisis support.'
        : safetyRoute === 'concern'
          ? 'An unvalidated rule flagged a safety concern; this is not a risk assessment. If danger is immediate, contact local emergency services.'
          : safetyRoute === 'unknown'
            ? "Safety interpretation unavailable. This rules-only build can't answer this topic reliably; do not treat this reply as assessed. Try a suggested topic; neural chat isn't installed here."
            : councilMode
              ? 'Experimental ' + councilMode + ' reflection · these are user-authored perspectives, not diagnoses.'
              : shown.supportedTopic
                ? 'Rules-only topic response · source links are background reading, not proof of this reply.'
                : "No matching topic. This build can't answer open-ended questions. Try a suggested topic; neural chat isn't installed here.");
    } catch (error) {
      if (epoch === generation) {
        appendMessage('assistant', 'The bundled rules engine could not complete that reply. No remote service was contacted.');
        if (!messageField.value) messageField.value = message;
        setFeedback(error instanceof Error ? error.message : 'Embedded engine failed.', true);
      }
    } finally {
      sending = false;
      updateAvailability();
      if (document.activeElement === sendButton || document.activeElement === messageField) messageField.focus();
    }
  }

  // This composer is an inert group, not a native form. If scripts fail,
  // neither browser submit keys nor Send can serialize sensitive text.
  sendButton.addEventListener('click', sendMessage);
  clearButton.addEventListener('click', clearChat);
  forgetAllButton.addEventListener('click', forgetAll);
  messageField.addEventListener('keydown', (event) => {
    if (event.key === 'Enter' && (event.ctrlKey || event.metaKey)) {
      event.preventDefault();
      sendMessage(event);
    }
  });
  document.querySelectorAll('[data-suggestion]').forEach((button) => {
    button.addEventListener('click', () => {
      messageField.value = button.dataset.suggestion || '';
      messageField.focus();
    });
  });

  updateAvailability();
  updateCouncilControls();
})();
