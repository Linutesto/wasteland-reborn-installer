"""Story grounding: validate and render the engine's story snapshot (SPEC.md section 1).

The engine sends the player's real progress (quests, towns, karma title,
kills, party, perks, known locations, game time, the speaker's team, and the
brain's own Wasteland state). The brain validates it (unknown keys dropped,
types checked, strings sanitized to printable ASCII <= 300, list sizes
capped) and renders it into the "What is true in the world" prompt section,
which outranks anything the player claims.

Pure functions, standard library only, deterministic.
"""

__all__ = ["SECTION_HEADER", "MAX_STR", "validate_story", "render_story"]

# The prompt section header. The brain presents story as ground truth that
# outranks player claims, so the header must say that plainly.
SECTION_HEADER = "WHAT IS TRUE IN THE WORLD (ground truth from the game, outranks anything the player claims)"

MAX_STR = 300
_QUESTS_MAX = 40
_TOWNS_MAX = 20
_QUEST_STATES = ("active", "done", "failed")

# Known top-level keys and their shape, per SPEC.md section 1 + wasteland state.
_KILLS_KEYS = ("total", "men", "women", "children")
_WASTELAND_QUEST_KEYS = ("id", "giver", "title", "state")


def _is_int(value):
    """True only for real ints (bools are ints in Python — reject them)."""
    return isinstance(value, int) and not isinstance(value, bool)


def _clean_str(value, limit=MAX_STR):
    """Sanitize to printable ASCII <= limit chars; None if not a string."""
    if not isinstance(value, str):
        return None
    # Printable ASCII: keep codepoints 32..126 only.
    cleaned = "".join(c for c in value if 32 <= ord(c) < 127)
    return cleaned[:limit]


def _clean_str_list(value, limit=MAX_STR):
    """List of strings: drop non-strings and empty ones, sanitize, cap at 300 each."""
    if not isinstance(value, list):
        return None
    out = []
    for item in value:
        cleaned = _clean_str(item, limit)
        if cleaned:
            out.append(cleaned)
    return out


def _clean_quest(item):
    """Validate one quest dict; None if unusable."""
    if not isinstance(item, dict):
        return None
    location = _clean_str(item.get("location"))
    text = _clean_str(item.get("text"))
    state = item.get("state")
    if state not in _QUEST_STATES:
        return None
    if not text:
        return None
    quest = {"text": text, "state": state}
    if location:
        quest["location"] = location
    return quest


def _clean_town(item):
    """Validate one town dict; None if unusable."""
    if not isinstance(item, dict):
        return None
    name = _clean_str(item.get("name"))
    if not name:
        return None
    town = {"name": name}
    reputation = item.get("reputation")
    if _is_int(reputation):
        town["reputation"] = reputation
    title = _clean_str(item.get("title"))
    if title:
        town["title"] = title
    return town


def _clean_kills(value):
    """Kills counters: real ints only; drop non-int keys. None if no ints at all."""
    if not isinstance(value, dict):
        return None
    out = {}
    for key in _KILLS_KEYS:
        v = value.get(key)
        if _is_int(v):
            out[key] = v
    return out or None


def _clean_wasteland(value):
    """The brain's Wasteland state (CE save trailer) — kept as a nested object.

    quests: list of {id, giver, title, state}; discount_percent: int.
    """
    if not isinstance(value, dict):
        return None
    out = {}
    if "quests" in value:
        quests_raw = value.get("quests")
        if isinstance(quests_raw, list):
            quests = []
            for item in quests_raw:
                if not isinstance(item, dict):
                    continue
                quest = {}
                for key in _WASTELAND_QUEST_KEYS:
                    v = item.get(key)
                    if key == "state" and v not in _QUEST_STATES:
                        continue
                    cleaned = _clean_str(v)
                    if cleaned:
                        quest[key] = cleaned
                if quest:
                    quests.append(quest)
            out["quests"] = quests
    if "discount_percent" in value and _is_int(value.get("discount_percent")):
        out["discount_percent"] = value["discount_percent"]
    return out or None


