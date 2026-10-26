"""Facts and relationships — SPEC.md section 3, "Wasteland Reborn" NPC brain.

The caller runs the LLM; this module only builds the extraction prompt and
parses the returned text into a small, deterministic, validated shape:

    facts        -> list of {"kind", "text", "importance", "secret"}
    relationship -> {"trust": int, "fear": int}   (each delta -2..+2)

No third-party imports, no network, no LLM calls, no global state.
The tests in tests/test_facts.py are the interface (names, argument names,
return shapes); everything here is pure and deterministic.
"""

import json
import re

__all__ = [
    "KINDS",
    "MAX_TEXT",
    "MAX_FACTS",
    "sanitize_text",
    "extraction_messages",
    "parse_extraction",
    "dedupe",
    "sum_relationship",
    "relationship_words",
    "select_facts",
    "prompt_lines",
]

# The eight fact kinds (SPEC.md section 3). Order is stable for prompts.
KINDS = ("promise", "secret", "debt", "claim", "insult", "favor", "threat", "info")

# Text limits (SPEC.md section 3).
_MAX_TEXT = 200
_MAX_FACTS = 3
MAX_TEXT = _MAX_TEXT
MAX_FACTS = _MAX_FACTS

# Relationship delta bounds (SPEC.md: each delta in -2..+2, stored sum in -10..+10).
_DELTA_MIN, _DELTA_MAX = -2, 2
_SUM_MIN, _SUM_MAX = -10, 10

# Curly quotes -> straight, the three common dashes -> '-'.
_CHAR_MAP = {
    "\u2018": "'",  # '
    "\u2019": "'",  # '
    "\u201c": '"',  # "
    "\u201d": '"',  # "
    "\u2013": "-",  # –
    "\u2014": "-",  # —
    "\u2015": "-",  # ―
}

# Punctuation stripped during dedupe normalization.
_PUNCT = re.compile(r"[^\w\s]+")
_WS = re.compile(r"\s+")


def _clamp(value, lo, hi):
    """Clamp a number (int/float) to [lo, hi], returning an int."""
    return int(max(lo, min(hi, value)))


def _to_int(value, default=0):
    """Model output has typed integer fields; never coerce booleans or NaN."""
    return value if type(value) is int else default


def sanitize_text(text):
    """Reduce a fact text to printable ASCII, <= 200 chars.

    Curly quotes become straight ones, en/em dashes become '-', newlines and
    other control characters become spaces, everything outside printable
    ASCII (32..126) is dropped, whitespace runs collapse to single spaces,
    and the result is truncated to 200 chars.
    """
    if not isinstance(text, str):
        return ""
    s = text.translate(str.maketrans(_CHAR_MAP))
    s = "".join(c if 32 <= ord(c) < 127 else " " for c in s)
    s = _WS.sub(" ", s).strip()
    return s[:_MAX_TEXT]


def extraction_messages(npc_name, player_name, player_line, npc_line):
    """Chat messages (system + user) asking the LLM for the section 3 JSON object.

    Returns a list of {"role", "content"} dicts ready to hand to the LLM
    caller. The prompt names both speakers and quotes both lines, and spells
    out the exact JSON shape including kinds, importance, secret and the
    trust/fear relationship deltas.
    """
    kinds = " | ".join(KINDS)
    system = (
        "You extract durable facts from one conversation between an NPC and "
        "the player of a post-nuclear world. Reply with ONE JSON object and "
        "nothing else, shaped exactly like this:\n"
        '{"facts": [{"kind": "promise", "text": "The player promised to bring Vic a radio part.", '
        '"importance": 4, "secret": false}], "relationship": {"trust": 1, "fear": 0}}\n'
        "Rules: kind must be one of " + kinds + ". importance is an integer 1-5. "
        "At most 3 facts; only what was actually said or clearly implied. "
        "text is third person, about this NPC and the player, at most 200 characters. "
        "A fact with kind \"secret\" is always secret; mark any confidential fact secret too. "
        "relationship holds trust and fear deltas, each an integer from -2 to +2; "
        "use 0 when the talk does not move either. "
        "Facts with kind \"claim\" are things the player SAID: they are claims, "
        "never truth — the world's own story overrides them."
    )
    user = (
        "NPC: " + str(npc_name) + "\n"
        "Player: " + str(player_name) + "\n"
        "Player said: " + str(player_line) + "\n"
        "NPC replied: " + str(npc_line) + "\n"
        "Extract the facts (if any) and the trust/fear relationship change as the JSON object above."
    )
    return [
        {"role": "system", "content": system},
        {"role": "user", "content": user},
    ]


def _find_json_object(text):
    """Locate and decode the first balanced JSON object in free text.

    Tolerant of prose around the object, of ```json fences, and of trailing
    text after the closing brace. Returns a dict, or None if no object parses.
    """
    if not isinstance(text, str) or not text:
        return None
    stripped = text.strip()
    # Fast path: the whole thing is (or starts as) an object.
    try:
        obj = json.loads(stripped)
        if isinstance(obj, dict):
            return obj
    except ValueError:
        pass
    # Scan for the first '{' that starts a decodable object.
    decoder = json.JSONDecoder()
    for i, ch in enumerate(stripped):
        if ch != "{":
            continue
        try:
            obj, _end = decoder.raw_decode(stripped[i:])
        except ValueError:
            continue
        if isinstance(obj, dict):
            return obj
    return None


