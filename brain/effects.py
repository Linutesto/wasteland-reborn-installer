"""effects: validation of LLM-proposed consequences against allowed_effects (SPEC.md section 5).

Pure, deterministic, stdlib-only. The brain proposes effects; the engine
re-validates and applies. This module keeps only effects whose type is in
`allowed_effects`, within the engine's own bounds, and whose relationship
gates pass. It also renders the allowed-effects prompt lines and the
JSON-schema fragment describing the response `effects` array.

Public API (tests are the contract):
    TYPES
    validate_effects(proposed, allowed, relationship, mood, active_quests=0) -> (kept, dropped)
    prompt_lines(allowed, relationship) -> list[str]
    response_schema_fragment(allowed) -> dict
"""

# The full effect vocabulary, in SPEC.md section 5 order.
TYPES = (
    "discount",
    "gift",
    "reveal_location",
    "side_quest",
    "complete_quest",
    "turn_hostile",
)

# Relationship gates (SPEC.md section 5).
_MIN_TRUST_DISCOUNT = 3
_MIN_TRUST_GIFT = 5
_MAX_TRUST_HOSTILE = -6

# Hard engine bounds for side_quest rewards/quantity.
_MAX_REWARD_CAPS = 9999
_MAX_REWARD_XP = 999
_MIN_QTY = 1
_MAX_QTY_FETCH_VISIT = 10

# Text limits for side_quest strings.
_MAX_TITLE = 60
_MAX_OBJECTIVE = 200


def _is_int(value):
    """True for real ints (bool is excluded on purpose)."""
    return isinstance(value, int) and not isinstance(value, bool)


def _clamp(value, low, high):
    return max(low, min(high, value))


def _reason(kind, why):
    """Build a short, stable reason string for the dropped list."""
    return "%s: %s" % (kind, why)


def _normalize_allowed(allowed):
    """Coerce the allowed dict into a safe mapping with defaults."""
    if not isinstance(allowed, dict):
        return {}
    return allowed


def _allowed_config(allowed, kind):
    """Return (present, config) for a kind. Config is a dict (may be empty)."""
    a = _normalize_allowed(allowed)
    if kind not in a:
        return False, {}
    cfg = a[kind]
    if cfg is None:
        cfg = {}
    if not isinstance(cfg, dict):
        cfg = {}
    return True, cfg


def _name_match(needle, haystacks):
    """Case-insensitive name match against a list of strings. Returns the
    canonical spelling from haystacks or None."""
    if not isinstance(needle, str):
        return None
    want = needle.strip().lower()
    for hay in haystacks or []:
        if isinstance(hay, str) and hay.strip().lower() == want:
            return hay
    return None


def _validate_discount(cfg, rel, effect, dropped):
    max_pct = cfg.get("max_percent")
    if not _is_int(max_pct) or max_pct < 1:
        dropped.append(_reason("discount", "no max_percent"))
        return None
    if rel.get("trust", 0) < _MIN_TRUST_DISCOUNT:
        dropped.append(_reason("discount", "trust below 3"))
        return None
    percent = effect.get("percent")
    if not _is_int(percent):
        dropped.append(_reason("discount", "percent missing or not an int"))
        return None
    if percent <= 0:
        dropped.append(_reason("discount", "percent below 1"))
        return None
    percent = _clamp(percent, 1, min(max_pct, 20))
    if percent < 1:
        dropped.append(_reason("discount", "percent below 1"))
        return None
    return {"type": "discount", "percent": percent}


def _validate_gift(cfg, rel, effect, dropped):
    items = cfg.get("items")
    if not isinstance(items, list) or not items:
        dropped.append(_reason("gift", "no items offered"))
        return None
    if rel.get("trust", 0) < _MIN_TRUST_GIFT:
        dropped.append(_reason("gift", "trust below 5"))
        return None
    pid = effect.get("pid")
    if not _is_int(pid):
        dropped.append(_reason("gift", "pid missing or not an int"))
        return None
    match = None
    for it in items:
        if isinstance(it, dict) and it.get("pid") == pid:
            match = it
            break
    if match is None:
        dropped.append(_reason("gift", "pid not offered"))
        return None
    max_qty = match.get("max_qty")
    if not _is_int(max_qty) or max_qty < 1:
        max_qty = 1
    qty = effect.get("qty", 1)
    if not _is_int(qty):
        dropped.append(_reason("gift", "qty is not an int"))
        return None
    qty = _clamp(qty, 1, max_qty)
    return {"type": "gift", "pid": pid, "qty": qty}


