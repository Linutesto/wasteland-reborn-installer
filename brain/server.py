#!/usr/bin/env python3
"""Wasteland Brain -- free-text NPC talk service for Fallout 2 CE.

Contract: docs/BRAIN-API.md (v1). Python 3 standard library only.

    python3 brain/server.py --host 127.0.0.1 --port 8820 \
        --llm http://127.0.0.1:8093 --db brain/brain.db

The model proposes, the engine disposes: nothing here changes game state.
"""

import argparse
import hashlib
import hmac
import http.server
import json
import os
import random
import re
import secrets
import signal
import sqlite3
import sys
import threading
import time
import unicodedata
import urllib.error
import urllib.parse
import urllib.request

from branch_memory import BranchMemory
import effects as story_effects
import facts as story_facts
import gossip as story_gossip
import story as story_snapshot
from story_runtime import StoryRuntime

API_V = 1
MAX_BODY = 64 * 1024
MAX_STR = 300
MAX_ARR = 64
MAX_SAY_OUT = 400
MAX_SUMMARY = 800
MOODS = ("friendly", "neutral", "wary", "hostile")
HISTORY_N = 8          # exchanges sent verbatim
SUMMARY_EVERY = 8      # summary refresh cadence (new exchanges)

HERE = os.path.dirname(os.path.abspath(__file__))

# What each engine intent means, for the system prompt. Unknown intents the
# engine sends still work; they just get a generic description.
INTENT_HELP = {
    "none": "just talking, no game action",
    "open_barter": "you start trading with the player now (only when they want "
                   "to trade/buy/sell or accept your offer to trade)",
    "end_talk": "the conversation ends now (player says goodbye, or you refuse "
                "to keep talking)",
    "join_party": "you agree to join the player's party",
    "leave_party": "you leave the player's party",
    "wait_here": "you agree to wait here",
    "follow": "you agree to follow the player",
    "attack": "you start a fight with the player (only if gravely provoked)",
    "refuse": "you decline what the player asked for",
}


# --------------------------------------------------------------------------
# config
# --------------------------------------------------------------------------

def _env_float(name, default):
    try:
        return float(os.environ.get(name, default))
    except ValueError:
        return float(default)


class Config:
    def __init__(self, **kw):
        self.host = "127.0.0.1"
        self.port = 8820
        self.llm_url = os.environ.get("BRAIN_LLM_URL", "http://127.0.0.1:8093")
        self.model = os.environ.get("BRAIN_LLM_MODEL", "qwen38")
        # "openai" = llama.cpp's /v1/chat/completions; "ollama" = Ollama's native /api/chat.
        self.llm_api = os.environ.get("BRAIN_LLM_API", "openai")
        # llama.cpp slot reserved for player conversations (-1 = any). The StarNet router keeps its traffic off it,
        # so crew jobs filling the other slots can no longer push NPC replies past the timeout into fallbacks.
        self.llm_slot = int(os.environ.get("BRAIN_LLM_SLOT", "3"))
        self.db_path = os.path.join(HERE, "brain.db")
        self.personas_dir = os.environ.get("BRAIN_PERSONAS", os.path.join(HERE, "personas"))
        self.log_dir = os.environ.get("BRAIN_LOG_DIR", os.path.join(HERE, "logs"))
        self.token = os.environ.get("BRAIN_TOKEN") or None
        self.token_file = os.environ.get("BRAIN_TOKEN_FILE", os.path.join(HERE, "token"))
        self.llm_timeout = _env_float("BRAIN_LLM_TIMEOUT", 25.0)
        self.summary_timeout = _env_float("BRAIN_SUMMARY_TIMEOUT", 60.0)
        self.summary_retry_s = _env_float("BRAIN_SUMMARY_RETRY", 120.0)
        self.health_ttl = 15.0
        self.health_timeout = 1.0
        self.log_prompts = os.environ.get("BRAIN_LOG_PROMPTS", "") not in ("", "0")
        self.max_tokens = 220
        self.temperature = 0.7
        for k, v in kw.items():
            if not hasattr(self, k):
                raise TypeError("unknown config key %r" % k)
            setattr(self, k, v)


def load_token(cfg):
    if cfg.token:
        return cfg.token
    path = cfg.token_file
    try:
        with open(path) as f:
            tok = f.read().strip()
        if tok:
            return tok
    except FileNotFoundError:
        pass
    tok = secrets.token_urlsafe(32)
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(fd, "w") as f:
        f.write(tok + "\n")
    os.chmod(path, 0o600)
    return tok


# --------------------------------------------------------------------------
# text sanitizing
# --------------------------------------------------------------------------

_TRANSLATE = {
    0x2018: "'", 0x2019: "'", 0x201A: "'", 0x201B: "'", 0x2032: "'", 0x0060: "'",
    0x201C: '"', 0x201D: '"', 0x201E: '"', 0x201F: '"', 0x2033: '"',
    0x00AB: '"', 0x00BB: '"',
    0x2010: "-", 0x2011: "-", 0x2012: "-", 0x2013: "-", 0x2014: "-",
    0x2015: "-", 0x2212: "-", 0x2043: "-",
    0x2026: "...", 0x2022: "-", 0x00B7: "-",
    0x00A0: " ", 0x2002: " ", 0x2003: " ", 0x2009: " ", 0x200A: " ",
    0x202F: " ", 0x3000: " ",
    0x200B: None, 0x200C: None, 0x200D: None, 0xFEFF: None,
    ord("\n"): " ", ord("\r"): " ", ord("\t"): " ",
}
_WS = re.compile(r"\s+")


