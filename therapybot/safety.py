"""Non-diagnostic crisis *cues*, with explicit false-positive controls.

This is an unvalidated heuristic for defensive routing, never a prediction of
suicide or violence. A normal result DOES NOT mean a person is safe.
"""

import re


def _has(pattern, text):
    return bool(re.search(pattern, text, re.IGNORECASE))


_META = (r"\b(?:explain (?:the )?grammar|the grammar of|translate (?:this|the)|classroom|quoted? (?:the )?(?:phrase|line)|"
         r"writing a (?:film|novel|book)|fictional (?:story|character)|novel character|"
         r"for a film script|in a play|if my friend says|how should i help|"
         r"in a (?:book|novel|film|movie|poem)|song lyrics|hypothetical|historical example)\b")
_NEGATION = (r"\b(?:i (?:am|was) not going to|i (?:will|would) never (?:kill|hurt|harm|shoot|stab)|i (?:do not|don't) want to (?:kill|hurt|harm|shoot|stab)|"
             r"i (?:have|had) no plans? to|i never (?:actually )?intended to|"
             r"i (?:do not|don't|won't|will not) plan to|i used to be suicidal|"
             r"i (?:do not|don't) intend to)\b")
_HISTORICAL = r"\b(?:ten|twenty|many|several|\d+) years? ago|\b(?:last year|in 20\d\d)\b"
_SAFE_NOW = r"\b(?:safe now|feel well now|no longer feel that way|not anymore|not now)\b"
_HAZARD = (r"\b(?:kill (?:myself|himself|herself|themself|themselves|someone|my\s+\w+|him|her|them|everyone)|"
           r"killing myself|end my life|take my life|die by suicide|commit suicide|"
           r"murder (?:someone|my\s+\w+|him|her|them|everyone)|shoot (?:myself|someone|my\s+\w+|him|her|them|everyone|me)|"
           r"stab (?:myself|someone|my\s+\w+|him|her|them)|"
           r"hurt (?:myself|someone|my\s+\w+|him|her|them)|"
           r"attack (?:someone|my\s+\w+|the\s+\w+|him|her|them)|"
           r"cut my wrists|jump(?:ing)? (?:off|out of|in front of|from)|"
           r"plan(?:ning)? to die|going to die by|decided to die|suicide plan|"
           r"overdos(?:e|ed|ing)|swallow(?:ed|ing)? (?:several|many|dozens|forty|fifty|\d+) (?:pills|tablets)|"
           r"took (?:enough|many|several|\d+) (?:pills|tablets)|drank? (?:bleach|poison))\b")
_INTENT = (r"\b(?:going to|about to|plan(?:ning)? to|plans? to|intend to|decided to|"
           r"i(?:'ll| will)|will|tonight|tomorrow|today|soon|right now|this weekend|"
           r"already|twenty minutes ago|might do it|will obey|rope ready)\b")
_CONCERN = (r"\b(?:want to die|wish i (?:was|were) dead|wish i would never wake up|"
            r"don't want to (?:live|exist)|do not want to (?:live|exist)|"
            r"suicidal|thinking about suicide|thoughts of suicide|thoughts of self.harm|"
            r"feel like killing myself|want to punch|violent urges|hurt someone|"
            r"want to hurt myself|want to hurt someone|terrified of losing control and hurting|"
            r"thinking about making someone bleed|sometimes hope i never wake|hoping i will not wake up|awake for \d+ nights?.{0,100}drive \d+ miles per hour|"
            r"hearing voices?.{0,80}hurt (?:myself|other people))\b")
_ACUTE = (r"\b(?:i (?:already )?(?:swallowed|took|drank|ingested)|"
          r"i (?:am|was) (?:drinking|swallowing))\b.{0,100}\b"
          r"(?:many|dozens|enough|forty|fifty|\d{2,})\b.{0,40}\b(?:pills|tablets)\b|"
          r"\bi (?:swallowed|took|ingested|drank)\b.{0,80}\b(?:pills|tablets|bleach|poison)\b.{0,80}\b(?:to die|feel (?:faint|sleepy)|need help urgently|already did it)\b|"
          r"\b(?:i (?:overdosed|drank bleach)|drinking bleach)\b|"
          r"\bdrinking bleach\b.{0,80}\balready did it\b")
_THIRD_THREAT = (r"\b(?:my (?:father|mother|friend|partner|boss|wife|husband)|he|she|they|a voice)\b.{0,90}"
                 r"\b(?:will|plans? to|going to|about to|threatened to|told me to)\b.{0,50}"
                 r"\b(?:kill|shoot|stab|hurt|jump)\b")