def _validate_reveal(cfg, effect, dropped):
    names = cfg.get("names")
    if not isinstance(names, list) or not names:
        dropped.append(_reason("reveal_location", "no names allowed"))
        return None
    name = effect.get("name")
    canonical = _name_match(name, names)
    if canonical is None:
        dropped.append(_reason("reveal_location", "name not allowed"))
        return None
    return {"type": "reveal_location", "name": canonical}


def _validate_side_quest(cfg, rel, effect, active, dropped):
    if active >= 1:
        dropped.append(_reason("side_quest", "an active side quest already exists"))
        return None
    title = effect.get("title")
    objective = effect.get("objective")
    if not isinstance(title, str) or not title.strip():
        dropped.append(_reason("side_quest", "title missing or empty"))
        return None
    if not isinstance(objective, str) or not objective.strip():
        dropped.append(_reason("side_quest", "objective missing or empty"))
        return None
    title = title[:_MAX_TITLE]
    objective = objective[:_MAX_OBJECTIVE]

    kind = effect.get("kind")
    if kind not in ("fetch", "visit"):
        dropped.append(_reason("side_quest", "kind must be fetch or visit"))
        return None

    if kind == "fetch":
        fetch_items = cfg.get("fetch_items") or []
        pids = [it.get("pid") for it in fetch_items if isinstance(it, dict)]
        pid = effect.get("pid")
        if not _is_int(pid) or pid not in pids:
            dropped.append(_reason("side_quest", "fetch pid not allowed"))
            return None
        qty = effect.get("qty", 1)
        if not _is_int(qty):
            qty = 1
        qty = _clamp(qty, _MIN_QTY, _MAX_QTY_FETCH_VISIT)
        body = {"kind": "fetch", "pid": pid, "qty": qty}
    else:
        visit_locations = cfg.get("visit_locations") or []
        location = effect.get("location")
        canonical = _name_match(location, visit_locations)
        if canonical is None:
            dropped.append(_reason("side_quest", "visit location not allowed"))
            return None
        body = {"kind": "visit", "location": canonical}

    max_caps = cfg.get("max_caps", _MAX_REWARD_CAPS)
    max_xp = cfg.get("max_xp", _MAX_REWARD_XP)
    if not _is_int(max_caps) or max_caps < 0:
        max_caps = _MAX_REWARD_CAPS
    if not _is_int(max_xp) or max_xp < 0:
        max_xp = _MAX_REWARD_XP

    reward_caps = effect.get("reward_caps", 0)
    if not _is_int(reward_caps):
        reward_caps = 0
    reward_caps = _clamp(reward_caps, 0, max_caps)

    reward_xp = effect.get("reward_xp", 0)
    if not _is_int(reward_xp):
        reward_xp = 0
    reward_xp = _clamp(reward_xp, 0, max_xp)

    return {
        "type": "side_quest",
        "title": title,
        "objective": objective,
        "kind": kind,
        **body,
        "reward_caps": reward_caps,
        "reward_xp": reward_xp,
    }


def _validate_complete_quest(cfg, effect, dropped):
    ids = cfg.get("ids")
    if not isinstance(ids, list) or not ids:
        dropped.append(_reason("complete_quest", "no ids allowed"))
        return None
    qid = effect.get("id")
    if not isinstance(qid, str) or qid not in ids:
        dropped.append(_reason("complete_quest", "id not allowed"))
        return None
    return {"type": "complete_quest", "id": qid}


def _validate_turn_hostile(rel, mood, effect, dropped):
    if rel.get("trust", 0) > _MAX_TRUST_HOSTILE:
        dropped.append(_reason("turn_hostile", "trust above -6"))
        return None
    if mood != "hostile":
        dropped.append(_reason("turn_hostile", "mood not hostile"))
        return None
    return {"type": "turn_hostile"}


_VALIDATORS = {
    "discount": lambda cfg, rel, mood, eff, active, dropped: _validate_discount(cfg, rel, eff, dropped),
    "gift": lambda cfg, rel, mood, eff, active, dropped: _validate_gift(cfg, rel, eff, dropped),
    "reveal_location": lambda cfg, rel, mood, eff, active, dropped: _validate_reveal(cfg, eff, dropped),
    "side_quest": lambda cfg, rel, mood, eff, active, dropped: _validate_side_quest(cfg, rel, eff, active, dropped),
    "complete_quest": lambda cfg, rel, mood, eff, active, dropped: _validate_complete_quest(cfg, eff, dropped),
    "turn_hostile": lambda cfg, rel, mood, eff, active, dropped: _validate_turn_hostile(rel, mood, eff, dropped),
}


