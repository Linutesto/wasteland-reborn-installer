"""Tests for brain/server.py against a fake OpenAI-style LLM server.

    cd <repo root> && python3 -m unittest discover -s brain/tests -v
"""

import http.client
import http.server
import json
import os
import shutil
import sys
import tempfile
import threading
import time
import unittest
import urllib.parse

HERE = os.path.dirname(os.path.abspath(__file__))
BRAIN = os.path.dirname(HERE)
sys.path.insert(0, BRAIN)

import server as brain  # noqa: E402

TOKEN = "test-token-123"
VIC = 16777278


# --------------------------------------------------------------------------
# fake LLM
# --------------------------------------------------------------------------

class FakeLLM:
    """Tiny llama.cpp stand-in. Set .mode / .reply / .summary_mode per test."""

    def __init__(self):
        self.mode = "ok"            # ok | hang | garbage | http500 | badcontent
        self.facts_reply = {"facts": [], "relationship": {"trust": 0, "fear": 0}}
        self.facts_delay = 0
        self.summary_mode = "ok"    # ok | fail
        self.health_ok = True
        self.reply = {"say": "Sure thing, Boss.", "mood": "friendly", "intent": "none"}
        self.requests = []
        self.release = threading.Event()
        fake = self

        class H(http.server.BaseHTTPRequestHandler):
            protocol_version = "HTTP/1.1"

            def log_message(self, *a):
                pass

            def _send(self, code, body, ctype="application/json"):
                b = body if isinstance(body, bytes) else body.encode("utf-8")
                self.send_response(code)
                self.send_header("Content-Type", ctype)
                self.send_header("Content-Length", str(len(b)))
                self.end_headers()
                self.wfile.write(b)

            def do_GET(self):
                if self.path == "/health" and fake.health_ok:
                    return self._send(200, '{"status":"ok"}')
                return self._send(503, '{"status":"loading"}')

            def do_POST(self):
                n = int(self.headers.get("Content-Length", 0))
                req = json.loads(self.rfile.read(n))
                fake.requests.append(req)
                is_summary = req["response_format"]["json_schema"]["name"] == "summary"
                if req["response_format"]["json_schema"]["name"] == "facts":
                    time.sleep(fake.facts_delay)
                    content = json.dumps(fake.facts_reply)
                elif is_summary:
                    if fake.summary_mode == "fail":
                        return self._send(500, '{"error":"boom"}')
                    content = json.dumps({"summary": "The player freed Vic in the Den."})
                else:
                    if fake.mode == "hang":
                        fake.release.wait(10)
                        content = json.dumps(fake.reply)
                    elif fake.mode == "garbage":
                        return self._send(200, "<html>not json</html>", "text/html")
                    elif fake.mode == "badcontent":
                        content = "I am not JSON, sorry"
                    elif fake.mode == "http500":
                        return self._send(500, '{"error":"oops"}')
                    else:
                        content = json.dumps(fake.reply)
                body = {"choices": [{"index": 0, "message": {"role": "assistant",
                                                             "content": content}}]}
                try:
                    self._send(200, json.dumps(body))
                except (BrokenPipeError, ConnectionResetError):
                    pass

        self.httpd = http.server.ThreadingHTTPServer(("127.0.0.1", 0), H)
        self.httpd.daemon_threads = True
        self.url = "http://127.0.0.1:%d" % self.httpd.server_address[1]
        self.thread = threading.Thread(target=self.httpd.serve_forever, daemon=True)
        self.thread.start()

    def talk_requests(self):
        return [r for r in self.requests
                if r["response_format"]["json_schema"]["name"] == "npc"]

    def stop(self):
        self.release.set()
        self.httpd.shutdown()
        self.httpd.server_close()


# --------------------------------------------------------------------------
# helpers
# --------------------------------------------------------------------------

def talk_body(**over):
    body = {
        "v": 1,
        "campaign": "Chosen One|1792700000",
        "npc": {"pid": VIC, "name": "Vic", "map": "ARVILLAG", "party_member": True,
                "can_barter": True, "inventory": [{"pid": 40, "name": "Stimpak", "qty": 3}],
                "caps": 25},
        "player": {"name": "Chosen One", "sex": "male", "level": 1, "karma": 0,
                   "reputation": "Neutral",
                   "stats": {"st": 5, "pe": 5, "en": 5, "ch": 5, "in": 5, "ag": 5, "lk": 5},
                   "caps": 750},
        "world": {"date": "2241-07-25", "time": "08:15", "map_name": "Arroyo village"},
        "dialog": {"reply": "Sure, Boss.", "options": ["Never mind."]},
        "allowed_intents": ["none", "open_barter", "end_talk"],
        "say": "Got anything for a gecko bite?",
    }
    for k, v in over.items():
        body[k] = v
    return body