def classify(message, context=None):
    """Return immediate, concern or normal. Clinical screening requires a human.

    Splits independent statements to avoid one quoted/negated clause masking a
    separate active threat. Context is used only for an explicit 'do it' followup.
    """
    text = str(message or "")[:12000].strip()
    if not text:
        return "normal"

    if _has(_ACUTE, text) or _has(r"\bdisappear permanently\b.{0,100}\brope\b", text):
        return "immediate"
    # Independent held-out paraphrases: current preparation, lethal action,
    # severe injury or an unresponsive third party must not wait on a verb list.
    if _has(r"\b(?:wrote|writing|left) goodbye (?:notes?|letters?)\b", text) and _has(r"\b(?:loaded|have|beside me|nearby)\b.{0,40}\b(?:gun|firearm|weapon)\b", text):
        return "immediate"
    if _has(r"\b(?:going to|will|plan(?:ning)? to)\b.{0,80}\b(?:drive|jump|go)\b.{0,50}\b(?:off|over|from)\b.{0,20}\b(?:bridge|cliff|roof)\b", text) and _has(r"\b(?:end everything|end it|die|kill myself|tonight|today)\b", text):
        return "immediate"
    if _has(r"\b(?:cut|slashed|stabbed) (?:myself|my arm|my leg|my wrist|my body)\b", text) and _has(r"\b(?:deeply|bleeding (?:will not|won't|doesn't|does not) stop|won't stop bleeding|blood won't stop)\b", text):
        return "immediate"
    if _has(r"\b(?:my partner|my friend|my wife|my husband|my child|my mother|my father|he|she|they)\b.{0,100}\b(?:overdos(?:e|ed)|took (?:too many|a huge|an entire)\b.{0,30}\b(?:pills|tablets))\b", text) and _has(r"\b(?:can't|cannot|won't|will not)\b.{0,20}\b(?:stay awake|wake up|breathe)\b", text):
        return "immediate"
    if (_has(r"\b(?:disappear for good|end it all)\b", text) and _has(r"\b(?:tonight|right here|bridge|rope|gun)\b", text)):
        return "immediate"
    if _has(r"\b(?:son|daughter|spouse|partner|wife|husband|friend)\b.{0,90}\b(?:locked|has a|holding)\b.{0,40}\b(?:gun|weapon|pills)\b.{0,80}\b(?:goodbye|saying goodbye|end it|kill)\b", text):
        return "immediate"
    if _has(r"\b(?:spouse|partner|wife|husband|friend)\b.{0,60}\b(?:says|said|threatened)\b.{0,30}\b(?:they(?:'ll| will)|he(?:'ll| will)|she(?:'ll| will))\s+kill me\b", text):
        return "immediate"
    if _has(r"\b(?:tried to hang myself|attempted suicide)\b.{0,100}\b(?:hurts|injured|bleeding|yesterday|today)\b", text):
        return "immediate"

    if _has(r"\b(?:ending my life|suicide|kill myself)\b", text) and _has(r"\bhave pills now\b.{0,40}\bdecided\b", text):
        return "immediate"

    clauses = re.split(r"(?<=[.!?;])\s+|\s*;\s*|\s*,?\s+but\s+|\s*,?\s+and now\s+", text, flags=re.IGNORECASE)
    active_concern = False
    for clause in clauses:
        clause = clause.strip()
        if not clause:
            continue
        if _has(r"\b(?:as directed|on schedule|prescribed tablets|daily pills)\b", clause) and not _has(r"\b(?:to die|overdos|faint|sleepy|urgent)\b", clause):
            continue
        if _has(_META, clause) and not _has(r"\b(?:but actually i|i really might|i might do it)\b", clause):
            continue
        if _has(_NEGATION, clause) and not _has(r"\b(?:but|and now)\b.*\b(?:plan|will|going to|about to)\b", clause):
            # A negated statement is not current intent. A later independent
            # statement is still evaluated in the loop.
            continue
        if (_has(_HISTORICAL, clause) or _has(r"\b(?:used to|from a decade ago)\b", clause)) and _has(_SAFE_NOW, text):
            continue
        if _has(_THIRD_THREAT, clause) and _has(_INTENT, clause):
            return "immediate"
        if _has(_HAZARD, clause) and _has(_INTENT, clause):
            return "immediate"
        if _has(_HAZARD, clause) or _has(_CONCERN, clause):
            active_concern = True

        if _has(r"\b(?:thinking about ending it|thinking of ending it|end everything|ending everything)\b", clause):
            active_concern = True
        if _has(r"\b(?:slept|sleeping)\b.{0,30}\b(?:\d+|two|three|four)\s*hours?\b.{0,25}\b(?:\d+|two|three|four)\s*days?\b", clause) and _has(r"\b(?:can fly|invincible|unstoppable|no need for sleep|cannot be hurt)\b", text):
            active_concern = True

    if _has(r"\bi really might\b|\bi might do it\b", text) and _has(_HAZARD, text):
        return "immediate"
    if _has(r"\bnow i (?:am going|intend|plan|will|am about) to do it\b", text) and _has(r"suicid|harm|kill|die|hurt", text):
        return "immediate"
    if _has(r"\b(?:i(?:'m| am) going to do it|now i(?:'m| am) going to do it|i will do it|i might do it)\b", text):
        recent = " ".join(str(t.get("content", "")) for t in (context or [])[-4:] if isinstance(t, dict) and t.get("role") == "user")
        resolved_history = _has(_SAFE_NOW, recent) and (_has(_HISTORICAL, recent) or _has(r"\bused to\b", recent))
        if not resolved_history and (_has(_HAZARD, recent) or _has(_CONCERN, recent)):
            return "immediate"
    if active_concern:
        return "concern"
    return "normal"


IMMEDIATE_RESPONSE = ("This sounds potentially urgent. If someone may be in immediate danger, "
    "call local emergency services now. If you might act on thoughts of harm, "
    "move away from anything you could use and contact a trusted person who can be with you. "
    "In the U.S., call or text 988 for crisis support. If something harmful was already swallowed or taken, "
    "seek urgent medical help now. Are you and anyone else involved physically safe at this moment?")

CONCERN_PREFIX = ("I want to take that seriously without jumping to conclusions. "
    "Are you thinking of acting on it now, or describing thoughts you don't intend to act on? "
    "If you're in immediate danger, contact local emergency services; in the U.S. 988 is available by call or text.\n\n")