def validate_effects(proposed, allowed, relationship, mood, active_quests=0):
    """Validate a list of proposed effect dicts against the engine's
    allowed_effects and the current relationship/mood state.

    Returns (kept, dropped):
      kept    — up to 2 effects, in input order, with only the documented
                keys and engine-authorized spellings/bounds.
      dropped — a list of short reason strings, one per effect dropped.

    A non-list `proposed` returns ([], []).
    """
    if not isinstance(proposed, list):
        return ([], [])

    allowed = allowed if isinstance(allowed, dict) else {}
    rel = relationship if isinstance(relationship, dict) else {}
    rel = {key: rel.get(key, 0) if _is_int(rel.get(key, 0)) else 0 for key in ("trust", "fear")}
    active = active_quests if _is_int(active_quests) and active_quests >= 0 else 0

    kept = []
    dropped = []

    for eff in proposed:
        if not isinstance(eff, dict):
            dropped.append("unknown: not an object")
            continue
        kind = eff.get("type")
        if kind not in TYPES:
            dropped.append("unknown: type %r" % (kind,))
            continue

        present, cfg = _allowed_config(allowed, kind)
        if not present:
            dropped.append("%s: not allowed" % kind)
            continue

        if len(kept) >= 2:
            dropped.append("%s: over the 2-effect limit" % kind)
            continue

        validator = _VALIDATORS[kind]
        result = validator(cfg, rel, mood, eff, active, dropped)
        if result is None:
            continue

        kept.append(result)
        if kind == "side_quest":
            # Consume the single active-quest slot immediately so a second
            # side_quest in the same proposal is rejected even if the first
            # was also valid.
            active = 1

    return (kept, dropped)


def prompt_lines(allowed, relationship):
    """Render one line per allowed effect describing the effect and its
    bounds, in TYPES order. Empty/missing allowed returns [].

    Only effects actually present in `allowed` appear in the output.
    """
    allowed = allowed if isinstance(allowed, dict) else {}
    rel = relationship if isinstance(relationship, dict) else {}

    lines = []
    for kind in TYPES:
        present, cfg = _allowed_config(allowed, kind)
        if not present:
            continue

        if kind == "discount":
            max_pct = cfg.get("max_percent")
            lines.append(
                "discount: give the player a barter discount of at most %s%% (needs trust >= 3)."
                % (max_pct if _is_int(max_pct) else "N/A")
            )
        elif kind == "gift":
            items = cfg.get("items") or []
            names = [it.get("name") for it in items if isinstance(it, dict) and it.get("name")]
            lines.append(
                "gift: give the player one of: %s (needs trust >= 5)."
                % (", ".join(names) if names else "nothing")
            )
        elif kind == "reveal_location":
            names = cfg.get("names") or []
            lines.append(
                "reveal_location: tell the player about one of: %s."
                % (", ".join(str(n) for n in names) if names else "nothing")
            )
        elif kind == "side_quest":
            max_caps = cfg.get("max_caps")
            max_xp = cfg.get("max_xp")
            fetch_pids = [it.get("pid") for it in (cfg.get("fetch_items") or []) if isinstance(it, dict)]
            visit_locs = cfg.get("visit_locations") or []
            lines.append(
                "side_quest: propose a fetch quest for one of pids %s (qty 1-10) "
                "or a visit to one of: %s; rewards at most %s caps and %s xp "
                "(only if no active side quest yet)."
                % (
                    fetch_pids if fetch_pids else "none",
                    ", ".join(str(n) for n in visit_locs) if visit_locs else "none",
                    max_caps if _is_int(max_caps) else "N/A",
                    max_xp if _is_int(max_xp) else "N/A",
                )
            )
        elif kind == "complete_quest":
            ids = cfg.get("ids") or []
            lines.append(
                "complete_quest: mark one of these quests complete: %s."
                % (", ".join(str(i) for i in ids) if ids else "none")
            )
        elif kind == "turn_hostile":
            lines.append(
                "turn_hostile: the NPC attacks (needs trust <= -6 AND mood 'hostile')."
            )
    return lines