class BrainCase(unittest.TestCase):
    llm_timeout = 2.0

    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="brain-test-")
        self.llm = FakeLLM()
        self.srv = None
        self.start()

    def tearDown(self):
        self.stop()
        self.llm.stop()
        shutil.rmtree(self.tmp, ignore_errors=True)

    def cfg(self):
        return brain.Config(
            host="127.0.0.1", port=0, llm_url=self.llm.url,
            db_path=os.path.join(self.tmp, "brain.db"),
            personas_dir=os.path.join(BRAIN, "personas"),
            log_dir=os.path.join(self.tmp, "logs"),
            token=TOKEN, token_file=os.path.join(self.tmp, "token"),
            llm_timeout=self.llm_timeout, summary_timeout=2.0, summary_retry_s=0.0)

    def start(self, cfg=None):
        self.srv = brain.BrainHTTPServer(cfg or self.cfg())
        self.port = self.srv.server_address[1]
        self.srv_thread = threading.Thread(target=self.srv.serve_forever, daemon=True)
        self.srv_thread.start()

    def stop(self):
        if self.srv:
            self.srv.shutdown()
            self.srv.server_close()
            self.srv = None

    def restart(self):
        self.stop()
        self.start()

    def request(self, method, path, body=None, token=TOKEN, raw=None, headers=None):
        c = http.client.HTTPConnection("127.0.0.1", self.port, timeout=30)
        h = dict(headers or {})
        if token is not None:
            h["Authorization"] = "Bearer " + token
        data = raw if raw is not None else (json.dumps(body).encode() if body is not None else None)
        if data is not None:
            h["Content-Type"] = "application/json"
        c.request(method, path, body=data, headers=h)
        r = c.getresponse()
        out = r.read()
        c.close()
        try:
            return r.status, json.loads(out)
        except ValueError:
            return r.status, out

    def talk(self, **over):
        return self.request("POST", "/v1/npc/talk", talk_body(**over))

    def memory(self, campaign="Chosen One|1792700000", pid=VIC):
        from urllib.parse import urlencode
        return self.request("GET", "/v1/npc/memory?" + urlencode({"campaign": campaign,
                                                                  "pid": pid}))

    def wait_summaries(self):
        for t in list(self.srv.brain.summary_threads):
            t.join(timeout=5)


# --------------------------------------------------------------------------
# tests
# --------------------------------------------------------------------------

class TestTransport(BrainCase):
    def test_health_no_auth(self):
        st, r = self.request("GET", "/v1/health", token=None)
        self.assertEqual(st, 200)
        self.assertEqual(r, {"ok": True, "v": 1, "llm": "up", "npcs": 2})

    def test_health_llm_down(self):
        self.llm.health_ok = False
        st, r = self.request("GET", "/v1/health", token=None)
        self.assertEqual((st, r["llm"]), (200, "down"))

    def test_health_cached(self):
        self.request("GET", "/v1/health", token=None)
        self.llm.health_ok = False
        st, r = self.request("GET", "/v1/health", token=None)
        self.assertEqual(r["llm"], "up")   # cached for 15 s

    def test_personas(self):
        st, r = self.request("GET", "/v1/npc/personas")
        self.assertEqual(st, 200)
        self.assertEqual(r["pids"], sorted(r["pids"]))
        for pid in (16777278, 16777589, 16777590, 16777591, 16777592, 16777593, 16777594,
                    16777314):
            self.assertIn(pid, r["pids"])

    def test_auth_missing(self):
        st, r = self.request("POST", "/v1/npc/talk", talk_body(), token=None)
        self.assertEqual((st, r), (401, {"error": "unauthorized"}))

    def test_auth_wrong(self):
        for path in ("/v1/npc/personas", "/v1/npc/memory?campaign=x&pid=1"):
            st, r = self.request("GET", path, token="nope")
            self.assertEqual((st, r), (401, {"error": "unauthorized"}))
        st, r = self.request("POST", "/v1/npc/talk", talk_body(), token="nope")
        self.assertEqual(st, 401)
        self.assertEqual(self.llm.requests, [])

    def test_bad_json(self):
        st, r = self.request("POST", "/v1/npc/talk", raw=b'{"v":1, nope')
        self.assertEqual((st, r), (400, {"error": "bad_json"}))
        st, r = self.request("POST", "/v1/npc/talk", raw=b"\xff\xfe")
        self.assertEqual((st, r), (400, {"error": "bad_json"}))

    def test_oversize(self):
        st, r = self.request("POST", "/v1/npc/talk", raw=b" " * (64 * 1024 + 1))
        self.assertEqual(st, 413)
        self.assertEqual(self.llm.requests, [])

    def test_unknown_route(self):
        st, _ = self.request("GET", "/v1/nope")
        self.assertEqual(st, 404)

    def test_token_file_created_0600(self):
        cfg = self.cfg()
        cfg.token = None
        tok = brain.load_token(cfg)
        self.assertTrue(len(tok) >= 32)
        self.assertEqual(os.stat(cfg.token_file).st_mode & 0o777, 0o600)
        self.assertEqual(brain.load_token(cfg), tok)   # stable across restarts