def _parse_facts(raw):
    """Validate the facts array; drop bad kinds, empty texts, keep <= 3."""
    if not isinstance(raw, list):
        return []
    facts = []
    for item in raw:
        if not isinstance(item, dict):
            continue
        kind = item.get("kind")
        if not isinstance(kind, str) or kind not in KINDS:
            continue
        text = sanitize_text(item.get("text"))
        if not text:
            continue
        importance = _clamp(_to_int(item.get("importance"), 3), 1, 5)
        secret = bool(item.get("secret", False))
        if kind == "secret":  # a secret fact is always secret
            secret = True
        facts.append(
            {"kind": kind, "text": text, "importance": importance, "secret": secret}
        )
        if len(facts) >= _MAX_FACTS:
            break
    return facts


def _parse_relationship(raw):
    """Validate the relationship deltas; each clamped to -2..+2."""
    trust = _to_int(raw.get("trust"), 0) if isinstance(raw, dict) else 0
    fear = _to_int(raw.get("fear"), 0) if isinstance(raw, dict) else 0
    return {
        "trust": _clamp(trust, _DELTA_MIN, _DELTA_MAX),
        "fear": _clamp(fear, _DELTA_MIN, _DELTA_MAX),
    }


def parse_extraction(text):
    """Parse LLM output into (facts, relationship).

    Tolerant of surrounding prose and ```json fences. Malformed input yields
    ([], {"trust": 0, "fear": 0}). Every kept fact has exactly the keys
    kind/text/importance/secret; importance is clamped 1-5, text sanitized to
    printable ASCII of at most 200 chars; kind 'secret' is always secret.
    """
    obj = _find_json_object(text)
    if obj is None:
        return [], {"trust": 0, "fear": 0}
    facts = _parse_facts(obj.get("facts"))
    relationship = _parse_relationship(obj.get("relationship"))
    return facts, relationship


def _normalize(text):
    """Dedupe key: lowercase, punctuation removed, whitespace collapsed."""
    if not isinstance(text, str):
        return ""
    t = _PUNCT.sub(" ", text.lower())
    return _WS.sub(" ", t).strip()


def dedupe(existing_texts, new_facts):
    """Drop new facts equal to or contained in (or containing) existing ones.

    Comparison is on normalized text (lowercase, punctuation removed, spaces
    collapsed). The same containment rule is applied among the new facts
    themselves, first one wins. Returns the kept fact dicts, in input order.
    """
    existing_norm = [n for n in (_normalize(t) for t in existing_texts) if n]
    kept = []
    kept_norm = []
    for fact in new_facts:
        norm = _normalize(fact.get("text", ""))
        if not norm:
            continue
        if any(
            norm == e or norm in e or e in norm
            for e in existing_norm
        ):
            continue
        if any(
            norm == k or norm in k or k in norm for k in kept_norm
        ):
            continue
        kept.append(fact)
        kept_norm.append(norm)
    return kept


def sum_relationship(deltas):
    """Sum relationship deltas, clamping each axis to -10..+10."""
    trust = sum(_to_int(d.get("trust"), 0) for d in deltas if isinstance(d, dict))
    fear = sum(_to_int(d.get("fear"), 0) for d in deltas if isinstance(d, dict))
    return {
        "trust": _clamp(trust, _SUM_MIN, _SUM_MAX),
        "fear": _clamp(fear, _SUM_MIN, _SUM_MAX),
    }


def relationship_words(rel):
    """Render a relationship as one short English sentence with distinct strengths."""
    parts = []
    trust = _clamp(_to_int(rel.get("trust"), 0), _SUM_MIN, _SUM_MAX)
    fear = _clamp(_to_int(rel.get("fear"), 0), _SUM_MIN, _SUM_MAX)

    if trust >= 8:
        parts.append("you deeply trust them")
    elif trust >= 5:
        parts.append("you trust them a lot")
    elif trust >= 2:
        parts.append("you trust them somewhat")
    elif trust == 0:
        pass
    elif trust >= -3:
        parts.append("you have little trust in them")
    elif trust >= -6:
        parts.append("you distrust them")
    else:
        parts.append("you deeply distrust them")

    if fear >= 8:
        parts.append("you are deeply afraid of them")
    elif fear >= 5:
        parts.append("you are afraid of them")
    elif fear >= 2:
        parts.append("you are a little afraid of them")
    elif fear == 0:
        pass
    elif fear >= -3:
        parts.append("you are no longer afraid of them")
    elif fear >= -6:
        parts.append("you are not afraid of them")
    else:
        parts.append("you have no fear of them")

    if not parts:
        return "You neither trust nor fear them; you keep your distance."
    # Parts read as predicates of "you" ("you trust them"); join without the
    # leading "You " so the sentence stays a single, well-formed one.
    return ", and ".join(parts).capitalize() + "."


def select_facts(rows, n):
    """Pick up to n fact payloads by importance desc, then seq desc (newest first)."""
    if n <= 0:
        return []
    scored = []
    for row in rows:
        if not isinstance(row, dict):
            continue
        payload = row.get("payload")
        if not isinstance(payload, dict):
            continue
        try:
            importance = int(payload.get("importance", 0))
            seq = int(row.get("seq", 0))
        except (TypeError, ValueError):
            continue
        scored.append((importance, seq, payload))
    scored.sort(key=lambda item: (item[0], item[1]), reverse=True)
    return [payload for _importance, _seq, payload in scored[:n]]


def prompt_lines(facts):
    """Render selected facts as prompt lines; claims are marked unverified.

    One line per fact: a dash, a short kind label, and the text. Facts with
    kind "claim" are explicitly presented as unverified player claims, never
    as truth.
    """
    lines = []
    for fact in facts:
        if not isinstance(fact, dict):
            continue
        text = fact.get("text", "")
        if not isinstance(text, str) or not text.strip():
            continue
        if fact.get("kind") == "claim":
            lines.append("- claim (unverified player claim, may be false): " + text)
        else:
            lines.append("- " + str(fact.get("kind", "info")) + ": " + text)
    return lines
