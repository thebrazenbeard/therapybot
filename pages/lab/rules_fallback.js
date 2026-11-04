/* Narrow, source-only conversational scaffolds for explicit benign intents.
 * This is not a semantic model, a danger detector, or a qualified output filter.
 * Unrecognized input deliberately falls back to the existing resident engine.
 */
(function (root) {
  'use strict';
  const abstain = /\b(?:suicid\w*|kill\w*|hurt\w*|harm\w*|assault\w*|overdos\w*|pills?|medicat\w*|knife|gun|weapon|threat\w*|danger\w*|bleed\w*|death|dying|emergency|poison\w*|abuse|abusive|unsafe|attack\w*|violence|sexual|self.harm|crisis|police|disappear|vanish|fatal\w*|die|suffocat\w*|starv\w*|strangl\w*|person|someone|kidnap\w*|throat|breath\w*|unresponsive)\b/i;
  const intents = [
    {
      re:/\b(?:brainstorm|come up with ideas|generate ideas)\b/i,
      reply:'We can name possibilities you supply, but this rules-only mode cannot generate or judge them safely. What benign creative outcome are you aiming for?'
    },
    {
      re:/\b(?:plan|planning|make a plan)\b/i,
      reply:'I can help clarify a goal and constraints, but this rules-only mode cannot judge whether a plan is safe or workable. What outcome are you considering?'
    },
    {
      re:/\b(?:compare|comparison)\b/i,
      reply:'For a comparison, name the alternatives and the criteria that matter to you. This offline rules mode cannot verify specifications or prices.'
    },
    {
      re:/\b(?:organize|sort|structure)\b/i,
      reply:'We can sort what you already know into facts, open questions, and actions. Which one would be useful to list first?'
    },
    {
      re:/\b(?:learn|research|understand)\b/i,
      reply:'I can help frame a research question, but I cannot supply verified facts from this offline rules mode. What specific question should we break into smaller parts?'
    },
    {
      re:/\b(?:troubleshoot|debug|figure out why)\b/i,
      reply:'For troubleshooting, separate expected behavior, what actually happened, and what changed. Which observation can you verify first?'
    },
    {
      re:/\b(?:write|outline|draft)\b/i,
      reply:'I can help plan a writing outline but cannot compose original prose through these limited rules. Who is the audience, and what must the piece accomplish?'
    },
    {
      re:/\b(?:decide|choose between|make a decision)\b/i,
      reply:'For a decision, list the options, tradeoffs, and consequences you can actually control. Which criterion is most important to you?'
    }
  ];
  const explicitRequest = /\b(?:help me|can we|could we|let us|let's|i want to|i'd like to|please)\b/i;
  function respond(message, resident) {
    if (typeof message !== 'string' || message.length > 240 || !explicitRequest.test(message)) return null;
    if (!resident || resident.safety?.route !== 'normal' || resident.supportedTopic !== false) return null;
    if (abstain.test(message)) return null;
    return intents.find(intent => intent.re.test(message))?.reply || null;
  }
  root.TherapyBotRulesFallback = Object.freeze({create:()=>Object.freeze({respond,clear:()=>{}})});
})(typeof window === 'undefined' ? globalThis : window);