class TestSchema(BrainCase):
    def assert422(self, body, field):
        st, r = self.request("POST", "/v1/npc/talk", body)
        self.assertEqual(st, 422, r)
        self.assertEqual(r["field"], field)
        self.assertIn("error", r)

    def test_missing_required(self):
        for f in ("v", "campaign", "say", "allowed_intents"):
            b = talk_body()
            del b[f]
            self.assert422(b, f)
        b = talk_body(); del b["npc"]["pid"]; self.assert422(b, "npc.pid")
        b = talk_body(); del b["npc"]["name"]; self.assert422(b, "npc.name")
        b = talk_body(); del b["player"]["name"]; self.assert422(b, "player.name")
        b = talk_body(); del b["player"]; self.assert422(b, "player")

    def test_types(self):
        self.assert422(talk_body(v=2), "v")
        self.assert422(talk_body(v="1"), "v")
        b = talk_body(); b["npc"]["pid"] = "16777278"; self.assert422(b, "npc.pid")
        b = talk_body(); b["npc"]["pid"] = True; self.assert422(b, "npc.pid")
        self.assert422(talk_body(allowed_intents="none"), "allowed_intents")
        self.assert422(talk_body(allowed_intents=[]), "allowed_intents")
        self.assert422(talk_body(allowed_intents=["none", 3]), "allowed_intents[1]")
        self.assert422(talk_body(say=""), "say")
        self.assert422(talk_body(say=12), "say")
        self.assert422([1, 2], "")
        b = talk_body(); b["npc"]["inventory"] = [{"pid": 40}]
        self.assert422(b, "npc.inventory[0].name")

    def test_limits(self):
        self.assert422(talk_body(say="x" * 301), "say")
        self.assertEqual(self.talk(say="x" * 300)[0], 200)
        b = talk_body(); b["npc"]["inventory"] = [{"name": "Rock", "qty": 1}] * 65
        self.assert422(b, "npc.inventory")
        b = talk_body(); b["dialog"]["options"] = ["y" * 301]
        self.assert422(b, "dialog.options[0]")
        b = talk_body(); b["campaign"] = "c" * 301
        self.assert422(b, "campaign")

    def test_unknown_npc(self):
        b = talk_body(); b["npc"]["pid"] = -1
        st, r = self.request("POST", "/v1/npc/talk", b)
        self.assertEqual((st, r), (404, {"error": "unknown_npc"}))
        st, r = self.memory(pid=16777219)
        self.assertEqual((st, r), (404, {"error": "unknown_npc"}))