def response_schema_fragment(allowed):
    """Return a JSON-schema fragment for the response `effects` field:
    an array of effect objects, at most 2, with one branch per allowed kind."""
    allowed = allowed if isinstance(allowed, dict) else {}
    rel = None  # schema does not depend on relationship

    defs = []
    for kind in TYPES:
        present, _cfg = _allowed_config(allowed, kind)
        if not present:
            continue
        if kind == "discount":
            defs.append({
                "type": "object",
                "required": ["type", "percent"],
                "properties": {
                    "type": {"const": "discount"},
                    "percent": {"type": "integer", "minimum": 1},
                },
                "additionalProperties": False,
            })
        elif kind == "gift":
            defs.append({
                "type": "object",
                "required": ["type", "pid"],
                "properties": {
                    "type": {"const": "gift"},
                    "pid": {"type": "integer"},
                    "qty": {"type": "integer", "minimum": 1},
                },
                "additionalProperties": False,
            })
        elif kind == "reveal_location":
            defs.append({
                "type": "object",
                "required": ["type", "name"],
                "properties": {
                    "type": {"const": "reveal_location"},
                    "name": {"type": "string", "minLength": 1},
                },
                "additionalProperties": False,
            })
        elif kind == "side_quest":
            defs.append({
                "type": "object",
                "required": ["type", "title", "objective", "kind"],
                "properties": {
                    "type": {"const": "side_quest"},
                    "title": {"type": "string", "minLength": 1, "maxLength": _MAX_TITLE},
                    "objective": {"type": "string", "minLength": 1, "maxLength": _MAX_OBJECTIVE},
                    "kind": {"enum": ["fetch", "visit"]},
                    "pid": {"type": "integer"},
                    "qty": {"type": "integer", "minimum": 1, "maximum": _MAX_QTY_FETCH_VISIT},
                    "location": {"type": "string", "minLength": 1},
                    "reward_caps": {"type": "integer", "minimum": 0},
                    "reward_xp": {"type": "integer", "minimum": 0},
                },
                "additionalProperties": False,
            })
        elif kind == "complete_quest":
            defs.append({
                "type": "object",
                "required": ["type", "id"],
                "properties": {
                    "type": {"const": "complete_quest"},
                    "id": {"type": "string", "minLength": 1},
                },
                "additionalProperties": False,
            })
        elif kind == "turn_hostile":
            defs.append({
                "type": "object",
                "required": ["type"],
                "properties": {
                    "type": {"const": "turn_hostile"},
                },
                "additionalProperties": False,
            })

    return {
        "type": "array",
        "maxItems": 2,
        "items": {"anyOf": defs} if defs else {"type": "object"},
    }


def validate_allowed(allowed):
    """Fail closed on malformed optional engine bounds before prompting or validating."""
    if not isinstance(allowed, dict):
        return {}
    result = {}
    def names(value):
        return [s for s in value[:64] if isinstance(s, str) and s.strip() and len(s) <= 300] if isinstance(value, list) else []
    def items(value, gift=False):
        out = []
        for item in value[:64] if isinstance(value, list) else []:
            if not isinstance(item, dict) or not _is_int(item.get('pid')) or not 0 <= item['pid'] <= 2147483647:
                continue
            if not isinstance(item.get('name'), str) or not item['name'].strip():
                continue
            entry = {'pid': item['pid'], 'name': item['name'][:300]}
            if gift:
                qty = item.get('max_qty')
                if not _is_int(qty) or qty <= 0:
                    continue
                entry['max_qty'] = min(qty, 10)
            out.append(entry)
        return out
    for kind in TYPES:
        cfg = allowed.get(kind)
        if not isinstance(cfg, dict):
            continue
        if kind == 'discount':
            bound = cfg.get('max_percent')
            if _is_int(bound) and bound > 0:
                result[kind] = {'max_percent': min(bound, 20)}
        elif kind == 'gift':
            offered = items(cfg.get('items'), True)
            if offered:
                result[kind] = {'items': offered}
        elif kind == 'reveal_location':
            offered = names(cfg.get('names'))
            if offered:
                result[kind] = {'names': offered}
        elif kind == 'side_quest':
            caps, xp = cfg.get('max_caps'), cfg.get('max_xp')
            if not _is_int(caps) or not _is_int(xp) or caps < 0 or xp < 0:
                continue
            result[kind] = {'max_caps': min(caps, 200), 'max_xp': min(xp, 100),
                            'fetch_items': items(cfg.get('fetch_items')),
                            'visit_locations': names(cfg.get('visit_locations'))}
        elif kind == 'complete_quest':
            ids = names(cfg.get('ids'))
            if ids:
                result[kind] = {'ids': ids}
        elif kind == 'turn_hostile':
            result[kind] = {}
    return result
