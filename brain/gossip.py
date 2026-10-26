"""Gossip: who hears which fact, when (SPEC.md section 4).

A non-secret fact with importance >= 3 becomes a rumor for other NPCs:

- same map (non-empty equal map): visible after fact.game_ticks + SAME_MAP_DELAY
  (1 day of 10-decisecond ticks);
- same team (non-None equal team): anywhere, after fact.game_ticks + SAME_TEAM_DELAY
  (3 days);
- never to the NPC who said it; never to a fact that is secret or
  importance < 3.

Rumors are computed at query time (no copies), so reloading a save rewinds
them too. Pure functions, standard library only, deterministic.
"""

__all__ = [
    "SAME_MAP_DELAY",
    "SAME_TEAM_DELAY",
    "MIN_IMPORTANCE",
    "rumors_for",
    "prompt_lines",
]

# One in-game day: 86400 seconds * 10 ticks/second (ticks are 1/10 s).
SAME_MAP_DELAY = 864000
# Three in-game days: same map, anywhere in the world.
SAME_TEAM_DELAY = 3 * SAME_MAP_DELAY
# Only facts at or above this importance spread as rumors (SPEC section 4).
MIN_IMPORTANCE = 3

_RUMOR_LIMIT = 4


def _payload(row):
    """Return the row's payload dict, or None if the row is not a usable fact."""
    if not isinstance(row, dict):
        return None
    payload = row.get("payload")
    return payload if isinstance(payload, dict) else None


def _eligible(row, me, now_ticks):
    """Return the rumor dict for this row, or None if it is not a rumor for `me` now.

    Rules checked, in order:
    - a fact row with a non-empty text payload (never own facts, never secrets,
      never importance < MIN_IMPORTANCE);
    - visibility: same map (non-empty and equal) after SAME_MAP_DELAY ticks,
      or same team (non-None and equal) after SAME_TEAM_DELAY ticks —
      missing/empty values on either side never count as a match.
    """
    if not isinstance(me, dict):
        return None
    payload = _payload(row)
    if payload is None:
        return None
    if row.get("npc_id") == me.get("npc_id"):
        return None
    if payload.get("secret"):
        return None
    try:
        importance = int(payload.get("importance", 0))
    except (TypeError, ValueError):
        return None
    if importance < MIN_IMPORTANCE:
        return None
    text = payload.get("text")
    if not isinstance(text, str) or not text:
        return None
    try:
        fact_ticks = int(row.get("game_ticks", 0))
    except (TypeError, ValueError):
        return None

    visible = False
    my_map = me.get("map")
    row_map = row.get("map")
    if my_map and row_map and my_map == row_map and fact_ticks + SAME_MAP_DELAY <= now_ticks:
        visible = True
    if not visible:
        my_team = me.get("team")
        row_team = row.get("team")
        if my_team is not None and row_team is not None and my_team == row_team \
                and fact_ticks + SAME_TEAM_DELAY <= now_ticks:
            visible = True
    if not visible:
        return None

    name = row.get("npc_name")
    if not isinstance(name, str) or not name:
        name = row.get("npc_id")
    return {"source": name, "text": text, "seq": row.get("seq")}


def rumors_for(me, fact_rows, now_ticks, limit=4):
    """Rumors `me` has heard by now_ticks, best first.

    me: dict with npc_id, map, team.
    fact_rows: rows with seq, npc_id, npc_name, game_ticks, map, team,
        payload{kind, text, importance, secret}.
    now_ticks: current gameTimeGetTime() (1/10 s since game start), or None.
    limit: max rumors (default 4).

    Returns a list of {'source', 'text', 'seq'} dicts, sorted by importance
    descending then seq descending. Identical rumor text is deduplicated,
    keeping the best row. now_ticks None -> [].
    """
    if not isinstance(fact_rows, list) or now_ticks is None:
        return []
    try:
        now = int(now_ticks)
    except (TypeError, ValueError):
        return []
    try:
        max_items = max(0, int(limit))
    except (TypeError, ValueError):
        max_items = _RUMOR_LIMIT

    candidates = []
    for row in fact_rows:
        rumor = _eligible(row, me, now)
        if rumor is not None:
            payload = _payload(row)
            try:
                importance = int(payload.get("importance", 0))
            except (TypeError, ValueError):
                importance = 0
            candidates.append((importance, rumor))

    # Sort by importance desc, then seq desc (newest wins ties).
    candidates.sort(key=lambda item: (item[0], _seq_of(item[1])), reverse=True)

    seen_text = set()
    out = []
    for importance, rumor in candidates:
        if rumor["text"] in seen_text:
            continue
        seen_text.add(rumor["text"])
        out.append({"source": rumor["source"], "text": rumor["text"], "seq": rumor["seq"]})
        if len(out) >= max_items:
            break
    return out


def _seq_of(rumor):
    """Safe seq for sorting: anything non-numeric sorts as the oldest."""
    seq = rumor.get("seq")
    if isinstance(seq, bool) or not isinstance(seq, (int, float)):
        return float("-inf")
    return seq


def prompt_lines(rumors):
    """Render rumors as prompt lines: 'You heard from <source>: <text>'."""
    lines = []
    if not isinstance(rumors, list):
        return lines
    for rumor in rumors:
        if not isinstance(rumor, dict):
            continue
        source = rumor.get("source") or "someone"
        text = rumor.get("text")
        if not text:
            continue
        lines.append("You heard from %s: %s" % (source, text))
    return lines
