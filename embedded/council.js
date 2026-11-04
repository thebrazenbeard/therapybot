/*
 * User-authored Inner Council: an explicitly simulated reflection tool.
 *
 * All perspectives come from the current caller's member list. The script
 * never discovers, diagnoses, stores, trains on, or uploads a person's parts.
 * Its output is deterministic prose, not neural inference or clinical advice.
 * Load after engine.js so the existing safety result can veto role simulation.
 */
(function (root) {
  'use strict';

  const MAX_MEMBERS = 32;
  const MAX_SPEAKERS = 4;
  const MAX_MESSAGE = 4000;
  const UNCERTAINTY = 'These are scripted reflections based only on user-defined roles, not evidence of independent minds, diagnoses, clinical judgments, or neural-model output.';
  const NO_MEMBERS = 'There is no Inner Council configured yet. You can create your own perspectives and decide what each represents; I will not assign parts to you.';

  function plain(value, limit) {
    if (typeof value !== 'string') return '';
    return value.slice(0, limit * 3).normalize('NFKC')
      .replace(/[\u0000-\u001f\u007f]/g, ' ')
      .replace(/[<>]/g, function (character) { return character === '<' ? '‹' : '›'; })
      .replace(/\s+/g, ' ').trim().slice(0, limit);
  }

  function normalizedMember(member) {
    if (!member || typeof member !== 'object' || Array.isArray(member)) return null;
    const id = plain(member.id, 32);
    const name = plain(member.name || member.displayName, 48);
    if (!name || !/^[\p{L}\p{N}][\p{L}\p{N} .,'’_-]*$/u.test(name)) return null;
    if (id && !/^[a-zA-Z0-9_-]{1,32}$/.test(id)) return null;
    return {
      id: id || name.toLowerCase().replace(/[^\p{L}\p{N}]+/gu, '-').slice(0, 32),
      name,
      role: plain(member.role, 100),
      notes: plain(member.notes, 200),
      focus: plain(member.focus, 160),
      question: plain(member.question, 160)
    };
  }

  function membersFrom(value) {
    if (!Array.isArray(value)) return [];
    const seenNames = new Set();
    const seenIds = new Set();
    const members = [];
    for (const valueMember of value.slice(0, MAX_MEMBERS)) {
      const member = normalizedMember(valueMember);
      if (!member) continue;
      const key = member.name.toLocaleLowerCase();
      if (seenNames.has(key) || seenIds.has(member.id)) continue;
      seenNames.add(key);
      seenIds.add(member.id);
      members.push(member);
    }
    return members;
  }

  function explicitCommand(message) {
    const input = message.trim();
    if (/^council\s*:/i.test(input)) return { mode: 'council', content: input.replace(/^council\s*:\s*/i, '') };
    if (/^integrate\s*:/i.test(input)) return { mode: 'integration', content: input.replace(/^integrate\s*:\s*/i, '') };
    if (/^containment\s*:/i.test(input)) return { mode: 'containment', content: input.replace(/^containment\s*:\s*/i, '') };
    const solo = input.match(/^solo\s+([^:\n]{1,64})\s*:\s*([\s\S]*)$/i);
    if (solo) return { mode: 'solo', memberName: solo[1].trim(), content: solo[2].trim() };
    return null;
  }

  function modeFrom(options, message) {
    const explicit = explicitCommand(message);
    if (explicit) return explicit;
    const modes = ['council', 'solo', 'integration', 'containment'];
    if (!modes.includes(options.mode)) return null;
    return {
      mode: options.mode,
      content: message,
      memberName: plain(options.memberName || options.memberId || options.selectedMember, 64)
    };
  }

  function safeBase(options, message) {
    const supplied = options.baseResult;
    // Never use a caller-supplied "normal" flag to override the resident
    // engine's independent check; future callers may not be the current UI.
    if (root.TherapyBotEmbedded && typeof root.TherapyBotEmbedded.respond === 'function') {
      const actual = root.TherapyBotEmbedded.respond({
        message,
        history: Array.isArray(options.history) ? options.history.slice(-20) : []
      });
      if (supplied !== undefined) {
        if (!supplied || typeof supplied !== 'object' || Array.isArray(supplied) ||
            typeof supplied.reply !== 'string' ||
            !supplied.safety || !['normal', 'concern', 'urgent_review'].includes(supplied.safety.route)) return null;
        if (supplied.safety.route !== 'normal') return supplied;
      }
      if (!actual || !actual.safety || actual.safety.route !== 'normal') return actual;
      return supplied || actual;
    }
    return null;
  }

  function unsafeRoster(members) {
    return members.some(function (member) {
      const value = [member.role, member.notes, member.focus, member.question].join(' ').toLowerCase();
      return /\b(?:should|must|need to|ought to|have to|will)\s+(?:hurt|kill|attack|shoot|stab|assault|abuse|punish)\b/.test(value) ||
        /\b(?:go|tell|urge)\s+(?:kill|hurt|attack|shoot|stab)\b/.test(value);
    });
  }

  function councilResult(base, mode, reply, speakers, facilitator, memberCount, introduction) {
    return {
      reply,
      introduction: introduction || '',
      facilitator,
      speakers,
      engine: 'embedded-semantic',
      supportedTopic: true,
      uncertainty: UNCERTAINTY,
      sources: [],
      state: {
        topic: 'inner-council',
        followup: false,
        councilMode: mode,
        availableMembers: memberCount
      },
      safety: { route: 'normal', coverage: 'unvalidated' }
    };
  }

  function baseOrFailClosed(base) {
    if (base && typeof base.reply === 'string' && base.safety &&
        ['normal', 'concern', 'urgent_review'].includes(base.safety.route)) return base;
    return {
      reply: 'I cannot verify the ordinary conversation and safety routing needed for an Inner Council session. Please use the standard conversation interface until the engine is available.',
      engine: 'embedded-semantic',
      supportedTopic: false,
      uncertainty: 'The required base safety result was unavailable or malformed.',
      sources: [],
      state: { topic: null, followup: false, councilMode: null },
      safety: { route: 'unknown', coverage: 'unvalidated' }
    };
  }

  function topicLine(content) {
    return content ? 'The question on the table is: “' + plain(content, 350) + '”' :
      'No question was supplied; this is a demonstration of the member perspectives you authored.';
  }

  function perspective(member, index) {
    const focus = member.focus || member.notes || member.role;
    const framings = [
      'What I keep coming back to: ',
      'What I do not want overlooked: ',
      'The concern I bring: ',
      'What matters from my perspective: '
    ];
    const clause = focus ? framings[index % framings.length] + focus +
      (/[.!?]$/.test(focus) ? '' : '.') :
      'I have no defined focus yet; you can revise my role.';
    const question = member.question ? 'I would ask: ' + member.question :
      'I would ask what this perspective changes about your options.';
    return { name: member.name, role: member.role || 'User-defined perspective', text: clause + ' ' + question };
  }

  function council(options, base, command, members) {
    if (!members.length) return councilResult(base, 'council', NO_MEMBERS, [], NO_MEMBERS, 0);
    const selection = Array.isArray(options.memberIds) ? options.memberIds.slice(0, MAX_MEMBERS) : [];
    const requested = selection.length ?
      members.filter(function (member) { return selection.some(function (id) { return id === member.id || id === member.name; }); }) : members;
    if (!requested.length) return councilResult(base, 'council',
      'None of the selected members exists in this Council. Select a configured member or edit the roster.',
      [], '', members.length);
    const speakers = requested.slice(0, MAX_SPEAKERS).map(perspective);
    const label = speakers.length < requested.length ?
      ' This turn includes the first ' + speakers.length + ' of ' + requested.length + ' selected perspectives.' : '';
    const intro = 'These are user-authored reflective lenses, not evidence of separate people or diagnoses. ' +
      topicLine(command.content) + label;
    const synthesis = speakers.length === 1 ?
      'Only one perspective is represented; this is not a round-table consensus.' :
      'These perspectives may emphasize different needs. I cannot settle the tension for you, and agreement should not be assumed. What does each perspective help you notice?';
    const transcript = speakers.map(function (speaker) {
      return speaker.name + ' (' + speaker.role + '): ' + speaker.text;
    }).join('\n\n');
    return councilResult(base, 'council', intro + '\n\n' + transcript + '\n\n' + synthesis,
      speakers, synthesis, members.length, intro);
  }

  function solo(base, command, members) {
    if (!members.length) return councilResult(base, 'solo', NO_MEMBERS, [], NO_MEMBERS, 0);
    const wanted = plain(command.memberName || '', 64).toLocaleLowerCase();
    const member = members.find(function (item) {
      return item.id.toLocaleLowerCase() === wanted || item.name.toLocaleLowerCase() === wanted;
    });
    if (!wanted || !member) {
      return councilResult(base, 'solo',
        'I cannot find that member in your configured Council. Choose one of your existing perspectives; I will not invent a new one.',
        [], '', members.length);
    }
    const speaker = perspective(member, 0);
    const intro = 'Speaking through the user-defined lens “' + member.name +
      '” as a reflection exercise, not as a separate being or diagnosis. ' + topicLine(command.content);
    const facilitator = 'What, if anything, rings true to you?';
    return councilResult(base, 'solo', intro + '\n\n' + speaker.name + ': ' + speaker.text +
      '\n\nWhat, if anything, rings true to you?', [speaker], facilitator, members.length, intro);
  }

  function integration(base, command, members) {
    if (!members.length) return councilResult(base, 'integration', NO_MEMBERS, [], NO_MEMBERS, 0);
    const labels = members.slice(0, MAX_SPEAKERS).map(function (member) {
      return member.name + ': ' + (member.focus || member.role || 'focus not specified');
    }).join('; ');
    const reply = 'Integration is a reflective summary, not a verdict. ' + topicLine(command.content) +
      '\n\nThe first configured perspectives emphasize: ' + labels +
      (members.length > MAX_SPEAKERS ? '. Additional perspectives are configured but not summarized in this short pass.' : '.') +
      '\n\nWhich concerns can coexist, where do they genuinely conflict, and what choice remains yours?';
    return councilResult(base, 'integration', reply, [], reply, members.length);
  }

  function respond(input) {
    const options = input && typeof input === 'object' && !Array.isArray(input) ? input : {};
    const message = plain(options.message, MAX_MESSAGE);
    const base = safeBase(options, message);
    const verified = baseOrFailClosed(base);
    // The ordinary engine's safety route is authoritative for this prototype.
    // It is known to be unvalidated and must never be bypassed by persona mode.
    if (verified.safety.route !== 'normal') return verified;
    const command = modeFrom(options, message);
    if (!command) return verified;
    const members = membersFrom(options.members);
    if (unsafeRoster(members)) {
      return {
        reply: 'At least one configured Council perspective contains a directive about harming or punishing someone. I will not perform that instruction as a voice. You can revise the member notes or return to direct conversation.',
        engine: 'embedded-semantic',
        supportedTopic: false,
        uncertainty: 'This is an unvalidated precaution on user-authored profile text, not an assessment of a person or their intentions.',
        sources: [],
        state: { topic: null, followup: false, councilMode: null },
        safety: { route: 'concern', coverage: 'unvalidated' }
      };
    }
    switch (command.mode) {
      case 'containment':
        return councilResult(verified, 'containment',
          'The Council is paused. I will return to ordinary conversation without assigning this experience to a role. You can decide whether to continue or stop here.',
          [], '', members.length);
      case 'solo':
        return solo(verified, command, members);
      case 'integration':
        return integration(verified, command, members);
      case 'council':
        return council(options, verified, command, members);
      default:
        return verified;
    }
  }

  root.TherapyBotCouncil = Object.freeze({ version: '0.1-experimental', respond });
})(window);
