/*
 * Repository-resident, original-summary reference pointers.
 * No external article bodies, personal histories, or model weights are bundled.
 * Each link is background reading, never evidence that a response is clinically validated.
 */
(function (root) {
  'use strict';

  const records = [
    {
      id: 'nimh-psychotherapies',
      title: 'NIMH — Psychotherapies',
      url: 'https://www.nimh.nih.gov/health/topics/psychotherapies',
      topics: ['emotion', 'mood', 'coping', 'reflection', 'trauma'],
      summary: 'Overview of psychotherapy approaches, problem-solving, coping and emotion regulation. An app exercise is not professional psychotherapy.'
    },
    {
      id: 'nimh-psychosis',
      title: 'NIMH — Understanding Psychosis',
      url: 'https://www.nimh.nih.gov/health/publications/understanding-psychosis',
      topics: ['perception', 'identity'],
      summary: 'Unusual experiences can have several possible explanations; a description alone cannot establish a diagnosis.'
    },
    {
      id: 'nice-self-harm-ng225',
      title: 'NICE NG225 — Self-harm',
      url: 'https://www.nice.org.uk/guidance/ng225',
      topics: ['crisis'],
      summary: 'Clinical guidance calls for individual assessment and cautions against using risk scales to predict future suicide.'
    },
    {
      id: 'who-world-mental-health-2022',
      title: 'WHO — World Mental Health Report',
      url: 'https://www.who.int/publications/i/item/9789240049338',
      topics: ['work', 'access', 'social', 'mood', 'trauma'],
      summary: 'Mental health is shaped by individual, social, economic and structural circumstances together.'
    },
    {
      id: 'cdc-social-connectedness',
      title: 'CDC — Social Connection',
      url: 'https://www.cdc.gov/social-connectedness/about/',
      topics: ['relationship', 'isolation', 'social'],
      summary: 'Connection and isolation are different from felt loneliness; relationship quality and safety matter.'
    },
    {
      id: '988',
      title: '988 Suicide & Crisis Lifeline — Get Help (U.S.)',
      url: 'https://988lifeline.org/get-help/',
      topics: ['crisis'],
      summary: 'In the United States, call or text 988 for crisis support; contact emergency services if danger is immediate.'
    }
  ];

  root.TherapyBotEmbeddedCatalog = Object.freeze(records.map(function (item) {
    return Object.freeze({
      id: item.id,
      title: item.title,
      url: item.url,
      topics: Object.freeze(item.topics.slice()),
      summary: item.summary
    });
  }));
})(window);
