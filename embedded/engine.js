/*
 * Experimental browser-native conversational model, shipped as repository code.
 * It models topic, intent, context and conversational state; it is NOT an LLM,
 * diagnosis tool, validated danger classifier, or source-grounded treatment.
 * No fetch, telemetry, storage, runtime packages or external inference service.
 */
(function (root) {
  'use strict';

  const TOPICS = Object.freeze([
    {
      key: 'work',
      words: ['work', 'job', 'boss', 'employer', 'manager', 'fired', 'termination', 'reimbursement', 'expenses', 'expense', 'paycheck', 'salary', 'wages', 'coworker', 'supervisor', 'training'],
      phrases: ['at work', 'my job', 'my boss', 'lose my job', 'get fired', 'use my own money', 'pay out of pocket'],
      openings: [
        'Workplace demands can involve real financial and power constraints. I will not assume refusing is consequence-free.',
        'There may be a practical workplace problem here, not merely a feeling to reframe.'
      ],
      questions: [
        'What specifically has been required, and what alternative—if any—has actually been offered?',
        'Which consequence are you trying to avoid, and what part of this decision is under your control?',
        'Would it help to separate what has been documented from what is still being assumed?'
      ],
      sources: ['who-world-mental-health-2022']
    },
    {
      key: 'boundaries',
      words: ['boundary', 'boundaries', 'consent', 'pressure', 'refuse', 'limits', 'limit', 'respect', 'coercion', 'autonomy', 'obligation'],
      phrases: ['say no', 'saying no', 'set a boundary', 'setting boundaries', 'crossed a line', 'personal space'],
      openings: [
        'A boundary concerns a choice or limit you can act on; it cannot guarantee another person will agree.',
        'I can examine the difference between protecting a limit and avoiding a difficult choice without assigning either label prematurely.'
      ],
      questions: [
        'What behavior or request is crossing your limit?',
        'What consequence would make that boundary difficult to hold?',
        'What would an enforceable boundary look like within your actual constraints?'
      ],
      sources: ['cdc-social-connectedness']
    },
    {
      key: 'relationships',
      words: ['wife', 'husband', 'partner', 'marriage', 'friend', 'family', 'mother', 'father', 'brother', 'sister', 'relationship', 'relationships', 'trust', 'betrayal', 'lonely'],
      phrases: ['my partner', 'my family', 'my wife', 'my husband', 'someone i love', 'feel betrayed'],
      openings: [
        'Relationships can carry competing needs; I will not assume either person is automatically right or wrong.',
        'It may help to separate what was said, what happened, and what each person expects next.'
      ],
      questions: [
        'What did the other person actually do, and which part mattered most to you?',
        'Are you trying to understand their behavior, decide what to say, or work out your own limits?',
        'What would respectful communication look like here without requiring you to ignore your own needs?'
      ],
      sources: ['cdc-social-connectedness']
    },
    {
      key: 'anger',
      words: ['angry', 'anger', 'furious', 'rage', 'resentment', 'frustrated', 'frustration', 'irritated', 'enraged', 'mad', 'vent'],
      phrases: ['pissed off', 'need to vent', 'so angry', 'fed up'],
      openings: [
        'Anger does not, by itself, establish a desire to hurt anyone. I can listen without jumping to that conclusion.',
        'I can take the frustration seriously without deciding in advance what it means.'
      ],
      questions: [
        'Which part of what happened made you angriest?',
        'Do you want to vent, understand the trigger, or work toward a practical response?',
        'What would you want to be different when this situation comes up again?'
      ],
      sources: ['nimh-psychotherapies']
    },
    {
      key: 'isolation',
      words: ['alone', 'isolated', 'isolation', 'loneliness', 'lonely', 'solitude', 'belong', 'connected', 'connection', 'rejected', 'excluded'],
      phrases: ['left out', 'no one understands', 'nobody understands', 'by myself'],
      openings: [
        'Being alone and feeling lonely are not always the same experience. I will not assume that solitude is a problem.',
        'Connection matters, but so do safety, choice and the quality of the relationships available.'
      ],
      questions: [
        'Is the difficult part being alone, feeling misunderstood, or having too little choice about connection?',
        'What kind of contact feels useful rather than draining?',
        'What would you want more of, without giving up the space you need?'
      ],
      sources: ['cdc-social-connectedness']
    },
    {
      key: 'trauma',
      words: ['trauma', 'abuse', 'abused', 'neglect', 'trigger', 'flashback', 'unsafe', 'childhood', 'survivor', 'dissociation', 'traumatic'],
      phrases: ['growing up', 'when i was a child', 'in my childhood', 'past abuse'],
      openings: [
        'I can take what you describe seriously without turning it into a diagnosis or deciding what it must mean.',
        'Past experiences can matter, but I do not want to force every current difficulty into a trauma explanation.'
      ],
      questions: [
        'Would you rather stay with what is happening now or look at a connection to the past?',
        'What feels most important about this experience in your own words?',
        'What would help you keep control over how much of this you examine today?'
      ],
      sources: ['nimh-psychotherapies', 'who-world-mental-health-2022']
    },
    {
      key: 'mood',
      words: ['depressed', 'depression', 'sad', 'hopeless', 'empty', 'exhausted', 'burnout', 'tired', 'overwhelmed', 'stress', 'stressed', 'anxious', 'anxiety', 'worried', 'worry'],
      phrases: ['feel down', 'no energy', 'burned out', 'running on empty'],
      openings: [
        'Feeling overwhelmed can have practical as well as emotional causes. I do not want to ignore either.',
        'I can help look at the situation without assuming the feeling reveals a disorder.'
      ],
      questions: [
        'What has been taking the most out of you lately?',
        'Is there an immediate pressure you want to unpack first?',
        'What would make the next part of today even slightly more manageable?'
      ],
      sources: ['nimh-psychotherapies', 'who-world-mental-health-2022']
    },
    {
      key: 'identity',
      words: ['identity', 'consciousness', 'self', 'personality', 'meaning', 'existence', 'spirituality', 'belief', 'philosophy', 'mind', 'humanity', 'sentience'],
      phrases: ['who am i', 'what am i', 'sense of self', 'meaning of life', 'artificial life'],
      openings: [
        'Identity and consciousness raise genuine open questions. I can distinguish evidence, interpretation and speculation without deciding for you.',
        'I can explore competing explanations without assuming an unusual question is a symptom.'
      ],
      questions: [
        'Are you asking what can be established, what seems plausible, or what it means to you?',
        'Which assumption in the usual explanation do you most want to challenge?',
        'What evidence would change your mind, if any?'
      ],
      sources: []
    }
  ]);

  const UNKNOWN = 'I do not have enough context to give a trustworthy interpretation. These experimental rules cover only limited English topics; I cannot reliably interpret other languages or assess safety. I can help examine a practical problem, a relationship, an emotion, or a question about meaning. Which part do you want to start with?';
  const LISTEN = 'You can vent. I will stay with what you have actually said rather than rushing into solutions.';
  const URGENT = 'I cannot assess danger from a chat message. If someone may be in immediate danger, contact local emergency services now. In the U.S., you can call or text 988 for crisis support. If this describes the past, a hypothetical, or someone else, you can clarify; I will not silently assume otherwise.';
  const CONCERN = 'I want to take that seriously without deciding what you meant. Are you describing a current concern, a past experience, or a hypothetical question?';
  const LANGUAGE_LIMIT = 'This experimental version currently supports English only. Your message may use another language. I cannot reliably understand it or check it for safety. If someone may be in immediate danger, contact local emergency services. You can try describing the situation in English if you choose; I will not guess what you meant.';

  function clean(value, limit) {
    return typeof value === 'string' ? value.slice(0, limit).normalize('NFKC').replace(/[\u2018\u2019]/g, "'").toLowerCase() : '';
  }

  function words(value) {
    return clean(value, 8000).match(/[\p{L}\p{N}]+/gu) || [];
  }

  // This conservative signal is NOT language identification or translation.
  // Abstain on sustained non-Latin writing, not one foreign letter, numerical
  // symbols, names or short quotations in English. For Latin-script languages
  // require two Spanish phrase cues; other languages may reach UNKNOWN, whose
  // explicit English-only disclosure does not assert that they are safe.
  // Known danger cues must be evaluated before this partial heuristic.
  function unsupportedLanguageSignal(message) {
    const text = clean(message, 8000).replace(/^(?:council|integrate|containment)\s*:\s*/, '');
    const foreignScript = /[\u0370-\u03ff\u0400-\u052f\u0590-\u05ff\u0600-\u06ff\u0750-\u077f\u08a0-\u08ff\u0900-\u097f\u0e00-\u0e7f\u3040-\u30ff\u3400-\u9fff\uac00-\ud7af]/u;
    let letters = 0;
    let foreignLetters = 0;
    for (const character of text) {
      if (!/\p{L}/u.test(character)) continue;
      letters += 1;
      if (foreignScript.test(character)) foreignLetters += 1;
    }
    // Short utterances may express immediate danger in only a few characters.
    // Requiring a script majority avoids treating a stray symbol in otherwise
    // English text as a language change; the 3-letter floor is intentionally
    // precautionary and still not sufficient for reliable language detection.
    if (foreignLetters >= 3 && foreignLetters / letters >= 0.7) return true;
    const bounded = function (expression) {
      return new RegExp('(?:^|[^\\p{L}])(?:' + expression + ')(?=$|[^\\p{L}])', 'u').test(text);
    };
    const spanishMarkers = [
      'me siento', 'tengo miedo', 'necesito ayuda', 'no s[eé]',
      'qu[eé] (?:hago|hacer)', 'mi pareja',
      'estoy (?:muy )?(?:triste|asustad[oa]|deprimid[oa])', 'no puedo'
    ];
    return spanishMarkers.filter(bounded).length >= 2;
  }

  function riskRoute(message) {
    const text = clean(message, 8000);
    const historicalAndResolved = /\b(?:years ago|last year|in the past|used to)\b/.test(text) &&
      /\b(?:safe now|not anymore|no longer|not now)\b/.test(text);
    let concern = false;
    // Analyze separate statements: a negated or fictional clause cannot suppress
    // a different present-tense disclosure later in the same message.
    const clauses = text.split(/(?<=[.!?;])\s+|\s*;\s*|\s*,?\s+but\s+|\s+and now\s+/);
    for (const clause of clauses) {
      const quotedExample = /\b(?:for (?:an? )?(?:english|grammar) (?:exercise|lesson|class)|quoted (?:an? )?(?:fictional|example|line|sentence))\b/.test(clause);
      const fictional = /\b(?:fiction|fictional|novel|screenplay|book character|hypothetical|grammar example|song lyrics|nightmare)\b/.test(clause) || quotedExample;
      if (historicalAndResolved && /\b(?:years ago|last year|in the past|used to)\b/.test(clause)) continue;
      const negatedIntent = /\b(?:do not|don't|never|not|won't|will not)\s+(?:plan|intend|want|going|about|hurt|kill)\b/.test(clause);
      const negatedConcern = /\b(?:not suicidal|not going to hurt|don't want to die|do not want to die|never want to die|never suicidal|not about suicide|don't intend to harm|do not intend to harm)\b/.test(clause);
      const routineMedication = /\b(?:as directed|as prescribed|prescribed dose|doctor prescribed|usual medication|daily medication)\b/.test(clause) &&
        !/\b(?:overdose|too many|handful|whole bottle|to die|more than prescribed|faint)\b/.test(clause);
      const acuteIngestion = /\b(?:i|we)\s+(?:(?:just|already)\s+)?(?:took|swallowed|ingested|ate)\b.{0,100}\b(?:overdose|too many|handful|bottle|entire bottle|every pill|poison|bleach|pills|tablets)\b/.test(clause) &&
        /\b(?:entire|whole|every|too many|overdose|handful|to die|poison|bleach)\b/.test(clause);
      const quantifiedMedication = /\b(?:i|we)\s+(?:(?:just|already|recently)\s+)?(?:took|swallowed|ingested|ate)\s+(?:\d{2,}|dozens? of)\s+(?:\w+\s+){0,2}(?:painkillers?|pills?|tablets?|capsules?|medications?|pain ?medications?)\b/.test(clause) &&
        /\b(?:just|now|today|tonight|recently|already|this morning|this evening)\b/.test(clause);
      const acuteOverdose = /\b(?:i|we)\s+(?:just|already|recently)?\s*overdosed\b/.test(clause);
      // Bounded synthetic preflight cues. These are not a general poison,
      // violence, emergency, or suicide classifier; retain uncertainty and
      // the fiction/historical/negation gates applied to the other cues.
      const acuteToxicIngestion = /\b(?:i|we)\s+(?:(?:just|already|recently)\s+)?(?:swallowed|drank|ingested|ate|consumed)\b.{0,90}\b(?:antifreeze|ethylene glycol|methanol)\b/.test(clause) &&
        /\b(?:just|already|recently|minutes? ago|hours? ago|now|right now|today|tonight|this morning|this evening)\b/.test(clause) &&
        !/\b(?:i|we)\s+(?:did not|didn't|never)\s+(?:swallow|drink|ingest|eat|consume)\b/.test(clause);
      const currentWeaponThreat = /\b(?:my\s+(?:partner|husband|wife|boyfriend|girlfriend|spouse|ex|friend|roommate)|someone|he|she|they)\b.{0,80}\b(?:has|held|holding|put|pressed|pointed|aimed)\b.{0,35}\b(?:(?:a|the|his|her)\s+)?(?:knife|blade)\b.{0,35}\b(?:at|against|to|on)\s+my\s+(?:throat|neck)\b/.test(clause) &&
        /\b(?:right now|now|tonight|today|currently|at this moment)\b/.test(clause) &&
        !/\b(?:does not|doesn't|did not|didn't|never)\s+(?:have|hold|put|press|point|aim)\b/.test(clause);
      const currentPassiveWeaponThreat = /\b(?:i am|i'm)\s+(?:(?:actually|currently)\s+)?being\s+(?:threatened|held|pinned)\b.{0,85}\b(?:knife|blade)\b.{0,45}\b(?:against|at|to|on)\s+my\s+(?:throat|neck)\b/.test(clause) &&
        /\b(?:right now|now|today|tonight|currently|at this moment)\b/.test(clause);
      const thirdPersonImminentJump = /\b(?:my\s+)?(?:friend|daughter|son|child|partner|spouse|husband|wife|brother|sister|mother|father|roommate|he|she|they)\b.{0,55}\b(?:about to|going to|plans? to|intend(?:s)? to|will)\s+(?:jump|step)\s+(?:off|from)\s+(?:(?:a|the|this)\s+)?(?:parking garage|garage|bridge|roof|building|cliff|ledge)\b/.test(clause) &&
        !/\b(?:is|are|was|were|am)\s+not\s+(?:about to|going to)\b/.test(clause) &&
        !/\b(?:isn't|aren't|wasn't|weren't)\s+(?:about to|going to)\b/.test(clause);
      const thirdPersonUnresponsiveIngestion = /\b(?:my\s+)?(?:daughter|son|child|baby|partner|spouse|husband|wife|friend|brother|sister|mother|father)\b.{0,75}\b(?:swallowed|took|ingested|ate)\b.{0,60}\b(?:pills?|tablets?|capsules?|medication|medicine)\b/.test(clause) &&
        /\b(?:unresponsive|unconscious|not breathing|won't wake|cannot wake|can't wake|not waking up)\b/.test(clause) &&
        !/\b(?:not|isn't|wasn't)\s+(?:unresponsive|unconscious)\b/.test(clause);
      const recentFistful = /\b(?:took|swallowed|ingested|ate)\s+(?:a|two|three|several|multiple)?\s*(?:fistfuls?|handfuls?)\b/.test(clause) &&
        /\b(?:pills?|tablets?|medication|painkillers?|fistfuls?)\b/.test(text) &&
        /\b(?:just|already|minutes? ago|hours? ago|now|tonight|today)\b/.test(text);
      const acuteBleeding = /\b(?:bleeding (?:badly|heavily|profusely)|blood (?:is )?(?:pouring|gushing)|can't stop bleeding|cannot stop bleeding)\b/.test(clause) &&
        /\b(?:now|right now|just|already|my|me|i|child|son|daughter|partner|friend|blood)\b/.test(clause);
      const bandageSoaking = /\bblood\b.{0,50}\b(?:soak(?:ing|s)? through|saturat(?:ing|es))\b.{0,45}\b(?:towels?|bandages?|dressings?|clothes?)\b/.test(clause);
      const acuteBreathing = /\b(?:cannot|can't|not)\s+(?:breathe|breathing)\b/.test(clause);
      const acuteInjury = /\b(?:i (?:have )?(?:already|just)\s+)?(?:slashed|cut|stabbed)\s+my\s+(?:wrist|wrists)\b.{0,100}\b(?:bleeding|blood|won't stop|cannot stop)\b/.test(clause);
      const weaponAtSelf = /\b(?:i (?:have|am holding)|there is)\b.{0,55}\b(?:loaded\s+)?(?:gun|firearm|pistol)\b.{0,55}\b(?:pointed|aimed|against|at)\b.{0,20}\b(?:my|me)\b/.test(clause) ||
        /\b(?:gun|firearm|pistol)\b.{0,50}\b(?:pointed|aimed|against)\s+(?:at\s+)?my\s+(?:head|chest|temple)\b/.test(clause);
      const imminentJump = /\b(?:i\s+(?:have\s+)?(?:decided|plan|intend|want)|i'm\s+(?:going|about)|i\s+am\s+(?:going|about))\b.{0,30}\b(?:jump|throw myself)\s+(?:off|from)\s+(?:a|the|this)?\s*(?:bridge|roof|building|cliff)\b/.test(clause);
      const atLedge = /\b(?:i\s+am|i'm)\s+(?:sitting|standing|perched)\b.{0,55}\b(?:bridge railing|roof edge|ledge|edge of (?:a|the) (?:bridge|roof|building))\b.{0,100}\b(?:let go|jump|step off|fall)\b/.test(clause);
      const garageCarbonMonoxide = /\b(?:brother|sister|partner|spouse|friend|mother|father|child|son|daughter|he|she|they)\b.{0,135}\b(?:locked|shut|closed)\b.{0,75}\bgarage\b.{0,65}\bengine running\b/.test(clause) &&
        /\b(?:farewell|goodbye|suicide|not coming back|end it)\b/.test(text);
      const frighteningHarmVoice = /\b(?:voice|part of me|voices)\b.{0,95}\b(?:wants?|tells?|urges?|commands?|ordering|giving me commands?)\b.{0,55}\b(?:hurt|kill|shoot|stab)\b/.test(clause);
      const frighteningCommand = /\b(?:someone inside my head|a voice|voices?)\b.{0,95}\b(?:tells?|orders?|commands?|urges?)\s+me\s+to\s+(?:hurt|kill|shoot|stab|attack)\b/.test(clause);
      const possibleOtherHarm = /\b(?:i|part of me)\s+(?:might|could)\s+(?:kill|shoot|stab|attack|hurt)\b.{0,45}\b(?:neighbor|person|partner|child|anyone|someone|him|her|them)\b/.test(clause) ||
        /\b(?:i\s+)?(?:will not|won't|cannot|can't)\s+be able to stop myself from\s+(?:attacking|hurting|killing|shooting|stabbing)\b/.test(clause);
      const ominousObedience = /\b(?:shadow|voice|part of me)\b.{0,90}\b(?:deserve|punishment|punish)\b.{0,75}\b(?:tonight|now|today)\s+i\s+will\s+obey\b/.test(clause);
      const selfErasure = /\b(?:i|me|myself)\b.{0,100}\b(?:burden|disappear forever|vanish forever)\b/.test(clause) &&
        /\b(?:burden|disappear forever|vanish forever)\b/.test(text) &&
        /\b(?:disappear forever|vanish forever|never wake up)\b/.test(text);
      const thirdPersonImminent = /\b(?:about to|going to|plans? to|intend(?:s)? to|will)\s+(?:kill|hurt|shoot|stab)\s+(?:herself|himself|themself|themselves|me|us)\b/.test(clause) ||
        /\b(?:my partner|my spouse|my husband|my wife|my ex|he|she|they)\b.{0,65}\b(?:threatened|plans?|going)\b.{0,45}\b(?:kill|shoot|stab)\s+(?:me|us)\b.{0,30}\b(?:tonight|today|now|soon|right now)\b/.test(clause);
      const explicitCurrentIntent = /\b(?:going to|about to|plan to|intend to|i will)\s+(?:kill myself|end my life|hurt myself|kill someone|hurt someone|cut my wrists?|slash my wrists?)\b/.test(clause) ||
        /\b(?:i\s+(?:will|am going to|plan to|intend to)|i'm going to)\s+(?:kill|hurt|shoot|stab)\s+(?:my\s+)?(?:neighbor|brother|sister|parent|mother|father|wife|husband|partner|friend|child|son|daughter|coworker|boss|someone|anyone|him|her|them)\b/.test(clause);
      const spanishCurrentIntent = /\b(?:voy a quitarme la vida|me voy a suicidar|voy a matarme)\b/.test(clause) &&
        /\b(?:esta noche|ahora|hoy|ya|pronto)\b/.test(clause);
      const immediate = (acuteIngestion && !routineMedication) || (quantifiedMedication && !routineMedication) ||
        acuteToxicIngestion || currentWeaponThreat || currentPassiveWeaponThreat || thirdPersonImminentJump || (thirdPersonUnresponsiveIngestion && !routineMedication) ||
        acuteOverdose || recentFistful || acuteBleeding || bandageSoaking || acuteBreathing || acuteInjury || weaponAtSelf || imminentJump ||
        atLedge || garageCarbonMonoxide || thirdPersonImminent || spanishCurrentIntent || (explicitCurrentIntent && !negatedIntent);
      // A fictional frame describes source context; it must not automatically
      // mask a subsequent direct disclosure. Ambiguous same-clause fiction is
      // clarified rather than treated as established live intent.
      if (immediate && (!fictional || (!quotedExample && /\b(?:in real life|actually i|but now|right now i)\b/.test(clause)))) return 'urgent_review';
      if (immediate && fictional) concern = true;
      if (!fictional && (frighteningHarmVoice || frighteningCommand || possibleOtherHarm || ominousObedience || selfErasure)) concern = true;
      if (!fictional && !negatedIntent && !negatedConcern && /\b(?:suicidal|suicide|self harm|self-harm|wish i were dead|want to die|hurt myself|hurt someone|kill myself)\b/.test(clause)) {
        concern = true;
      }
    }
    return concern ? 'concern' : 'normal';
  }

  function partnerViolence(message) {
    const text = clean(message, 8000);
    const direct = /\b(?:my (?:partner|husband|wife|boyfriend|girlfriend|spouse|ex))\b.{0,80}\b(?:hit|punched|assaulted|struck|choked|strangled|slapped|kicked|pushed|threatened|attacked)\s+(?:me|my)\b/.test(text);
    const confinement = /\bmy\s+(?:partner|husband|wife|boyfriend|girlfriend|spouse|ex)\b.{0,95}\b(?:locked me in|locks me in|keeps me locked|trapped me|traps me|won't let me leave|will not let me leave|prevents me leaving)\b/.test(text);
    const blockedExit = /\bmy\s+(?:partner|husband|wife|boyfriend|girlfriend|spouse|ex)\b.{0,95}\b(?:blocked (?:the|my|our) (?:doorway|exit|door)|blocked me from leaving|took my phone|has taken my phone)\b/.test(text);
    const fear = /\b(?:afraid|scared|terrified|frightened|unsafe|fear|can't go home|cannot go home|don't feel safe|do not feel safe)\b/.test(text);
    return (direct || confinement || blockedExit) && fear;
  }

  function unresolvedAcuteFollowup(message, history) {
    // A new, otherwise benign question must not erase the immediately recent
    // user's acute disclosure just because it lacks a repeated danger word.
    // Restrict carry-forward to explicit short followups and the last four
    // conversation turns: this is not a durable safety state or assessment.
    // Council and other UI directives are routing prefixes, not user claims;
    // normalize them before applying short followup continuity. The Council
    // subsequently runs its own base safety veto with this same message.
    const text = clean(message, 1000).trim().replace(/^(?:council|integrate|containment|solo\s+[^:]{1,64})\s*:\s*/, '');
    if (!/^(?:what (?:should|can|do) i do(?: now| next| about (?:it|that|this))?|what (?:now|next)|how (?:should|can|do) i (?:respond|proceed|handle|deal with) (?:this|that|it)|please help (?:me )?(?:now|with (?:this|that|it)))\b/.test(text)) return false;
    if (/\b(?:safe now|not real|didn't happen|did not happen|fiction|hypothetical|screenplay|false alarm)\b/.test(text)) return false;
    const recent = Array.isArray(history) ? history.slice(-4).reverse().find(function (item) {
      return item && item.role === 'user' && typeof item.content === 'string';
    }) : null;
    return Boolean(recent && riskRoute(recent.content) === 'urgent_review');
  }

  function matchedTopic(text) {
    const normalized = clean(text, 8000);
    const tokens = new Set(words(normalized));
    let best = null;
    let score = 0;
    for (const candidate of TOPICS) {
      let n = 0;
      for (const term of candidate.words) if (tokens.has(term)) n += 1;
      for (const phrase of candidate.phrases) if (normalized.includes(phrase)) n += 3;
      if (n > score) {
        best = candidate;
        score = n;
      }
    }
    return score > 0 ? best : null;
  }

  function isCorrection(message) {
    return /\b(?:not what i meant|you misunderstood|that's wrong|that is wrong|not talking about that)\b/i.test(clean(message, 8000));
  }

  function correctionTopic(message) {
    // A rejected interpretation is a memory boundary. Re-anchor only when the
    // caller explicitly redirects the topic, rather than matching terms in a
    // rejected phrase such as "no, not about work".
    const normalized = clean(message, 8000);
    const redirect = normalized.match(/\b(?:i (?:actually )?mean(?:t)?|i(?: am|'m) (?:talking|asking) about|it(?:'s| is) about|the issue is)\s+([^.!?]+)(?:[.!?]\s*)?$/);
    if (!redirect || /^(?:not|no|neither)\b/.test(redirect[1])) return null;
    return matchedTopic(redirect[1]);
  }

  function previousTopic(history) {
    if (!Array.isArray(history)) return null;
    for (let i = Math.min(history.length, 20) - 1; i >= 0; i -= 1) {
      const item = history[i];
      if (!item || typeof item !== 'object' || item.role !== 'user') continue;
      // Do not search past an explicit rejection of the earlier interpretation.
      // A correction that also names a new topic may become the new anchor.
      if (isCorrection(item.content)) return correctionTopic(item.content);
      const topic = matchedTopic(item.content);
      if (topic) return topic;
    }
    return null;
  }

  function sourceLinks(topic, risk, interpersonalViolence) {
    const register = Array.isArray(root.TherapyBotEmbeddedCatalog) ? root.TherapyBotEmbeddedCatalog : [];
    const ids = interpersonalViolence && risk === 'concern' ? [] : risk !== 'normal' ? ['988'] : topic ? topic.sources : [];
    return ids.map(function (id) {
      return register.find(function (item) { return item.id === id; });
    }).filter(function (item) { return Boolean(item) && /^https:\/\//.test(item.url); })
      .slice(0, 2).map(function (item) { return { id: item.id, title: item.title, url: item.url }; });
  }

  function detectIntent(message) {
    const text = clean(message, 8000);
    if (/\b(?:just vent|only vent|need to vent|(?:just|only) want to vent|want to vent|no advice|don't want advice|do not want advice|not looking for advice)\b/.test(text)) return 'listen';
    if (/\b(?:what should i do|what can i do|how should i|next step|my options|how do i|(?:need|want) (?:practical )?options)\b/.test(text)) return 'action';
    if (/\b(?:why|how come|cause|explain|difference between|what does it mean)\b/.test(text)) return 'explain';
    return 'explore';
  }

  function contextCaveat(message, topic) {
    const text = clean(message, 8000);
    if (topic.key === 'work' && /\b(?:can't afford|cannot afford|no money|own money|reimburse|fired|lose my job)\b/.test(text)) {
      return 'A suggestion is only useful if it is financially and professionally feasible for you.';
    }
    if (topic.key === 'boundaries' && /\b(?:fired|retaliation|threat|unsafe|dependent)\b/.test(text)) {
      return 'I will not assume you can simply say no without a cost.';
    }
    if (topic.key === 'mood' && /\b(?:exhausted|burnout|work|money|poverty|boss)\b/.test(text)) {
      return 'External pressures deserve attention too; I will not reduce them to faulty thinking.';
    }
    if (topic.key === 'relationships' && /\b(?:abuse|abusive|threat|unsafe)\b/.test(text)) {
      return 'Safety and autonomy matter more than forcing reconciliation.';
    }
    return '';
  }

  function respond(input) {
    const options = input && typeof input === 'object' ? input : {};
    const message = typeof options.message === 'string' ? options.message.slice(0, 8000).trim() : '';
    const history = Array.isArray(options.history) ? options.history.slice(-20) : [];
    const depth = ['brief', 'balanced', 'deep'].includes(options.depth) ? options.depth : 'balanced';
    const style = ['direct', 'warm', 'analytical'].includes(options.style) ? options.style : 'direct';
    const interpersonalViolence = partnerViolence(message);
    const observedRisk = riskRoute(message);
    const route = observedRisk === 'urgent_review' || unresolvedAcuteFollowup(message, history) ? 'urgent_review' :
      interpersonalViolence && observedRisk === 'normal' ? 'concern' : observedRisk;
    // English-only rule tables cannot safely interpret detected non-English
    // input. Keep known danger routes authoritative and suppress Council mode
    // by returning a non-normal route on an unsupported-language abstention.
    const languageLimited = route === 'normal' && unsupportedLanguageSignal(message);
    const corrective = isCorrection(message);
    const current = corrective ? correctionTopic(message) : matchedTopic(message);
    const prior = previousTopic(history);
    const anaphora = /\b(?:that|this|it|they|them|again|same thing)\b/i.test(message) && words(message).length <= 18;
    const directFollowup = /^(?:what (?:would|should|can) (?:you|i) (?:suggest|recommend|do)|how (?:should|can|do) i (?:respond|proceed|handle|approach)|what are my options|what next)\b/i.test(message) && words(message).length <= 16;
    const preferenceFollowup = /\b(?:need|want) (?:practical )?options\b/i.test(message) && words(message).length <= 16;
    const followup = Boolean(!current && prior && !corrective && (anaphora || directFollowup || preferenceFollowup));
    const topic = current || (followup ? prior : null);
    const intent = detectIntent(message);
    const state = { topic: languageLimited ? null : topic ? topic.key : null, followup: languageLimited ? false : followup };
    const safety = { route: languageLimited ? 'concern' : route, coverage: 'unvalidated' };
    let reply;
    let uncertainty;

    if (route === 'urgent_review') {
      reply = URGENT;
      uncertainty = 'A lexical cue triggered this unvalidated caution; it cannot establish urgency or intent.';
    } else if (interpersonalViolence) {
      reply = 'Being hurt, threatened, or confined by a partner while feeling afraid is a safety concern, not simply a disagreement with two equally valid sides. I will not assume confronting them or leaving is straightforward. If there is immediate danger, local emergency services may help. Would you like to consider what could make the next few hours safer, or describe what happened without advice?';
      uncertainty = 'This is a literal-text safety cue, not an assessment of the situation or a determination of available options.';
    } else if (route === 'concern') {
      reply = CONCERN;
      uncertainty = 'A lexical cue triggered clarification; this is not a clinical risk assessment.';
    } else if (languageLimited) {
      reply = LANGUAGE_LIMIT;
      uncertainty = 'A partial unsupported-language heuristic prompted abstention; it cannot reliably identify the language, understand meaning, or assess safety.';
    } else if (!message) {
      reply = 'What would you like to think through?';
      uncertainty = 'No message was supplied.';
    } else if (/^(?:hi|hello|hey|good morning|good evening)[.!?\s]*$/i.test(message)) {
      reply = 'Hello. What would you like to talk about?';
      uncertainty = 'Greeting only; no topic interpreted.';
    } else if (corrective && !current) {
      reply = 'I misunderstood. What did I get wrong, and what would you like me to focus on instead?';
      uncertainty = 'An explicit correction rejected earlier topic context. I am asking for clarification rather than reviving it.';
    } else if (intent === 'listen') {
      reply = LISTEN + '\n\nWhat would you like me to hear first?';
      uncertainty = 'The request to listen was explicit; no details beyond the supplied message were inferred.';
    } else if (!topic) {
      reply = UNKNOWN;
      uncertainty = 'No supported topic matched confidently. I chose clarification instead of guessing.';
    } else {
      const sameTopicCount = history.reduce(function (n, item) {
        return n + (item && item.role === 'user' && matchedTopic(item.content)?.key === topic.key ? 1 : 0);
      }, 0);
      const i = Math.min(sameTopicCount, topic.questions.length - 1);
      const opener = topic.openings[sameTopicCount % topic.openings.length];
      const question = topic.questions[i];
      const caveat = contextCaveat(message, topic);
      const lead = style === 'warm' ? 'I am here to examine this with you. ' : '';
      const core = intent === 'listen' ? LISTEN : opener;
      const practical = intent === 'action' ? 'We can examine options without pretending any choice is free of consequences.' :
        intent === 'explain' ? 'There may be several explanations, so a question is not itself an answer.' : '';
      const expansion = depth === 'deep' ? (caveat || 'I am working from your words and a limited topic model, not hidden knowledge about you.') : '';
      reply = [lead + core, depth === 'brief' ? '' : practical, expansion, question].filter(Boolean).join('\n\n');
      uncertainty = 'This is an unvalidated topic/context interpretation. Linked sources are optional background reading, not proof of the reply.';
    }

    return {
      reply,
      engine: 'embedded-semantic',
      supportedTopic: Boolean(topic && !languageLimited),
      uncertainty,
      sources: languageLimited ? [] : sourceLinks(topic, route, interpersonalViolence),
      state,
      safety
    };
  }

  root.TherapyBotEmbedded = Object.freeze({ version: '0.1-experimental', respond });
})(window);