def sanitize(text, limit=MAX_SAY_OUT):
    """Printable ASCII only (0x20-0x7E), single line, <= limit chars."""
    if not isinstance(text, str):
        text = "" if text is None else str(text)
    s = text.translate(_TRANSLATE)
    s = unicodedata.normalize("NFKD", s)          # e-acute -> e + combining mark
    s = "".join(c for c in s if " " <= c <= "~")  # drop everything else
    s = _WS.sub(" ", s).strip()
    if len(s) > limit:
        cut = s[: limit - 3]
        if " " in cut[limit // 2:]:
            cut = cut.rsplit(" ", 1)[0]
        s = cut.rstrip(" ,;:-") + "..."
    return s


def clean_say(text, npc_name):
    s = sanitize(text, limit=10_000)
    # Model sometimes prefixes its own name or wraps the line in quotes.
    for prefix in (npc_name, npc_name.split(" ")[0]):
        if prefix and s.lower().startswith(prefix.lower() + ":"):
            s = s[len(prefix) + 1:].strip()
    if len(s) >= 2 and s[0] == s[-1] == '"' and s.count('"') == 2:
        s = s[1:-1].strip()
    return sanitize(s)


# --------------------------------------------------------------------------
# request validation
# --------------------------------------------------------------------------

class Invalid(Exception):
    def __init__(self, msg, field):
        super().__init__(msg)
        self.msg = msg
        self.field = field


def _walk_limits(obj, path):
    if isinstance(obj, str):
        if len(obj) > MAX_STR:
            raise Invalid("string longer than %d chars" % MAX_STR, path)
    elif isinstance(obj, list):
        if len(obj) > MAX_ARR:
            raise Invalid("array longer than %d items" % MAX_ARR, path)
        for i, v in enumerate(obj):
            _walk_limits(v, "%s[%d]" % (path, i))
    elif isinstance(obj, dict):
        for k, v in obj.items():
            if len(k) > MAX_STR:
                raise Invalid("key longer than %d chars" % MAX_STR, path)
            _walk_limits(v, "%s.%s" % (path, k) if path else k)


def _is_int(v):
    return isinstance(v, int) and not isinstance(v, bool)


def _req(obj, key, path, kind):
    if key not in obj or obj[key] is None:
        raise Invalid("missing required field", path + key)
    v = obj[key]
    if kind == "int" and not _is_int(v):
        raise Invalid("must be an integer", path + key)
    if kind == "str":
        if not isinstance(v, str):
            raise Invalid("must be a string", path + key)
        if not v.strip():
            raise Invalid("must not be empty", path + key)
    if kind == "obj" and not isinstance(v, dict):
        raise Invalid("must be an object", path + key)
    if kind == "list" and not isinstance(v, list):
        raise Invalid("must be an array", path + key)
    return v


def _opt(obj, key, path, kind):
    if key not in obj or obj[key] is None:
        return None
    return _req(obj, key, path, kind) if kind != "str" else _opt_str(obj, key, path)


def _opt_str(obj, key, path):
    v = obj[key]
    if not isinstance(v, str):
        raise Invalid("must be a string", path + key)
    return v


def validate_talk(body):
    if not isinstance(body, dict):
        raise Invalid("body must be a JSON object", "")
    _walk_limits(body, "")
    v = _req(body, "v", "", "int")
    if v != API_V:
        raise Invalid("unsupported version (expected %d)" % API_V, "v")
    _req(body, "campaign", "", "str")
    _opt(body, "content", "", "str")
    npc = _req(body, "npc", "", "obj")
    _req(npc, "pid", "npc.", "int")
    _req(npc, "name", "npc.", "str")
    _opt(npc, "instance", "npc.", "str")
    _opt(npc, "description", "npc.", "str")
    for k in ("map",):
        _opt(npc, k, "npc.", "str")
    for k in ("party_member", "can_barter"):
        if k in npc and npc[k] is not None and not isinstance(npc[k], bool):
            raise Invalid("must be a boolean", "npc." + k)
    if npc.get("caps") is not None and not _is_int(npc["caps"]):
        raise Invalid("must be an integer", "npc.caps")
    inv = _opt(npc, "inventory", "npc.", "list")
    for i, it in enumerate(inv or []):
        p = "npc.inventory[%d]." % i
        if not isinstance(it, dict):
            raise Invalid("must be an object", p[:-1])
        _req(it, "name", p, "str")
        if it.get("qty") is not None and not _is_int(it["qty"]):
            raise Invalid("must be an integer", p + "qty")
        if it.get("pid") is not None and not _is_int(it["pid"]):
            raise Invalid("must be an integer", p + "pid")
    player = _req(body, "player", "", "obj")
    _req(player, "name", "player.", "str")
    for k in ("sex", "reputation"):
        _opt(player, k, "player.", "str")
    for k in ("level", "karma", "caps"):
        if player.get(k) is not None and not _is_int(player[k]):
            raise Invalid("must be an integer", "player." + k)
    st = _opt(player, "stats", "player.", "obj")
    for k, sv in (st or {}).items():
        if not _is_int(sv):
            raise Invalid("must be an integer", "player.stats." + k)
    world = _opt(body, "world", "", "obj") or {}
    for k in ("date", "time", "map_name"):
        _opt(world, k, "world.", "str")
    dialog = _opt(body, "dialog", "", "obj") or {}
    _opt(dialog, "reply", "dialog.", "str")
    opts = _opt(dialog, "options", "dialog.", "list")
    for i, o in enumerate(opts or []):
        if not isinstance(o, str):
            raise Invalid("must be a string", "dialog.options[%d]" % i)
    intents = _req(body, "allowed_intents", "", "list")
    if not intents:
        raise Invalid("must not be empty", "allowed_intents")
    for i, it in enumerate(intents):
        if not isinstance(it, str) or not it.strip():
            raise Invalid("must be a non-empty string", "allowed_intents[%d]" % i)
    _req(body, "say", "", "str")
    timeline = _opt(body, "timeline", "", "obj")
    if timeline is not None:
        if "branch" in timeline and (not isinstance(timeline["branch"], str) or len(timeline["branch"]) > 128):
            raise Invalid("must be a branch string", "timeline.branch")
        if "head" in timeline and (not _is_int(timeline["head"]) or not 0 <= timeline["head"] <= 9007199254740991):
            raise Invalid("must be a nonnegative sequence", "timeline.head")
        if "fork" in timeline and not isinstance(timeline["fork"], bool):
            raise Invalid("must be a boolean", "timeline.fork")
    _opt(body, "story", "", "obj")
    _opt(body, "allowed_effects", "", "obj")
    if "allowed_effects" in body:
        body["allowed_effects"] = story_effects.validate_allowed(body["allowed_effects"])
    if "story" in body:
        body["story"] = story_snapshot.validate_story(body["story"])
    return body


# --------------------------------------------------------------------------
# personas
# --------------------------------------------------------------------------

def load_personas(directory):
    by_id, by_pid = {}, {}
    for fn in sorted(os.listdir(directory)):
        if not fn.endswith(".json"):
            continue
        with open(os.path.join(directory, fn), encoding="utf-8") as f:
            p = json.load(f)
        for key in ("id", "pids", "name", "role", "fallback_lines"):
            if not p.get(key):
                raise ValueError("%s: persona missing %r" % (fn, key))
        if p["id"] in by_id:
            raise ValueError("%s: duplicate persona id %r" % (fn, p["id"]))
        p["fallback_lines"] = [sanitize(x) for x in p["fallback_lines"] if sanitize(x)]
        if not p["fallback_lines"]:
            raise ValueError("%s: no usable fallback_lines" % fn)
        by_id[p["id"]] = p
        for pid in p["pids"]:
            if not _is_int(pid):
                raise ValueError("%s: bad pid %r" % (fn, pid))
            if pid in by_pid:
                raise ValueError("%s: pid %d already mapped to %s" % (fn, pid, by_pid[pid]["id"]))
            by_pid[pid] = p
    return by_id, by_pid


def resolve_persona(by_pid, req):
    """Native identity/dialogue cover mod NPCs without inventing biographies."""
    npc = req["npc"]
    content = req.get("content") or "fallout2"
    if content == "fallout2" and npc["pid"] in by_pid:
        return by_pid[npc["pid"]]
    if not 0x01000000 < npc["pid"] < 0x02000000:
        return None
    identity = ([content, "instance", npc["instance"]] if npc.get("instance")
                else [content, "prototype", npc["pid"], npc["name"]])
    key = hashlib.sha256(json.dumps(identity).encode()).hexdigest()[:24]
    return {
        "id": "native-" + key, "pids": [npc["pid"]], "name": npc["name"],
        "role": "The person identified by the current game dialogue. Infer your "
                "role and manner only from that dialogue and the supplied facts",
        "voice": "Match the vocabulary and tone of your original dialogue",
        "never": ["inventing quests, rewards, secrets, relationships or past events",
                  "inventing an occupation or claiming to be a trader just because barter is available",
                  "claiming to be in the player's party unless the engine says so",
                  "modern references or knowledge of game mechanics"],
        "fallback_lines": ["Let's talk another time."],
    }


# --------------------------------------------------------------------------
# memory
# --------------------------------------------------------------------------

SCHEMA = """
CREATE TABLE IF NOT EXISTS exchanges (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    campaign TEXT NOT NULL,
    npc_id TEXT NOT NULL,
    ts REAL NOT NULL,
    pid INTEGER,
    player_name TEXT,
    player_line TEXT NOT NULL,
    npc_line TEXT NOT NULL,
    mood TEXT,
    intent TEXT,
    source TEXT,
    map TEXT,
    map_name TEXT,
    game_date TEXT,
    game_time TEXT,
    karma INTEGER
);
CREATE INDEX IF NOT EXISTS ix_exchanges_key ON exchanges(campaign, npc_id, id);
CREATE TABLE IF NOT EXISTS summaries (
    campaign TEXT NOT NULL,
    npc_id TEXT NOT NULL,
    summary TEXT NOT NULL,
    covered_upto INTEGER NOT NULL,
    total_at INTEGER NOT NULL,
    updated_ts REAL NOT NULL,
    PRIMARY KEY (campaign, npc_id)
);
"""

EX_COLS = ("id", "ts", "pid", "player_name", "player_line", "npc_line", "mood",
           "intent", "source", "map", "map_name", "game_date", "game_time", "karma")


class Memory(BranchMemory):
    def __init__(self, path):
        super().__init__(path, SCHEMA, EX_COLS)


# --------------------------------------------------------------------------
# LLM
# --------------------------------------------------------------------------

class LLMError(Exception):
    pass


def call_with_deadline(fn, timeout):
    """Run fn() in a daemon thread; give up after `timeout` seconds."""
    box = {}

    def run():
        try:
            box["v"] = fn()
        except BaseException as e:  # noqa: BLE001 - reported to caller
            box["e"] = e

    t = threading.Thread(target=run, daemon=True, name="llm-call")
    t.start()
    t.join(max(0.0, timeout))
    if t.is_alive():
        raise LLMError("timeout after %.1fs" % timeout)
    if "e" in box:
        raise LLMError("%s: %s" % (type(box["e"]).__name__, box["e"]))
    return box["v"]


def ollama_chat(base_url, payload, timeout):
    """Ollama's native chat API: unlike its OpenAI layer it can turn thinking off."""
    body = {"model": payload["model"], "messages": payload["messages"], "stream": False,
            "think": False, "keep_alive": "30m",
            "options": {"temperature": payload.get("temperature", 0.7),
                        "num_predict": payload.get("max_tokens", 220)}}
    fmt = payload.get("response_format") or {}
    if fmt.get("type") == "json_schema":
        body["format"] = fmt["json_schema"]["schema"]

    def post(body):
        req = urllib.request.Request(
            base_url.rstrip("/") + "/api/chat", data=json.dumps(body).encode("utf-8"),
            headers={"Content-Type": "application/json"}, method="POST")
        with urllib.request.urlopen(req, timeout=max(0.1, timeout)) as r:
            return r.read(1 << 20)

    try:
        raw = post(body)
    except urllib.error.HTTPError as e:
        detail = e.read(2048).decode("utf-8", "replace")
        e.close()
        # Models without a thinking mode reject the "think" switch.
        if e.code != 400 or "think" not in detail:
            raise LLMError("LLM HTTP %d" % e.code)
        del body["think"]
        try:
            raw = post(body)
        except urllib.error.HTTPError as e2:
            e2.close()
            raise LLMError("LLM HTTP %d" % e2.code)
    content = json.loads(raw).get("message", {}).get("content")
    if not isinstance(content, str):
        raise LLMError("content is not a string")
    return content


def llm_chat(base_url, payload, timeout, api="openai"):
    if api == "ollama":
        return ollama_chat(base_url, payload, timeout)
    req = urllib.request.Request(
        base_url.rstrip("/") + "/v1/chat/completions",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"}, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=max(0.1, timeout)) as r:
            raw = r.read(1 << 20)
    except urllib.error.HTTPError as e:
        e.close()
        raise LLMError("LLM HTTP %d" % e.code)
    data = json.loads(raw)
    content = data["choices"][0]["message"]["content"]
    if not isinstance(content, str):
        raise LLMError("content is not a string")
    return content


def parse_json_object(text):
    text = text.strip()
    if text.startswith("```"):
        text = re.sub(r"^```[a-zA-Z]*\s*|\s*```$", "", text)
    try:
        obj = json.loads(text)
    except ValueError:
        m = re.search(r"\{.*\}", text, re.S)
        if not m:
            raise LLMError("no JSON object in model output")
        try:
            obj = json.loads(m.group(0))
        except ValueError as e:
            raise LLMError("bad JSON from model: %s" % e)
    if not isinstance(obj, dict):
        raise LLMError("model output is not an object")
    return obj


# --------------------------------------------------------------------------
# prompting
# --------------------------------------------------------------------------

def karma_band(k):
    if k is None:
        return "unknown"
    if k <= -500:
        return "villainous"
    if k <= -100:
        return "shady"
    if k < 100:
        return "neutral"
    if k < 500:
        return "good"
    return "saintly"


def _fmt_list(xs):
    return "; ".join(str(x) for x in xs if x)


def player_facts(mem, campaign, npc_id, req):
    n = mem.count(campaign, npc_id)
    player = req["player"]
    facts = []
    if n == 0:
        facts.append("You have no earlier free-form conversations with %s on record "
                     "(you may still know them from the story so far)." % player["name"])
    else:
        first = mem.first(campaign, npc_id)
        last = mem.recent(campaign, npc_id, 1)[0]
        facts.append("You have talked with %s %d time%s before." %
                     (last.get("player_name") or player["name"], n, "" if n == 1 else "s"))
        where = last.get("map_name") or last.get("map")
        if where or last.get("game_date"):
            facts.append("Your last talk was%s%s." % (
                " in " + where if where else "",
                " on " + last["game_date"] if last.get("game_date") else ""))
        fwhere = first.get("map_name") or first.get("map")
        if n > 1 and (fwhere or first.get("game_date")):
            facts.append("Your first talk was%s%s." % (
                " in " + fwhere if fwhere else "",
                " on " + first["game_date"] if first.get("game_date") else ""))
        if last.get("player_name") and last["player_name"] != player["name"]:
            facts.append("They used to call themselves %s." % last["player_name"])
    facts.append("Their karma seems %s." % karma_band(player.get("karma")))
    return facts


def build_system_prompt(persona, req, summary, facts, allowed):
    npc, player = req["npc"], req["player"]
    world = req.get("world") or {}
    dialog = req.get("dialog") or {}
    L = []
    L.append("You are %s, a character in the Fallout wasteland. Use the engine's "
             "date and location for the setting, including in total conversions. "
             "Speak only as %s, in character, in plain spoken English."
             % (persona["name"], persona["name"]))
    L.append("Who you are: " + persona["role"] + ".")
    if persona.get("background"):
        L.append("What you know for certain: " + " ".join(persona["background"]))
    if persona.get("voice"):
        L.append("How you talk: " + persona["voice"] + ".")
    if persona.get("knows"):
        L.append("Topics you know about: " + _fmt_list(persona["knows"]) + ".")
    if persona.get("never"):
        L.append("Never: " + _fmt_list(persona["never"]) + ".")

    L.append("")
    L.append("CURRENT SITUATION (from the game engine; this is the truth):")
    if npc.get("description"):
        L.append("- Native description of your appearance: %s." % npc["description"])
    place = world.get("map_name") or npc.get("map")
    if place:
        L.append("- Place: %s." % place)
    if world.get("date") or world.get("time"):
        L.append("- Date/time: %s %s." % (world.get("date", ""), world.get("time", "")))
    if npc.get("party_member"):
        L.append("- You are travelling with %s as a member of their party%s." % (
            player["name"], (" (you call them %s)" % persona["companion_address"])
            if persona.get("companion_address") else ""))
    else:
        L.append("- You are NOT in %s's party." % player["name"])
    desc = [player["name"]]
    if player.get("sex"):
        desc.append(player["sex"])
    if player.get("level") is not None:
        desc.append("level %d" % player["level"])
    if player.get("reputation"):
        desc.append("reputation: %s" % player["reputation"])
    L.append("- The person talking to you: " + ", ".join(desc) + ".")
    inv = npc.get("inventory") or []
    if inv:
        items = ", ".join("%s x%d" % (sanitize(i["name"], 60), i.get("qty") or 1) for i in inv)
        L.append("- Your inventory, COMPLETE list: " + items + ".")
    else:
        L.append("- Your inventory: nothing to offer right now.")
    if npc.get("caps") is not None:
        L.append("- Your caps: %d." % npc["caps"])
    if npc.get("can_barter") is False:
        L.append("- You cannot trade right now.")
    if dialog.get("reply"):
        L.append('- The dialog screen shows your last line: "%s"' % dialog["reply"])
    if dialog.get("options"):
        L.append("- The player's scripted options on screen: " +
                 " | ".join(dialog["options"]))

    L.append("")
    L.extend(story_snapshot.render_story(req.get("story") or {}))
    L.append("MEMORY:")
    L.extend(req.get("_story_memory_lines", []))
    for f in facts:
        L.append("- " + f)
    if summary:
        L.append("- Summary of older conversations: " + summary)

    L.append("")
    L.append("RULES:")
    L.append("- Items and prices: the inventory list above is the ONLY truth about what you "
             "carry. Never offer, promise or claim to have any item that is not on it, and "
             "never quote a price in caps. If asked about something you know of that is not "
             "on the list, just say you don't have it with you right now; do not make up "
             "where it went.")
    if "open_barter" in allowed:
        L.append("- If the player wants to trade, buy or sell, agree in your own words and "
                 "choose intent open_barter; the haggling happens after.")
    else:
        L.append("- Trading is not possible right now. If the player asks to trade, put it off "
                 "in character (later, not here, not now).")
    L.append("- Never mention screens, menus, buttons, stats, saving or anything else about "
             "the game itself.")
    L.append("- Do not invent people, places, quests or events you are not sure of; "
             "be vague instead.")
    L.append("- Reply with 1 to 3 short sentences of speech only: no narration, no actions "
             "in asterisks, no emoji.")
    L.append("- Choose exactly one intent from this list:")
    for it in allowed:
        L.append("  * %s: %s" % (it, INTENT_HELP.get(it, "the engine action '%s'" % it)))
    L.append("  Use 'none' unless the player's line clearly calls for another intent. "
             "Offering or pitching goods is never a refusal.")
    L.append("- mood is how you feel toward the player right now: friendly, neutral, "
             "wary or hostile.")
    L.extend(story_effects.prompt_lines(req.get("allowed_effects") or {}, req.get("_relationship") or {}))
    L.append('- Answer with JSON only: say, mood, intent, and an effects array when consequences are available. '
             'Effects are proposals: the engine validates them. Use an empty array when none fit.')
    return "\n".join(L)


def build_messages(persona, req, history, summary, facts, allowed):
    msgs = [{"role": "system",
             "content": build_system_prompt(persona, req, summary, facts, allowed)}]
    for ex in history:
        msgs.append({"role": "user", "content": ex["player_line"]})
        msgs.append({"role": "assistant", "content": json.dumps(
            {"say": ex["npc_line"], "mood": ex.get("mood") or "neutral",
             "intent": ex.get("intent") or "none"})})
    msgs.append({"role": "user", "content": req["say"]})
    return msgs


def talk_schema(allowed, effects_allowed=None):
    result = {"type": "json_schema", "json_schema": {"name": "npc", "schema": {
        "type": "object",
        "properties": {
            "say": {"type": "string", "maxLength": MAX_SAY_OUT},
            "mood": {"type": "string", "enum": list(MOODS)},
            "intent": {"type": "string", "enum": list(allowed)},
        },
        "required": ["say", "mood", "intent"],
        "additionalProperties": False}}}

    if effects_allowed:
        schema = result["json_schema"]["schema"]
        schema["properties"]["effects"] = story_effects.response_schema_fragment(effects_allowed)
        schema["required"].append("effects")
    return result


# --------------------------------------------------------------------------
# the brain
# --------------------------------------------------------------------------

class Brain:
    def __init__(self, cfg):
        self.cfg = cfg
        self.token = load_token(cfg)
        self.personas, self.by_pid = load_personas(cfg.personas_dir)
        self.mem = Memory(cfg.db_path)
        os.makedirs(cfg.log_dir, exist_ok=True)
        self._log_lock = threading.Lock()
        self._health = {"t": 0.0, "llm": "down"}
        self._health_lock = threading.Lock()
        self._sum_lock = threading.Lock()
        self._sum_inflight = set()
        self._sum_failed_at = {}
        self.summary_threads = []   # for tests
        self.story = StoryRuntime(self, lambda payload, timeout: call_with_deadline(
            lambda: llm_chat(self.cfg.llm_url, payload, timeout, self.cfg.llm_api), timeout))
        self._talk_guard = threading.Lock()
        self._talk_locks = {}

    def close(self):
        self.story.close()
        for t in list(self.summary_threads):
            t.join(timeout=5)
        self.mem.close()

    # -- logging ---------------------------------------------------------
    def log(self, name, rec):
        rec = dict(rec)
        rec.setdefault("time", time.strftime("%Y-%m-%dT%H:%M:%S%z"))
        line = json.dumps(rec, ensure_ascii=False)
        with self._log_lock:
            with open(os.path.join(self.cfg.log_dir, name), "a", encoding="utf-8") as f:
                f.write(line + "\n")

    # -- health ----------------------------------------------------------
    def llm_status(self):
        with self._health_lock:
            if time.monotonic() - self._health["t"] < self.cfg.health_ttl and self._health["t"]:
                return self._health["llm"]
            status = "down"
            try:
                if self.cfg.llm_api == "ollama":
                    with urllib.request.urlopen(self.cfg.llm_url.rstrip("/") + "/api/tags",
                                                timeout=self.cfg.health_timeout) as r:
                        if r.status == 200:
                            status = "up"
                else:
                    with urllib.request.urlopen(self.cfg.llm_url.rstrip("/") + "/health",
                                                timeout=self.cfg.health_timeout) as r:
                        data = json.loads(r.read(4096) or b"{}")
                        if r.status == 200 and data.get("status") == "ok":
                            status = "up"
            except urllib.error.HTTPError as e:
                e.close()
                status = "down"
            except Exception:  # noqa: BLE001
                status = "down"
            self._health = {"t": time.monotonic(), "llm": status}
            return status

    # -- talk ------------------------------------------------------------
    def talk(self, req):
        persona = resolve_persona(self.by_pid, req)
        if persona is None:
            return None
        with self._talk_guard:
            lock = self._talk_locks.setdefault((req["campaign"], persona["id"]), threading.Lock())
        with lock:
            return self._talk(req)

    def _talk(self, req):
        t0 = time.monotonic()
        persona = resolve_persona(self.by_pid, req)
        if persona is None:
            return None
        campaign = req["campaign"]
        npc_id = persona["id"]
        allowed = []
        for it in ["none"] + req["allowed_intents"]:
            if it not in allowed:
                allowed.append(it)

        with self.mem.lock:
            branch, created = self.mem.timeline.resolve(campaign, req.get("timeline"))
        if created:
            self.log("talk.jsonl", {"event": "timeline_created", "campaign": campaign, "branch": branch,
                                    "requested_branch": (req.get("timeline") or {}).get("branch")})
        view = self.mem.view(branch)
        summary = view.summary(campaign, npc_id)["summary"]
        history = view.recent(campaign, npc_id, HISTORY_N)
        facts = player_facts(view, campaign, npc_id, req)
        req = dict(req)
        req["_story_memory_lines"], req["_relationship"] = self.story.context(campaign, branch, npc_id, req)
        messages = build_messages(persona, req, history, summary, facts, allowed)
        payload = {
            "model": self.cfg.model,
            "max_tokens": max(400, self.cfg.max_tokens) if req.get("allowed_effects") else self.cfg.max_tokens,
            "temperature": self.cfg.temperature,
            "chat_template_kwargs": {"enable_thinking": False},
            "messages": messages,
            "response_format": talk_schema(allowed, req.get("allowed_effects")),
        }
        if self.cfg.llm_slot >= 0:
            payload["id_slot"] = self.cfg.llm_slot
        if self.cfg.log_prompts:
            self.log("prompts.jsonl", {"campaign": campaign, "npc": npc_id, "messages": messages})

        source, error, requested = "llm", None, None
        say, mood, intent = "", "neutral", "none"
        out = {}
        budget = self.cfg.llm_timeout - (time.monotonic() - t0) - 0.05
        try:
            content = call_with_deadline(
                lambda: llm_chat(self.cfg.llm_url, payload, budget, self.cfg.llm_api), budget)
            out = parse_json_object(content)
            say = clean_say(out.get("say", ""), persona["name"])
            if not say:
                raise LLMError("empty say")
            mood = out.get("mood") if out.get("mood") in MOODS else "neutral"
            requested = out.get("intent")
            if isinstance(requested, str) and requested in allowed:
                intent = requested
            else:
                intent = "none"
                if requested != "none":
                    error = "intent %r not allowed; replaced by none" % (requested,)
        except Exception as e:  # noqa: BLE001 - every failure becomes a fallback
            source, error = "fallback", str(e)
            say = random.choice(persona["fallback_lines"])
            mood, intent = "neutral", "none"

        latency = int((time.monotonic() - t0) * 1000)
        world = req.get("world") or {}
        exchange_id = self.mem.add(campaign, npc_id, {
            "ts": time.time(), "pid": req["npc"]["pid"],
            "player_name": req["player"]["name"],
            "player_line": sanitize(req["say"], MAX_STR),
            "npc_line": say, "mood": mood, "intent": intent, "source": source,
            "map": req["npc"].get("map"), "map_name": world.get("map_name"),
            "game_date": world.get("date"), "game_time": world.get("time"),
            "karma": req["player"].get("karma"),
        }, branch=branch)
        accepted = self.story.validate_and_store(campaign, branch, npc_id, req, out.get("effects"), mood) if source == "llm" else []
        with self.mem.lock:
            head = self.mem.timeline.head(campaign)
        if source == "llm":
            self.story.extract_async(persona, req, branch, say)
        self.log("talk.jsonl", {
            "campaign": campaign, "npc": npc_id, "pid": req["npc"]["pid"],
            "latency_ms": latency, "source": source,
            "intent_requested": requested, "intent_accepted": intent,
            "allowed_intents": req["allowed_intents"], "error": error,
            "say_in": req["say"], "say_out": say,
        })
        self.maybe_summarize(persona, campaign, npc_id, branch)
        return {"v": API_V, "npc_id": npc_id, "say": say, "mood": mood,
                "intent": intent, "source": source, "latency_ms": latency,
                "effects": accepted, "timeline": {"branch": branch, "head": head}}

    # -- summaries -------------------------------------------------------
    def maybe_summarize(self, persona, campaign, npc_id, branch=None):
        view = self.mem.view(branch)
        key = (campaign, npc_id, branch)
        try:
            total = view.count(campaign, npc_id)
            s = view.summary(campaign, npc_id)
            if total - s["total_at"] < SUMMARY_EVERY or total <= HISTORY_N:
                return
            with self._sum_lock:
                if key in self._sum_inflight:
                    return
                failed = self._sum_failed_at.get(key)
                if failed and time.monotonic() - failed < self.cfg.summary_retry_s:
                    return
                self._sum_inflight.add(key)
            t = threading.Thread(target=self._summarize, args=(persona, campaign, npc_id, total, branch),
                                 daemon=True, name="summary")
            self.summary_threads = [x for x in self.summary_threads if x.is_alive()] + [t]
            t.start()
        except Exception as e:  # noqa: BLE001 - never fail a talk
            self.log("talk.jsonl", {"campaign": campaign, "npc": npc_id,
                                    "event": "summary_schedule_failed", "error": str(e)})

    def _summarize(self, persona, campaign, npc_id, total, branch=None):
        view = self.mem.view(branch)
        key = (campaign, npc_id, branch)
        try:
            prev = view.summary(campaign, npc_id)
            old = view.unsummarized_old(campaign, npc_id, prev["covered_upto"])
            if not old:
                view.set_summary(campaign, npc_id, prev["summary"],
                                     prev["covered_upto"], total)
                return
            lines = []
            for ex in old:
                where = ex.get("map_name") or ex.get("map") or "?"
                lines.append("[%s %s] %s: %s / %s: %s" % (
                    ex.get("game_date") or "?", where, ex.get("player_name") or "Player",
                    ex["player_line"], persona["name"], ex["npc_line"]))
            prompt = ("You keep the memory of %s, a Fallout 2 character. Merge the previous "
                      "summary and the new conversation lines into ONE short summary (under "
                      "600 characters), written in the third person, keeping names, promises, "
                      "favours, debts, places and how %s feels about the player. No invention."
                      % (persona["name"], persona["name"]))
            user = "Previous summary: %s\n\nNew lines:\n%s" % (
                prev["summary"] or "(none)", "\n".join(lines))
            payload = {
                "model": self.cfg.model, "max_tokens": 260, "temperature": 0.3,
                "chat_template_kwargs": {"enable_thinking": False},
                "messages": [{"role": "system", "content": prompt},
                             {"role": "user", "content": user}],
                "response_format": {"type": "json_schema", "json_schema": {
                    "name": "summary", "schema": {
                        "type": "object",
                        "properties": {"summary": {"type": "string",
                                                   "maxLength": MAX_SUMMARY}},
                        "required": ["summary"], "additionalProperties": False}}},
            }
            to = self.cfg.summary_timeout
            content = call_with_deadline(lambda: llm_chat(self.cfg.llm_url, payload, to, self.cfg.llm_api), to)
            text = sanitize(parse_json_object(content).get("summary", ""), MAX_SUMMARY)
            if not text:
                raise LLMError("empty summary")
            view.set_summary(campaign, npc_id, text, old[-1]["id"], total)
            with self._sum_lock:
                self._sum_failed_at.pop(key, None)
            self.log("talk.jsonl", {"campaign": campaign, "npc": npc_id,
                                    "event": "summary_refreshed", "covered_upto": old[-1]["id"]})
        except Exception as e:  # noqa: BLE001
            with self._sum_lock:
                self._sum_failed_at[key] = time.monotonic()
            try:
                self.log("talk.jsonl", {"campaign": campaign, "npc": npc_id,
                                        "event": "summary_failed", "error": str(e)})
            except Exception:  # noqa: BLE001
                pass
        finally:
            with self._sum_lock:
                self._sum_inflight.discard(key)


# --------------------------------------------------------------------------
# HTTP
# --------------------------------------------------------------------------

class Handler(http.server.BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"
    server_version = "WastelandBrain/1"
    sys_version = ""

    def log_message(self, fmt, *args):  # quiet; talk.jsonl is the log
        if getattr(self.server, "verbose", False):
            sys.stderr.write("%s %s\n" % (self.address_string(), fmt % args))

    @property
    def brain(self):
        return self.server.brain

    def send_json(self, code, obj, close=False):
        body = json.dumps(obj).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        if close:
            self.send_header("Connection", "close")
            self.close_connection = True
        self.end_headers()
        self.wfile.write(body)

    def authorized(self):
        h = self.headers.get("Authorization", "")
        if not h.startswith("Bearer "):
            return False
        return hmac.compare_digest(h[7:].strip().encode(), self.brain.token.encode())

    def route(self):
        return urllib.parse.urlsplit(self.path)

    def do_GET(self):
        u = self.route()
        if u.path == "/v1/health":
            return self.send_json(200, {"ok": True, "v": API_V, "llm": self.brain.llm_status(),
                                        "npcs": len(self.brain.personas)})
        if u.path not in ("/v1/npc/personas", "/v1/npc/memory"):
            return self.send_json(404, {"error": "not_found"})
        if not self.authorized():
            return self.send_json(401, {"error": "unauthorized"})
        if u.path == "/v1/npc/personas":
            return self.send_json(200, {"pids": sorted(self.brain.by_pid), "all_dialogue_npcs": True})
        q = urllib.parse.parse_qs(u.query)
        campaign = (q.get("campaign") or [""])[0]
        pid_s = (q.get("pid") or [""])[0]
        if not campaign:
            return self.send_json(422, {"error": "missing required field", "field": "campaign"})
        npc_id = (q.get("npc_id") or [""])[0]
        branch = (q.get("branch") or [None])[0]
        if npc_id:
            mem = self.brain.mem.view(branch)
            s = mem.summary(campaign, npc_id)
            return self.send_json(200, {"npc_id": npc_id, "campaign": campaign,
                                        "exchanges": mem.all(campaign, npc_id),
                                        "summary": s["summary"],
                                        "summary_covered_upto": s["covered_upto"]})
        try:
            pid = int(pid_s)
        except ValueError:
            return self.send_json(422, {"error": "must be an integer", "field": "pid"})
        persona = self.brain.by_pid.get(pid)
        if persona is None:
            return self.send_json(404, {"error": "unknown_npc"})
        mem = self.brain.mem.view(branch)
        s = mem.summary(campaign, persona["id"])
        return self.send_json(200, {"npc_id": persona["id"], "campaign": campaign,
                                    "exchanges": mem.all(campaign, persona["id"]),
                                    "summary": s["summary"],
                                    "summary_covered_upto": s["covered_upto"]})

    def do_POST(self):
        u = self.route()
        if u.path != "/v1/npc/talk":
            return self.send_json(404, {"error": "not_found"}, close=True)
        if not self.authorized():
            return self.send_json(401, {"error": "unauthorized"}, close=True)
        try:
            length = int(self.headers.get("Content-Length", ""))
        except ValueError:
            return self.send_json(411, {"error": "length_required"}, close=True)
        if length > MAX_BODY:
            return self.send_json(413, {"error": "too_large"}, close=True)
        raw = self.rfile.read(length) if length > 0 else b""
        try:
            body = json.loads(raw.decode("utf-8"))
        except (ValueError, UnicodeDecodeError):
            return self.send_json(400, {"error": "bad_json"})
        try:
            validate_talk(body)
        except Invalid as e:
            self.brain.log("talk.jsonl", {"event": "rejected", "status": 422,
                                          "error": e.msg, "field": e.field})
            return self.send_json(422, {"error": e.msg, "field": e.field})
        try:
            resp = self.brain.talk(body)
        except Exception as e:  # noqa: BLE001 - e.g. DB failure
            self.brain.log("talk.jsonl", {"event": "internal_error", "error": repr(e)})
            return self.send_json(500, {"error": "internal"})
        if resp is None:
            self.brain.log("talk.jsonl", {"event": "rejected", "status": 404,
                                          "pid": body["npc"]["pid"], "error": "unknown_npc"})
            return self.send_json(404, {"error": "unknown_npc"})
        return self.send_json(200, resp)


class BrainHTTPServer(http.server.ThreadingHTTPServer):
    daemon_threads = True
    allow_reuse_address = True

    def __init__(self, cfg, verbose=False):
        self.brain = Brain(cfg)
        self.verbose = verbose
        super().__init__((cfg.host, cfg.port), Handler)

    def server_close(self):
        super().server_close()
        self.brain.close()


def main(argv=None):
    ap = argparse.ArgumentParser(description="Wasteland Brain NPC talk service")
    ap.add_argument("--host", default="127.0.0.1")
    ap.add_argument("--port", type=int, default=8820)
    ap.add_argument("--llm", default=os.environ.get("BRAIN_LLM_URL", "http://127.0.0.1:8093"),
                    help="llama.cpp base URL")
    ap.add_argument("--model", default=os.environ.get("BRAIN_LLM_MODEL", "qwen38"))
    ap.add_argument("--llm-api", choices=["openai", "ollama"],
                    default=os.environ.get("BRAIN_LLM_API", "openai"))
    ap.add_argument("--db", default=os.path.join(HERE, "brain.db"))
    ap.add_argument("--personas", default=os.environ.get("BRAIN_PERSONAS",
                                                         os.path.join(HERE, "personas")))
    ap.add_argument("--log-dir", default=os.environ.get("BRAIN_LOG_DIR",
                                                        os.path.join(HERE, "logs")))
    ap.add_argument("--token-file", default=os.environ.get("BRAIN_TOKEN_FILE",
                                                           os.path.join(HERE, "token")))
    ap.add_argument("-v", "--verbose", action="store_true")
    a = ap.parse_args(argv)
    cfg = Config(host=a.host, port=a.port, llm_url=a.llm, model=a.model, llm_api=a.llm_api, db_path=a.db,
                 personas_dir=a.personas, log_dir=a.log_dir, token_file=a.token_file)
    srv = BrainHTTPServer(cfg, verbose=a.verbose)
    tok_src = "BRAIN_TOKEN env" if cfg.token else cfg.token_file
    print("wasteland-brain v%d on http://%s:%d  llm=%s model=%s personas=%d pids=%d token=%s "
          "timeout=%.1fs" % (API_V, cfg.host, cfg.port, cfg.llm_url, cfg.model,
                             len(srv.brain.personas), len(srv.brain.by_pid), tok_src,
                             cfg.llm_timeout), flush=True)
    def _term(*_):
        raise KeyboardInterrupt
    signal.signal(signal.SIGTERM, _term)
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        srv.server_close()


if __name__ == "__main__":
    main()