class TestNativeNpcs(BrainCase):
    def native(self, instance="42", content="fallout2", pid=16777219):
        b = talk_body(content=content)
        b["npc"].update(pid=pid, name="Villager", instance=instance,
                         party_member=False, can_barter=False, description="A weathered brahmin herder.")
        b["dialog"] = {"reply": "I tend the brahmin here.", "options": ["Goodbye."]}
        b["allowed_intents"] = ["none", "end_talk"]
        return b

    def test_all_dialogue_npcs_advertised(self):
        st, r = self.request("GET", "/v1/npc/personas")
        self.assertTrue(r["all_dialogue_npcs"])

    def test_nonparty_npc_and_memory(self):
        b = self.native()
        st, r = self.request("POST", "/v1/npc/talk", b)
        self.assertEqual(st, 200)
        self.assertTrue(r["npc_id"].startswith("native-"))
        npc_id = r["npc_id"]
        self.assertIn("I tend the brahmin", self.llm.talk_requests()[-1]["messages"][0]["content"])
        self.assertIn("A weathered brahmin herder", self.llm.talk_requests()[-1]["messages"][0]["content"])
        b["npc"]["map"] = "NEWPLACE"
        st, r = self.request("POST", "/v1/npc/talk", b)
        self.assertEqual(r["npc_id"], npc_id)
        self.assertEqual(len(self.llm.talk_requests()[-1]["messages"]), 4)
        st, r = self.request("GET", "/v1/npc/memory?" + urllib.parse.urlencode({"campaign": b["campaign"], "npc_id": npc_id}))
        self.assertEqual(len(r["exchanges"]), 2)

    def test_instances_and_conversions_do_not_share_memory(self):
        ids = []
        for b in (self.native(), self.native(instance="43"), self.native(content="ettu"),
                  self.native(content="ettu", pid=VIC, instance="45")):
            st, r = self.request("POST", "/v1/npc/talk", b)
            self.assertEqual(st, 200)
            ids.append(r["npc_id"])
        self.assertEqual(len(set(ids)), 4)
        self.assertTrue(all(x.startswith("native-") for x in ids))

    def test_native_instance_keeps_memory_when_prototype_changes(self):
        b = self.native()
        _, first = self.request("POST", "/v1/npc/talk", b)
        b["npc"]["pid"] += 100
        _, second = self.request("POST", "/v1/npc/talk", b)
        self.assertEqual(first["npc_id"], second["npc_id"])
        self.assertEqual(len(self.llm.talk_requests()[-1]["messages"]), 4)

    def test_nonmerchant_cannot_open_barter(self):
        self.llm.reply["intent"] = "open_barter"
        st, r = self.request("POST", "/v1/npc/talk", self.native())
        self.assertEqual((st, r["intent"]), (200, "none"))

    def test_new_fields_validated(self):
        b = self.native(); b["content"] = 12
        st, r = self.request("POST", "/v1/npc/talk", b)
        self.assertEqual((st, r["field"]), (422, "content"))
        b = self.native(); b["npc"]["instance"] = 12
        st, r = self.request("POST", "/v1/npc/talk", b)
        self.assertEqual((st, r["field"]), (422, "npc.instance"))


