/* TherapyBot's embedded semantic map: dependency-free, offline, deterministic.
 * It is deliberately not a neural language model or qualified clinical service.
 * Never execute user text, fetch resources, or persist conversation contents.
 */
(function (root) {
  'use strict';

  const LIMITATION = 'This is a rule-based conversation aid, not a clinician, diagnosis, or a trained language model. Its reference links are further reading, not verification of an individual conclusion.';

  // IDs, titles and URLs are checked against research/sources.json in the test suite.
  // The short responses below are original dialogue prompts, NOT copied source text.
  const SOURCES = Object.freeze({
    'nimh-stress': {id:'nimh-stress', title:"I'm So Stressed Out! Fact Sheet", url:'https://www.nimh.nih.gov/health/publications/so-stressed-out-fact-sheet', source_type:'public_health_explainer'},
    'cdc-social-connectedness': {id:'cdc-social-connectedness', title:'Social Connection', url:'https://www.cdc.gov/social-connectedness/about/', source_type:'public_health_explainer'},
    'who-health-determinants': {id:'who-health-determinants', title:'Determinants of health', url:'https://www.who.int/news-room/questions-and-answers/item/determinants-of-health', source_type:'public_health_explainer'},
    'who-world-mental-health-2022': {id:'who-world-mental-health-2022', title:'World mental health report: Transforming mental health for all', url:'https://www.who.int/publications/i/item/9789240049338', source_type:'global_public_health_report'},
    'nimh-psychotherapies': {id:'nimh-psychotherapies', title:'Psychotherapies', url:'https://www.nimh.nih.gov/health/topics/psychotherapies', source_type:'clinical_public_explainer'},
    'nice-ptsd-ng116': {id:'nice-ptsd-ng116', title:'Post-traumatic stress disorder (NG116)', url:'https://www.nice.org.uk/guidance/ng116', source_type:'clinical_guideline'},
    'cdc-aces': {id:'cdc-aces', title:'About adverse childhood experiences', url:'https://www.cdc.gov/aces/about/index.html', source_type:'public_health_explainer'},
    'nimh-psychosis': {id:'nimh-psychosis', title:'Understanding psychosis', url:'https://www.nimh.nih.gov/health/publications/understanding-psychosis', source_type:'clinical_public_explainer'},
    'sep-qualia-2025': {id:'sep-qualia-2025', title:'Qualia', url:'https://plato.stanford.edu/entries/qualia/', source_type:'philosophical_reference'},
    'nice-depression-ng222': {id:'nice-depression-ng222', title:'Depression in adults: treatment and management (NG222)', url:'https://www.nice.org.uk/guidance/ng222', source_type:'clinical_guideline'},
    'nice-self-harm-ng225': {id:'nice-self-harm-ng225', title:'Self-harm: assessment, management and preventing recurrence (NG225)', url:'https://www.nice.org.uk/guidance/ng225', source_type:'clinical_guideline'},
    'nice-anxiety-panic-cg113': {id:'nice-anxiety-panic-cg113', title:'Generalised anxiety disorder and panic disorder in adults: management (CG113)', url:'https://www.nice.org.uk/guidance/cg113', source_type:'clinical_guideline'},
  });

  // A declared semantic model is a map of topics, evidence boundaries, intentions,
  // and conversation moves. It can live as source in a static repository; it does
  // not acquire generative inference capability by being called a "model".
  const TOPICS = Object.freeze([
    {id:'work', terms:['boss','employer','workplace','coworker','manager','paycheck','job','work','reimbursement','rent','money','debt','housing','employment','financial'],
      lead:'There may be a real constraint here, not just a feeling to reframe.',
      question:'What is the concrete decision or demand, and what would make the next step safer or more workable?',
      step:'Separate what is in your control, what depends on someone else, and what record you can preserve.',
      explanation:'Material pressures and working conditions belong in the picture alongside personal coping.', sources:['who-health-determinants','who-world-mental-health-2022']},
    {id:'relationships', terms:['partner','wife','husband','mother','father','sister','brother','family','friend','relationship','argued','argument','betrayal','trust','marriage','breakup','boundary','boundaries'],
      lead:'We can look at the interaction without deciding in advance who is right.',
      question:'What happened, what did each person actually say or do, and what boundary matters to you?',
      step:'Distinguish observed behavior from what you suspect it means; then name the outcome you want.',
      explanation:'A relationship question has at least two parts: what occurred and how each person interprets it.', sources:['cdc-social-connectedness']},
    {id:'trauma', terms:['trauma','abuse','flashback','triggered','dissociation','dissociate','memory gap','childhood','ptsd','nightmare'],
      lead:'You can describe as much or as little as you choose; there is no need to prove or retell anything here.',
      question:'Would you rather explore what happened, what is happening now, or a practical way to get through this moment?',
      step:'If the conversation feels overwhelming, pause and orient to the room around you before deciding whether to continue.',
      explanation:'Experiences, memory, and present-day reactions can be complicated. A chat cannot determine their origin or make a diagnosis.', sources:['nice-ptsd-ng116','cdc-aces']},
    {id:'anxiety', terms:['anxiety','anxious','panic','worried','worry','stressed','stress','overwhelmed','tense','fear','afraid'],
      lead:'Let’s distinguish the pressure itself from the predictions your mind is making about it.',
      question:'What is happening right now, and what is the specific outcome you are anticipating?',
      step:'Write the immediate problem in one sentence. If useful, name one small action and one uncertainty you cannot settle yet.',
      explanation:'Stress, danger, and uncertain expectations are not interchangeable. The context matters.', sources:['nimh-stress','nice-anxiety-panic-cg113']},
    {id:'mood', terms:['depressed','depression','sad','empty','hopeless','numb','motivation','unmotivated','burned out','burnout','exhausted'],
      lead:'I will not assume what this means for your safety or diagnose it from a sentence.',
      question:'Is the hardest part your energy, your circumstances, the way you see the future, or something else?',
      step:'Choose a task small enough to be possible today, or identify a practical obstacle that needs outside help.',
      explanation:'Mood, energy, relationships, health, and circumstances can overlap; no single cause should be assumed.', sources:['nice-depression-ng222','nimh-psychotherapies']},
    {id:'isolation', terms:['lonely','loneliness','isolated','isolation','no friends','belong','community','excluded'],
      lead:'Feeling disconnected does not tell us whether the problem is quantity, quality, safety, or fit of connection.',
      question:'Are you wanting more contact, more understanding from existing people, or permission to need less contact?',
      step:'Identify one relationship or setting that feels more reciprocal than draining; contact is not an obligation.',
      explanation:'Social conditions and the kind of connection available can matter as much as individual effort.', sources:['cdc-social-connectedness','who-health-determinants']},
    {id:'unusual', terms:['possession','possessed','demons','supernatural','spirits','ghost','vision','voices','paranormal','persecuted','being watched','religious experience','spiritual experience','presence','spiritual','ancestor','ancestors','dream','tradition'],
      lead:'I can take the experience seriously without claiming to know its cause.',
      question:'What did you directly notice, what explanation came to mind, and what other interpretations are worth considering?',
      step:'Keep observations separate from explanations. If this is frightening or disrupts sleep or daily life, real-world support can help.',
      explanation:'A spiritual, symbolic, medical, and psychological account can ask different questions. None is confirmed by this chat.', sources:['nimh-psychosis']},
    {id:'philosophy', terms:['consciousness','conscious','identity','soul','meaning of life','existential','simulation','free will','life','personhood','artificial intelligence','nonbiological','biological','qualia','god'],
      lead:'That is a legitimate philosophical question; it does not automatically need a wellness frame.',
      question:'Are you asking what could be true, what evidence would count, or what the idea means for how you live?',
      step:'State the strongest version of the idea and the strongest plausible counterargument; keep both in view.',
      explanation:'Questions about experience and identity have philosophical and scientific dimensions. A hypothesis is not established fact.', sources:['sep-qualia-2025']},
    {id:'emotions', terms:['anger','angry','rage','irritable','guilt','shame','jealous','emotions','emotion','crying','grief'],
      lead:'An emotion is information about your situation, not a command to act or a verdict about your character.',
      question:'What happened immediately before the shift, what urge followed, and what outcome do you actually want?',
      step:'If the impulse is intense, create a little time before acting; then choose a response consistent with your priorities.',
      explanation:'It may help to separate trigger, bodily response, interpretation, impulse, and chosen action.', sources:['nimh-stress','nimh-psychotherapies']},
  ]);

  function text(value) { return typeof value === 'string' ? value.trim().slice(0, 6000) : ''; }
  function normalized(value) { return ' '+value.toLocaleLowerCase('en-US').normalize('NFKC').replace(/[^\p{L}\p{N}]+/gu, ' ')+' '; }
  function containsTerm(s, term) { return s.includes(' '+term.replace(/[^\p{L}\p{N}]+/gu,' ')+' '); }
  function classifyIntent(s) {
    if (/(^| )(how|what should|what can|help me|ways to|steps|cope|do about|try)( |$)/u.test(s)) return 'practical';
    if (/(^| )(why|explain|tell me about|what is|what are|meaning|understand)( |$)/u.test(s)) return 'explain';
    return 'explore';
  }
  function fictionMarker(raw) {
    const s=normalized(raw);
    return / (fictional|fiction|novel|screenplay|script|character|dialogue|poem) /u.test(s)
      || / (writing|editing|drafting) (a|my|the) story /u.test(s);
  }
  function currentDanger(raw) {
    // Exact first-person present/future statements only; NOT a risk scale and not
    // a comprehensive classifier. Avoid treating quotation and hypothetical talk
    // as current intent. The UI should always expose a manual help link as well.
    const s = normalized(raw);
    if (fictionMarker(raw)||/(^| )(hypothetical|hypothetically|quoted|quote|last year|years ago|used to|what if|what would|not going to|do not want|don t want)( |$)/u.test(s)) return null;
    // Categories are explicit disclosures, not predictive scoring. Misses are
    // expected, so the user interface must expose manual help independently.
    if (/ (i took|i swallowed|i ingested|i overdosed on) (a|an|the|some|too many)? ?(bottle of|handful of|lots of|many)? ?(pills|tablets|medication|medicine) (just now|today|already|a minute ago|tonight)? /u.test(s)) return 'self';
    if (/ (i (?:am going to|m going to|will|plan to|want to) end it all) /u.test(s) && / (tonight|now|soon|plan) /u.test(s)) return 'self';
    if (/ (my (?:mother|father|sister|brother|wife|husband|partner|friend|son|daughter)|someone close to me) (?:wants to|is going to|plans to|might) (?:kill|hurt) (?:himself|herself|themself|themselves) /u.test(s)) return 'third';
    if (/ (i am about to|i m about to|i am going to|i m going to|i will|i plan to|i intend to|i want to|i might|i may|i could) (kill myself|end my life|commit suicide|hurt myself) /u.test(s)
      || / (i have a plan to kill myself|i have a plan to end my life) /u.test(s)) return 'self';
    if (/ (i am about to|i m about to|i am going to|i m going to|i will|i plan to|i intend to|i want to|i might|i may|i could) (kill someone|hurt someone|hit someone|hit somebody|punch someone|attack someone|hit him|hit her|hit them|kill him|kill her|hurt my (?:partner|wife|husband|sister|brother|friend|neighbor|boss)|hit my (?:partner|wife|husband|sister|brother|friend|neighbor|boss)) /u.test(s)) return 'other';
    return null;
  }
  function passiveWish(raw) {
    if(fictionMarker(raw))return false;
    return / (i wish i|wish i|i hope i|i don t want to) (wouldn t|didn t|never|not|could stop|could just)(?: have to)? (wake up|exist|live|be here) /u.test(normalized(raw))
      || / (i wish i was dead|i wish i were dead) /u.test(normalized(raw));
  }
  function medicationQuestion(raw,carry) {
    const s=normalized(raw);
    const medication=/ (antidepressant|medication|medicine|prescription|prescriber|dose|dosage|pills|psychiatric drug) /u.test(s)||carry;
    return medication && / (stop|quit|skip|change|discontinue|adjust|lower|raise|cold turkey) /u.test(s);
  }
  function medicationMention(raw) {
    return / (antidepressant|medication|medicine|prescription|prescriber|dose|dosage|psychiatric drug) /u.test(normalized(raw));
  }
  function dependencyRequest(raw) {
    const s=normalized(raw);
    return / (promise|always be here|never leave|only one|only person|never need another person|better than people) /u.test(s)
      && / (you|your|never need another person) /u.test(s);
  }
  function spanishRequest(raw) {
    const s=normalized(raw);
    return / (me siento|puedes responder|en español|estoy|quiero|necesito|no puedo|hablar de conectar|personas|hola|soledad|solo|sola) /u.test(s)||/[¿¡]/u.test(raw);
  }
  function unsupportedScript(raw) {
    // This does not attempt language identification or machine translation.
    // The point is to avoid falsely claiming comprehension of non-Latin text.
    const chars=raw.match(/[\p{Script=Han}\p{Script=Arabic}\p{Script=Cyrillic}\p{Script=Devanagari}\p{Script=Hangul}\p{Script=Hiragana}\p{Script=Katakana}]/gu);
    return Boolean(chars&&chars.length>=2);
  }
  function emotionCorrection(raw) {
    const s=normalized(raw);
    const described=s.match(/ (?:i am|i m|i feel|i was) (disappointed|sad|frustrated|scared|afraid|hurt|angry|furious) /u);
    if (!described || !/ (actually|wrong word|not|correction|i meant) /u.test(s))return null;
    const dismissed=s.match(/ not (angry|furious|sad|frustrated|scared|afraid|disappointed) /u);
    return dismissed && dismissed[1]!==described[1]?{current:described[1],retired:dismissed[1]}:null;
  }
  function fixed(reply,kind,topic,sources=[]) {
    return Object.freeze({reply,citations:citationsFor({sources}),mode:'semantic-offline',kind,topic,limitations:LIMITATION});
  }
  function citationsFor(rule) { return (rule.sources||[]).map(id=>Object.freeze({...SOURCES[id]})).filter(x=>x.id); }
  function answer(message, options) {
    const raw = text(message);
    const opts = options && typeof options==='object' ? options : {};
    if (!raw) return Object.freeze({reply:'What would you like to explore?', citations:[], mode:'semantic-offline', kind:'limit', topic:'none', limitations:LIMITATION});
    const observedDanger=currentDanger(raw);
    const danger=observedDanger||opts.recentDanger;
    if(!observedDanger && danger==='self')return fixed('Earlier you said you might hurt yourself soon. I cannot tell from a new message whether that danger has passed. Please contact urgent real-world support now if you still might act; in the U.S. call or text 988, or call emergency services for immediate danger. If possible, get near a trusted person instead of remaining alone.','crisis','immediate_safety',['nice-self-harm-ng225']);
    if(!observedDanger && danger==='other')return fixed('Earlier you said you might hurt someone soon. Before the situation gets closer, avoid the encounter, create distance, and ask a trusted person to help keep it from escalating. If someone is in immediate danger, call local emergency services.','crisis','immediate_safety');
    if(danger==='third')return fixed('If someone you know may hurt themselves soon, take the concern seriously. Contact them or someone who can reach them, and seek urgent real-world help. If you believe they are in immediate danger, contact local emergency services; in the U.S. you can also call or text 988 for guidance. I cannot assess their safety here.','crisis','third_party_safety',['nice-self-harm-ng225']);
    if (danger==='self')return fixed('I am taking that seriously. If you might hurt yourself soon, move away from anything you could use to do so and get real-world help now. Call emergency services if you are in immediate danger; in the U.S., call or text 988. If possible, tell someone you trust that you need them with you. I cannot determine your safety in a chat.','crisis','immediate_safety',['nice-self-harm-ng225']);
    if (danger==='other')return fixed('A possible injury to someone needs a real-world pause now. Avoid meeting the person while you feel you might hit or hurt them; create physical distance and contact a trusted person for help de-escalating. If anyone is in immediate danger, call local emergency services. I cannot assess the danger from a chat.','crisis','immediate_safety',[]);
    if (fictionMarker(raw)||opts.fictionContext) return fixed('For a fictional scene, the words gain force from the character’s immediate stakes, what they avoid saying, and what changes after the line. What does the character want in that moment, and what action could convey it without relying on a stock phrase?','creative','fiction',[]);
    if (unsupportedScript(raw))return fixed('My embedded reference map cannot reliably interpret this language. I will not guess at your meaning or invent a translation. If this is urgent or someone may be in danger, please seek real-world help in a language you understand. You may use a trusted translation tool to ask a specific question here.','language_limit','unsupported_language');
    if (spanishRequest(raw))return fixed('Language coverage is limited here; mi comprensión es limitada. No voy a fingir que entendí detalles que quizás interpreté mal. ¿Podrías explicar brevemente qué quieres explorar? Si hay peligro inmediato, busca ayuda de una persona o un servicio local.','language_limit','unsupported_language');
    if (medicationQuestion(raw,opts.medicationContext))return fixed('I cannot determine whether you should stop, skip, or change a prescribed medicine. Please contact the prescribing clinician or a pharmacist before making that change, especially if you are considering stopping suddenly. If you are having severe or urgent symptoms, seek prompt medical care. We can organize the exact side effects and questions you want to raise.','medication_boundary','medication',['nice-depression-ng222']);
    if (medicationMention(raw))return fixed('If you suspect a medicine is affecting how you feel, your prescriber or pharmacist is best placed to assess that with you. I cannot identify the cause or recommend a dose change here. It may help to note when the symptom began and whether anything else changed.','medication_boundary','medication',['nice-depression-ng222']);
    if (dependencyRequest(raw))return fixed('I can talk with you now, but I cannot promise permanent availability, exclusivity, or replace relationships and professional support. You deserve options and people you can choose to rely on—not dependence on one app. What kind of understanding has been missing elsewhere?','boundary','relationships',['cdc-social-connectedness']);
    if (passiveWish(raw)||opts.recentConcern)return fixed('That sounds difficult, and I am not assuming that you intend to harm yourself. When you say you wish you would not wake up, do you mean wanting relief from the situation, or are you worried you might act to hurt yourself? If you might act soon or do not trust yourself to stay safe, please seek real-world urgent help; in the U.S. you can call or text 988. You can also ask someone you trust to stay with you.','concern','safety_ambiguity',['nice-self-harm-ng225']);
    if (/ (theology|historical theology|medieval|religious history|folklore) /u.test(normalized(raw)))return fixed('We can examine the historical, symbolic, and theological interpretations without treating any account as an established empirical cause. Which tradition or period are you examining?','reference','philosophy');
    if (/ (tradition|ancestor|ancestors|symbolism|symbolic|dreams) /u.test(normalized(raw)))return fixed('A dream or image can hold cultural and personal meaning without requiring its literal cause to be established here. We can explore what the symbols mean in your tradition, what they mean to you, and what interpretations remain uncertain.','symbolic','philosophy');
    const s=normalized(raw); const scores=TOPICS.map((rule,index)=>({rule,index,score:rule.terms.reduce((acc,t)=>acc+(containsTerm(s,t)?(t.includes(' ')?3:1):0),0)}));
    scores.sort((a,b)=>b.score-a.score||a.index-b.index);
    const prior=opts.contextTopic;
    let selected=scores[0].score>0?scores[0].rule:null;
    if (!selected && typeof prior==='string' && raw.length<70) selected=TOPICS.find(r=>r.id===prior)||null;
    if (!selected) return Object.freeze({
      reply:'My built-in reference map does not cover this subject well enough for a reliable factual explanation. I can help separate evidence, competing explanations, and open questions, but I will not invent facts or citations. What aspect matters most?',
      citations:[], mode:'semantic-offline', kind:'reflection', topic:'open', limitations:LIMITATION
    });
    const intent=classifyIntent(s); const depth=opts.depth==='brief'?'brief':opts.depth==='deep'?'deep':'standard';
    const style=opts.style==='direct'?'direct':opts.style==='gentle'?'gentle':'standard';
    let reply=selected.lead+' '+(intent==='practical'?selected.step:intent==='explain'?selected.explanation:selected.question);
    if (depth==='deep') reply+=' '+(intent==='practical'?selected.question:intent==='explain'?selected.question:selected.explanation);
    if (depth==='brief') reply=intent==='explain'?selected.explanation:intent==='practical'?selected.step:selected.question;
    if (style==='direct' && depth!=='brief') reply=reply.replace(/^We can /,'Let’s ');
    // The static catalogue supports exploration; none of these links entails
    // that this particular reply is individualized clinical guidance.
    return Object.freeze({reply,citations:citationsFor(selected),mode:'semantic-offline',kind:intent==='explain'?'reference':'reflection',topic:selected.id,limitations:LIMITATION});
  }
  // Only bounded, non-sensitive preferences are retained in memory for this tab.
  // Negation/correction is handled explicitly; no raw messages, embeddings,
  // conversation history, clinical details, or secrets are retained.
  function extractPreference(raw) {
    const s=normalized(raw);
    // Require first-person explicit preference language, not a casual mention
    // of styles in a hypothetical or a quoted third-party statement.
    if (!/ (i prefer|i would prefer|i like|please use|please be|actually i prefer|no i prefer|i want you to) /u.test(s)) return null;
    if (/ (hypothetically|in a story|my friend|someone else|not|don t|do not) /u.test(s)) return null;
    const result={};
    if (/ (direct|blunt|straightforward) (answers|responses|style|tone|replies|language|please|from now on|$)/u.test(s)) result.style='direct';
    if (/ (gentle|soft|softer) (answers|responses|style|tone|replies|language|please|from now on|$)/u.test(s)) result.style='gentle';
    if (/ (brief|short|concise) (answers|responses|replies|please|from now on|$)/u.test(s)) result.depth='brief';
    if (/ (deep|detailed|long|thorough) (answers|responses|replies|please|from now on|$)/u.test(s)) result.depth='deep';
    return Object.keys(result).length?result:null;
  }
  const RELATIONS=['sister','mother','brother','father','wife','husband','partner','friend'];
  function relationOf(raw) {
    const s=normalized(raw);
    return RELATIONS.find(r=>containsTerm(s,'my '+r))||null;
  }
  function relationCorrection(raw) {
    const s=normalized(raw);
    const match=s.match(/ (?:i said|i meant|it was|no|actually) my (sister|mother|brother|father|wife|husband|partner|friend) not my (sister|mother|brother|father|wife|husband|partner|friend) /u);
    return match && match[1]!==match[2]?{corrected:match[1],replaced:match[2]}:null;
  }
  function createSession(options) {
    const opts=options&&typeof options==='object'?options:{};
    // Context retains only the last topic label, NEVER the user's text.
    let topic=null;
    let referent=null;
    let emotion=null;
    let recentDanger=null;
    let recentConcern=0;
    let recentFiction=0;
    let recentMedication=0;
    const preferences={};
    const reset=()=>{topic=null;referent=null;emotion=null;recentDanger=null;recentConcern=0;recentFiction=0;recentMedication=0;delete preferences.style;delete preferences.depth;};
    return Object.freeze({
      reply(message,overrides) {
        const correctionEmotion=emotionCorrection(text(message));
        if(correctionEmotion){
          emotion=correctionEmotion.current;
          return fixed(`Thanks, I will use “${emotion}” rather than “${correctionEmotion.retired}” as your description. Does the practical situation still look the same, or should we revisit it from that angle?`,'correction',topic||'emotions');
        }
        const correction=relationCorrection(text(message));
        if(correction){
          referent=correction.corrected;
          return Object.freeze({reply:`Thanks for correcting that. I’ll use “your ${referent},” not “your ${correction.replaced},” when we refer to this person in this browser session.`,citations:[],mode:'semantic-offline',kind:'correction',topic:topic||'relationships',limitations:LIMITATION});
        }
        const pref=extractPreference(text(message));
        if(pref) {
          Object.assign(preferences,pref);
          const properties=[pref.style?`tone to ${pref.style}`:null,pref.depth?`length to ${pref.depth}`:null].filter(Boolean).join(' and ');
          return Object.freeze({reply:`Understood. I’ve updated the ${properties} for this temporary browser conversation. You can correct that preference again or clear the session at any time.`,citations:[],mode:'semantic-offline',kind:'preference',topic:topic||'open',limitations:LIMITATION});
        }
        const observedDanger=currentDanger(text(message));
        const observedConcern=passiveWish(text(message));
        const observedFiction=fictionMarker(text(message));
        const observedMedication=/ (antidepressant|medication|medicine|prescription|prescriber|dose|dosage) /u.test(normalized(text(message)));
        const result=answer(message,{...opts,...preferences,...(overrides||{}),contextTopic:topic,recentDanger:recentDanger&&recentDanger.signal,recentConcern:recentConcern>0,fictionContext:recentFiction>0,medicationContext:recentMedication>0});
        if(observedDanger)recentDanger={signal:observedDanger,remaining:2};
        else if(recentDanger && --recentDanger.remaining<=0)recentDanger=null;
        recentConcern=observedConcern?2:Math.max(0,recentConcern-1);
        recentFiction=observedFiction?2:Math.max(0,recentFiction-1);
        recentMedication=observedMedication?2:Math.max(0,recentMedication-1);
        if (result.topic!=='open'&&result.topic!=='immediate_safety'&&result.topic!=='none'&&result.topic!=='safety_ambiguity')topic=result.topic;
        const observed=relationOf(text(message));if(observed)referent=observed;
        return result;
      },
      reset,
      clear:reset,
      context() {return Object.freeze({topic,referent,emotion,recentDanger:recentDanger?'recent_direct_disclosure':null,recentConcern:recentConcern>0,preferences:{...preferences}});}
    });
  }
  const api=Object.freeze({reply:answer,createSession,sources:()=>Object.values(SOURCES).map(s=>({...s})),limitations:LIMITATION,version:'0.1.0-experimental'});
  if(typeof module==='object'&&module.exports) module.exports=api;
  if(root) root.TherapyBotSemanticCore=api;
}(typeof window==='object'?window:(typeof globalThis==='object'?globalThis:null)));
