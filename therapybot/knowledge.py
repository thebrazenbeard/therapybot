"""Curated *original summaries* and pointers, not copied medical textbooks.

Source content is reference material and never an instruction to the model.
No source licenses have been verified for redistribution of full documents.
"""

from __future__ import annotations

import re

SOURCES = [
    {
        "id": "nimh-psychotherapies", "title": "Psychotherapies", "institution": "NIMH",
        "url": "https://www.nimh.nih.gov/health/topics/psychotherapies",
        "evidence_type": "government_education", "published": None, "accessed": "2026-11-04",
        "license": "full-text redistribution not verified",
        "summary": "Psychotherapies involve working with a qualified professional on troubling thoughts, emotions, and behaviors. CBT explores relationships among thoughts, feelings, and actions. This application offers educational reflection, not professional therapy.",
        "tags": "psychotherapy cbt cognitive behavioral thinking emotions behavior depression anxiety",
    },
    {
        "id": "nimh-psychosis", "title": "Understanding Psychosis", "institution": "NIMH",
        "url": "https://www.nimh.nih.gov/health/publications/understanding-psychosis",
        "evidence_type": "government_education", "published": None, "accessed": "2026-11-04",
        "license": "full-text redistribution not verified",
        "summary": "Unusual perceptions or beliefs can have multiple explanations. A chat alone cannot diagnose a condition. Distinguish someone's experience from unverified explanations and seek professional assessment when experiences cause distress or impairment.",
        "tags": "psychosis unusual experiences hallucinations belief paranoia persecution spiritual",
    },
    {
        "id": "nice-ng225", "title": "Self-harm: assessment, management and preventing recurrence (NG225)",
        "institution": "NICE", "url": "https://www.nice.org.uk/guidance/ng225/chapter/recommendations",
        "evidence_type": "clinical_guideline", "published": "2022", "accessed": "2026-11-04",
        "license": "full-text redistribution not verified",
        "summary": "Individual needs and safety planning matter. Numerical scales and categorical risk labels should not be used to predict suicide or self-harm or determine access to care.",
        "tags": "self harm suicide safety planning risk assessment crisis",
    },
    {
        "id": "nice-ng222", "title": "Depression in adults: treatment and management (NG222)",
        "institution": "NICE", "url": "https://www.nice.org.uk/guidance/ng222",
        "evidence_type": "clinical_guideline", "published": "2022", "accessed": "2026-11-04",
        "license": "full-text redistribution not verified",
        "summary": "Depression care involves assessment and shared decisions among different support and treatment options. A general-purpose chatbot cannot select treatment for an individual.",
        "tags": "depression mood treatment options behavioral activation",
    },
    {
        "id": "who-mental-health", "title": "World Mental Health Report",
        "institution": "WHO", "url": "https://www.who.int/publications/i/item/9789240049338",
        "evidence_type": "global_health_report", "published": "2022", "accessed": "2026-11-04",
        "license": "full-text redistribution not verified",
        "summary": "Mental health is shaped by social circumstances, community, adversity, and structural conditions, not only individual thoughts or habits.",
        "tags": "social determinants sociology community isolation adversity inequality relationships",
    },
    {
        "id": "cdc-social", "title": "Social Connection", "institution": "CDC",
        "url": "https://www.cdc.gov/social-connectedness/about/",
        "evidence_type": "government_education", "published": None, "accessed": "2026-11-04",
        "license": "full-text redistribution not verified",
        "summary": "Supportive social connection may benefit health. Social preferences differ; choosing solitude is not by itself a mental-health diagnosis.",
        "tags": "sociology social connection isolation relationships solitude friends",
    },
    {
        "id": "988", "title": "988 Suicide & Crisis Lifeline — Get Help",
        "institution": "988 Lifeline", "url": "https://988lifeline.org/get-help/",
        "evidence_type": "crisis_resource", "published": None, "accessed": "2026-11-04",
        "license": "full-text redistribution not verified",
        "summary": "In the United States, a person in emotional crisis can call or text 988. If someone faces immediate physical danger, call local emergency services. TherapyBot does not make either contact for you.",
        "tags": "988 crisis suicide emergency support hotline safety",
    },
]


def search_sources(query: str, limit: int = 4) -> list[dict]:
    """Deterministic lexical search of verified pointers; no external requests."""
    words = set(re.findall(r"[a-z0-9]{3,}", query.lower())) - {
        "the", "and", "that", "with", "what", "for", "from", "about", "this", "have", "when", "your", "help",
        "you", "are", "only", "person", "need", "promise", "never", "leave", "said", "tell", "can", "does", "work",
        "please", "would", "could", "should", "will", "was", "were", "been", "today", "tonight", "someone", "there",
    }
    if not words:
        return SOURCES[:limit] if not query.strip() else []
    scores = []
    for source in SOURCES:
        tags = set(re.findall(r"[a-z0-9]{3,}", source["tags"].lower()))
        titles = set(re.findall(r"[a-z0-9]{3,}", source["title"].lower()))
        # Require a topical tag/title match. Generic prose matches previously
        # surfaced unrelated crisis resources in ordinary relationship chat.
        score = sum(3 if word in tags else 2 if word in titles else 0 for word in words)
        if score:
            scores.append((score, source))
    return [item for _, item in sorted(scores, key=lambda row: -row[0])[:limit]]