class TestTalk(BrainCase):
    def test_happy_path(self):
        self.llm.reply = {"say": "Got three stimpaks, Boss. Want to trade?",
                          "mood": "friendly", "intent": "open_barter"}
        st, r = self.talk()
        self.assertEqual(st, 200, r)
        self.assertEqual(r["v"], 1)
        self.assertEqual(r["npc_id"], "vic")
        self.assertEqual(r["say"], "Got three stimpaks, Boss. Want to trade?")
        self.assertEqual(r["mood"], "friendly")
        self.assertEqual(r["intent"], "open_barter")
        self.assertEqual(r["source"], "llm")
        self.assertIsInstance(r["latency_ms"], int)
        # request shape sent to llama.cpp
        req = self.llm.talk_requests()[0]
        self.assertEqual(req["model"], "qwen38")
        self.assertEqual(req["max_tokens"], 220)
        self.assertEqual(req["temperature"], 0.7)
        self.assertEqual(req["chat_template_kwargs"], {"enable_thinking": False})
        sch = req["response_format"]["json_schema"]["schema"]
        self.assertEqual(sch["properties"]["intent"]["enum"], ["none", "open_barter", "end_talk"])
        self.assertEqual(sch["required"], ["say", "mood", "intent"])
        system = req["messages"][0]["content"]
        self.assertIn("Stimpak x3", system)
        self.assertIn("Your caps: 25", system)
        self.assertIn("ONLY truth", system)
        self.assertEqual(req["messages"][-1], {"role": "user",
                                               "content": "Got anything for a gecko bite?"})
        # log line
        with open(os.path.join(self.tmp, "logs", "talk.jsonl")) as f:
            rec = json.loads(f.readlines()[-1])
        self.assertEqual(rec["intent_requested"], "open_barter")
        self.assertEqual(rec["intent_accepted"], "open_barter")
        self.assertEqual(rec["source"], "llm")

    def test_intent_not_allowed(self):
        self.llm.reply = {"say": "Let's trade.", "mood": "friendly", "intent": "open_barter"}
        st, r = self.talk(allowed_intents=["none", "end_talk"])
        self.assertEqual(st, 200)
        self.assertEqual(r["intent"], "none")
        self.assertEqual(r["source"], "llm")
        self.assertEqual(r["say"], "Let's trade.")
        with open(os.path.join(self.tmp, "logs", "talk.jsonl")) as f:
            rec = json.loads(f.readlines()[-1])
        self.assertEqual(rec["intent_requested"], "open_barter")
        self.assertEqual(rec["intent_accepted"], "none")
        self.assertIn("not allowed", rec["error"])
        # schema enum also restricted
        enum = self.llm.talk_requests()[0]["response_format"]["json_schema"]["schema"][
            "properties"]["intent"]["enum"]
        self.assertNotIn("open_barter", enum)

    def test_prompt_trade_rules(self):
        self.talk(allowed_intents=["none", "open_barter"])
        self.talk(allowed_intents=["none", "end_talk"])
        a, b = [r["messages"][0]["content"] for r in self.llm.talk_requests()]
        self.assertIn("choose intent open_barter", a)
        self.assertNotIn("Trading is not possible", a)
        self.assertIn("Trading is not possible right now", b)
        self.assertNotIn("open_barter", b)
        self.assertIn("(you call them Boss)", a)

    def test_none_always_available(self):
        self.llm.reply = {"say": "Bye.", "mood": "neutral", "intent": "attack"}
        st, r = self.talk(allowed_intents=["end_talk"])
        self.assertEqual((st, r["intent"]), (200, "none"))
        enum = self.llm.talk_requests()[0]["response_format"]["json_schema"]["schema"][
            "properties"]["intent"]["enum"]
        self.assertEqual(enum, ["none", "end_talk"])

    def test_bad_mood_becomes_neutral(self):
        self.llm.reply = {"say": "Hm.", "mood": "ecstatic", "intent": "none"}
        st, r = self.talk()
        self.assertEqual(r["mood"], "neutral")

    def test_sanitize(self):
        self.llm.reply = {"say": "Vic: “Well—I’ll be…”\nCafé "
                                 "\U0001F600 日本 \tdone " + "word " * 120,
                          "mood": "friendly", "intent": "none"}
        st, r = self.talk()
        s = r["say"]
        self.assertEqual(r["source"], "llm")
        self.assertLessEqual(len(s), 400)
        self.assertTrue(all(32 <= ord(c) <= 126 for c in s), s)
        self.assertNotIn("\n", s)
        self.assertTrue(s.startswith("\"Well-I'll be...\" Cafe done word"), s)
        self.assertTrue(s.endswith("..."))

    def test_sanitize_unit(self):
        self.assertEqual(brain.sanitize("a–b\r\nc"), "a-b c")
        self.assertEqual(brain.sanitize("日本"), "")
        self.assertEqual(len(brain.sanitize("x" * 1000)), 400)
        self.assertEqual(brain.clean_say('"Howdy."', "Vic"), "Howdy.")

    def test_empty_say_is_fallback(self):
        self.llm.reply = {"say": "日本語", "mood": "friendly", "intent": "none"}
        st, r = self.talk()
        self.assertEqual(r["source"], "fallback")
        self.assertTrue(r["say"])

    def fallback_check(self, max_s):
        t0 = time.monotonic()
        st, r = self.talk(allowed_intents=["none", "open_barter"])
        dt = time.monotonic() - t0
        self.assertEqual(st, 200)
        self.assertEqual(r["source"], "fallback")
        self.assertEqual(r["intent"], "none")
        with open(os.path.join(BRAIN, "personas", "vic.json")) as f:
            persona = json.load(f)
        self.assertIn(r["say"], persona["fallback_lines"])
        self.assertLess(dt, max_s)
        return dt

    def test_llm_timeout(self):
        self.llm.mode = "hang"
        dt = self.fallback_check(self.llm_timeout + 1.0)
        self.assertGreaterEqual(dt, self.llm_timeout - 0.3)

    def test_llm_garbage(self):
        for mode in ("garbage", "badcontent", "http500"):
            self.llm.mode = mode
            self.fallback_check(self.llm_timeout)

    def test_llm_unreachable(self):
        self.stop()
        cfg = self.cfg()
        cfg.llm_url = "http://127.0.0.1:9"   # discard port, nothing listening
        self.start(cfg)
        self.fallback_check(self.llm_timeout)
        st, r = self.request("GET", "/v1/health", token=None)
        self.assertEqual(r["llm"], "down")

    def test_env_timeout(self):
        os.environ["BRAIN_LLM_TIMEOUT"] = "0.7"
        try:
            self.assertEqual(brain.Config().llm_timeout, 0.7)
        finally:
            del os.environ["BRAIN_LLM_TIMEOUT"]
        self.assertEqual(brain.Config().llm_timeout, 25.0)

    def test_concurrent_talks(self):
        results = []

        def go(i):
            results.append(self.talk(say="line %d" % i)[0])
        ts = [threading.Thread(target=go, args=(i,)) for i in range(6)]
        [t.start() for t in ts]
        [t.join() for t in ts]
        self.assertEqual(results, [200] * 6)
        self.assertEqual(len(self.memory()[1]["exchanges"]), 6)