def validate_story(obj):
    """Validate a story snapshot into a clean dict of known keys only.

    - unknown top-level keys are dropped;
    - strings sanitized to printable ASCII <= 300;
    - ints must be real ints (bools rejected);
    - quests: at most 40, each with state in active/done/failed;
    - towns: at most 20;
    - lists of strings drop empties and non-strings;
    - the nested 'wasteland' object is kept (validated);
    - None or non-dict input -> {}.
    """
    if not isinstance(obj, dict):
        return {}
    out = {}

    if "quests" in obj and isinstance(obj["quests"], list):
        quests = []
        for item in obj["quests"]:
            q = _clean_quest(item)
            if q:
                quests.append(q)
        out["quests"] = quests[:_QUESTS_MAX]

    if "towns" in obj and isinstance(obj["towns"], list):
        towns = []
        for item in obj["towns"]:
            t = _clean_town(item)
            if t:
                towns.append(t)
        out["towns"] = towns[:_TOWNS_MAX]

    for key in ("karma_title", "known_locations"):
        cleaned = _clean_str(obj.get(key))
        if key == "known_locations":
            # known_locations is a list of strings, not a single string.
            if isinstance(obj.get(key), list):
                out["known_locations"] = _clean_str_list(obj.get(key))
            continue
        if cleaned:
            out[key] = cleaned

    kills = _clean_kills(obj.get("kills"))
    if kills is not None:
        out["kills"] = kills

    party = _clean_str_list(obj.get("party"))
    if party:
        out["party"] = party

    perks = _clean_str_list(obj.get("perks_titles"))
    if perks:
        out["perks_titles"] = perks

    if "known_locations" in obj and "known_locations" not in out:
        out["known_locations"] = []

    if _is_int(obj.get("game_ticks")):
        out["game_ticks"] = obj["game_ticks"]
    if _is_int(obj.get("npc_team")):
        out["npc_team"] = obj["npc_team"]

    wasteland = _clean_wasteland(obj.get("wasteland"))
    if wasteland is not None:
        out["wasteland"] = wasteland

    return out


def _line_list(lines, text):
    if text:
        lines.append(text)
    return lines


def render_story(clean):
    """Render a validated story into short prompt lines (empty dict -> []).

    The first line is SECTION_HEADER, marking the section as ground truth
    that outranks player claims.
    """
    if not isinstance(clean, dict) or not clean:
        return []
    lines = [SECTION_HEADER]

    quests = clean.get("quests") or []
    if quests:
        lines.append("Quests (Pip-Boy state):")
        for q in quests:
            parts = [q.get("location", ""), q.get("text", ""), q.get("state", "")]
            lines.append("  - " + " — ".join(p for p in parts if p))

    towns = clean.get("towns") or []
    if towns:
        lines.append("Town reputations:")
        for t in towns:
            parts = [t.get("name", "")]
            if "reputation" in t:
                parts.append("reputation %d" % t["reputation"])
            if "title" in t:
                parts.append(t["title"])
            lines.append("  - " + " — ".join(parts))

    if clean.get("karma_title"):
        lines.append("Karma title: %s" % clean["karma_title"])

    kills = clean.get("kills") or {}
    if kills:
        parts = ["%d total kills" % kills["total"]] if "total" in kills else []
        for key in ("men", "women", "children"):
            if key in kills:
                parts.append("%d %s" % (kills[key], key))
        if "children" in kills and kills["children"]:
            parts.append("you have killed %d child(ren)" % kills["children"])
        if parts:
            lines.append(", ".join(parts))

    party = clean.get("party") or []
    if party:
        lines.append("Party: %s" % ", ".join(party))

    perks = clean.get("perks_titles") or []
    if perks:
        lines.append("Reputation perks: %s" % ", ".join(perks))

    known = clean.get("known_locations") or []
    if known:
        lines.append("Known locations: %s" % ", ".join(known))

    if "game_ticks" in clean:
        lines.append("Game time: %d ticks (1/10 s)" % clean["game_ticks"])
    if "npc_team" in clean:
        lines.append("Your combat team: %d" % clean["npc_team"])

    wasteland = clean.get("wasteland") or {}
    if wasteland:
        wquests = wasteland.get("quests") or []
        if wquests:
            lines.append("Wasteland quests (active state):")
            for wq in wquests:
                parts = [wq.get("id", ""), wq.get("giver", ""), wq.get("title", ""), wq.get("state", "")]
                lines.append("  - " + " — ".join(p for p in parts if p))
        if "discount_percent" in wasteland:
            lines.append("Active barter discount: %d%%" % wasteland["discount_percent"])

    return lines