class TestMemory(BrainCase):
    def test_exchange_stored_and_in_next_prompt(self):
        self.llm.reply = {"say": "Boss! Good to see you.", "mood": "friendly", "intent": "none"}
        self.talk(say="Hi Vic, remember me?")
        b = talk_body(say="Still got the flask?")
        b["npc"]["map"] = "DENBUS1"
        b["world"]["map_name"] = "The Den"
        self.request("POST", "/v1/npc/talk", b)
        st, m = self.memory()
        self.assertEqual(st, 200)
        ex = m["exchanges"]
        self.assertEqual([e["player_line"] for e in ex], ["Hi Vic, remember me?",
                                                           "Still got the flask?"])
        self.assertEqual(ex[0]["npc_line"], "Boss! Good to see you.")
        self.assertEqual([e["map"] for e in ex], ["ARVILLAG", "DENBUS1"])
        self.assertEqual(ex[0]["game_date"], "2241-07-25")
        self.assertEqual(ex[0]["intent"], "none")
        msgs = self.llm.talk_requests()[1]["messages"]
        self.assertEqual(msgs[1], {"role": "user", "content": "Hi Vic, remember me?"})
        self.assertEqual(json.loads(msgs[2]["content"])["say"], "Boss! Good to see you.")
        self.assertIn("talked with Chosen One 1 time before", msgs[0]["content"])
        self.assertIn("last talk was in Arroyo village", msgs[0]["content"])

    def test_history_window_is_8(self):
        for i in range(11):
            self.talk(say="line %d" % i)
        msgs = self.llm.talk_requests()[-1]["messages"]
        users = [m["content"] for m in msgs[1:] if m["role"] == "user"]
        self.assertEqual(users, ["line %d" % i for i in range(2, 10)] + ["line 10"])

    def test_persists_across_restart(self):
        self.talk(say="Remember this.")
        self.restart()
        st, m = self.memory()
        self.assertEqual([e["player_line"] for e in m["exchanges"]], ["Remember this."])
        self.talk(say="And now?")
        msgs = self.llm.talk_requests()[-1]["messages"]
        self.assertEqual(msgs[1]["content"], "Remember this.")

    def test_campaign_isolation(self):
        self.talk(campaign="A|1", say="secret for A")
        self.talk(campaign="B|2", say="hello from B")
        self.assertEqual([e["player_line"] for e in self.memory("A|1")[1]["exchanges"]],
                         ["secret for A"])
        self.assertEqual([e["player_line"] for e in self.memory("B|2")[1]["exchanges"]],
                         ["hello from B"])
        prompt_b = json.dumps(self.llm.talk_requests()[1]["messages"])
        self.assertNotIn("secret for A", prompt_b)

    def test_npc_isolation(self):
        self.talk(say="for vic only")
        b = talk_body(say="hi maida")
        b["npc"]["pid"] = 16777314
        b["npc"]["name"] = "Maida Buckner"
        st, r = self.request("POST", "/v1/npc/talk", b)
        self.assertEqual(r["npc_id"], "maida")
        self.assertNotIn("for vic only", json.dumps(self.llm.talk_requests()[1]["messages"]))
        self.assertEqual([e["player_line"] for e in self.memory(pid=16777314)[1]["exchanges"]],
                         ["hi maida"])
        self.assertEqual([e["player_line"] for e in self.memory()[1]["exchanges"]],
                         ["for vic only"])

    def test_vic_stage_pids_share_memory(self):
        for pid in (16777278, 16777590, 16777594):
            b = talk_body(say="pid %d" % pid)
            b["npc"]["pid"] = pid
            st, r = self.request("POST", "/v1/npc/talk", b)
            self.assertEqual(r["npc_id"], "vic")
        a = self.memory(pid=16777278)[1]["exchanges"]
        c = self.memory(pid=16777593)[1]["exchanges"]
        self.assertEqual(a, c)
        self.assertEqual(len(a), 3)
        self.assertEqual(self.llm.talk_requests()[2]["messages"][1]["content"], "pid 16777278")

    def test_fallback_exchanges_stored(self):
        self.llm.mode = "http500"
        self.talk(say="anyone home?")
        ex = self.memory()[1]["exchanges"]
        self.assertEqual((len(ex), ex[0]["source"]), (1, "fallback"))

    def test_summary_refresh(self):
        for i in range(9):
            self.talk(say="line %d" % i)
        self.wait_summaries()
        st, m = self.memory()
        self.assertEqual(m["summary"], "The player freed Vic in the Den.")
        self.assertEqual(m["summary_covered_upto"], m["exchanges"][0]["id"])
        sreq = [r for r in self.llm.requests
                if r["response_format"]["json_schema"]["name"] == "summary"]
        self.assertEqual(len(sreq), 1)
        self.assertIn("line 0", sreq[0]["messages"][1]["content"])
        self.assertNotIn("line 1", sreq[0]["messages"][1]["content"])
        self.talk(say="after summary")
        system = self.llm.talk_requests()[-1]["messages"][0]["content"]
        self.assertIn("Summary of older conversations: The player freed Vic", system)
        # no new summary until 8 more exchanges
        self.wait_summaries()
        self.assertEqual(len([r for r in self.llm.requests
                              if r["response_format"]["json_schema"]["name"] == "summary"]), 1)

    def test_summary_failure_does_not_fail_talk(self):
        self.llm.summary_mode = "fail"
        codes = []
        for i in range(12):
            st, r = self.talk(say="line %d" % i)
            codes.append((st, r["source"]))
            self.wait_summaries()
        self.assertEqual(codes, [(200, "llm")] * 12)
        st, m = self.memory()
        self.assertEqual(m["summary"], "")
        with open(os.path.join(self.tmp, "logs", "talk.jsonl")) as f:
            self.assertTrue(any('"summary_failed"' in line for line in f))
        # recovers once the LLM summarizes again
        self.llm.summary_mode = "ok"
        self.talk(say="line 12")
        self.wait_summaries()
        self.assertTrue(self.memory()[1]["summary"])

    def test_memory_endpoint_validation(self):
        st, r = self.request("GET", "/v1/npc/memory?pid=16777278")
        self.assertEqual((st, r["field"]), (422, "campaign"))
        st, r = self.request("GET", "/v1/npc/memory?campaign=x&pid=abc")
        self.assertEqual((st, r["field"]), (422, "pid"))
        st, r = self.memory("never-played")
        self.assertEqual((st, r["exchanges"], r["summary"]), (200, [], ""))


class TestPersonas(unittest.TestCase):
    def test_persona_files(self):
        by_id, by_pid = brain.load_personas(os.path.join(BRAIN, "personas"))
        self.assertEqual(set(by_id), {"vic", "maida"})
        self.assertEqual(by_pid[16777589]["id"], "vic")
        self.assertEqual(by_pid[16777314]["id"], "maida")
        # every persona pid exists in the engine's critter table under the right name
        names = {}
        with open(os.path.join(BRAIN, "..", "docs", "critter-pids.tsv")) as f:
            for line in f:
                parts = line.rstrip("\n").split("\t")
                if len(parts) >= 3 and parts[0].isdigit():
                    names[int(parts[0])] = parts[2]
        for pid, p in by_pid.items():
            self.assertTrue(names.get(pid, "").startswith(p["name"].split(" ")[0]),
                            (pid, names.get(pid)))


if __name__ == "__main__":
    unittest.main()
