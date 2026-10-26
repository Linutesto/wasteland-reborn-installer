"""facts: extraction prompt, parsing/clamping, dedupe, relationship, selection (SPEC.md section 3)."""
import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import facts  # noqa: E402


class ExtractionPromptTest(unittest.TestCase):
    def test_messages_shape(self):
        msgs = facts.extraction_messages("Vic", "Chosen One", "I'll get you a radio part.", "Deal, Boss.")
        self.assertIsInstance(msgs, list)
        self.assertEqual(msgs[0]["role"], "system")
        self.assertEqual(msgs[-1]["role"], "user")
        joined = " ".join(m["content"] for m in msgs)
        for needle in ("Vic", "Chosen One", "radio part", "Deal, Boss.", "promise", "trust", "fear", "JSON"):
            self.assertIn(needle, joined)


class ParseTest(unittest.TestCase):
    def test_parses_and_clamps(self):
        raw = ('{"facts": [{"kind": "promise", "text": "The player promised a radio part.", "importance": 9, "secret": false},'
               '{"kind": "bogus", "text": "x", "importance": 3},'
               '{"kind": "insult", "text": "", "importance": 2},'
               '{"kind": "info", "text": "' + "a" * 500 + '", "importance": 0}],'
               ' "relationship": {"trust": 5, "fear": -7}}')
        fs, rel = facts.parse_extraction(raw)
        self.assertEqual(len(fs), 2)  # bogus kind and empty text dropped
        self.assertEqual(fs[0], {"kind": "promise", "text": "The player promised a radio part.", "importance": 5, "secret": False})
        self.assertEqual(fs[1]["importance"], 1)
        self.assertLessEqual(len(fs[1]["text"]), 200)
        self.assertEqual(rel, {"trust": 2, "fear": -2})

    def test_max_three_facts(self):
        items = ",".join('{"kind": "info", "text": "fact %d", "importance": 2}' % i for i in range(6))
        fs, _ = facts.parse_extraction('{"facts": [%s]}' % items)
        self.assertEqual(len(fs), 3)

    def test_secret_defaults_and_kinds(self):
        self.assertEqual(set(facts.KINDS), {"promise", "secret", "debt", "claim", "insult", "favor", "threat", "info"})
        fs, rel = facts.parse_extraction('{"facts": [{"kind": "secret", "text": "Vic owes the Slavers.", "importance": 4}]}')
        self.assertTrue(fs[0]["secret"])  # kind secret is always secret
        self.assertEqual(rel, {"trust": 0, "fear": 0})

    def test_garbage_and_fenced(self):
        self.assertEqual(facts.parse_extraction("not json at all"), ([], {"trust": 0, "fear": 0}))
        self.assertEqual(facts.parse_extraction(""), ([], {"trust": 0, "fear": 0}))
        fs, _ = facts.parse_extraction('Sure!\n```json\n{"facts": [{"kind": "favor", "text": "Helped.", "importance": 3}]}\n```')
        self.assertEqual(fs[0]["kind"], "favor")
        fs, rel = facts.parse_extraction('{"facts": "nope", "relationship": {"trust": "lots"}}')
        self.assertEqual((fs, rel), ([], {"trust": 0, "fear": 0}))

    def test_text_sanitized_printable_ascii(self):
        fs, _ = facts.parse_extraction('{"facts": [{"kind": "info", "text": "He said “hi” — then left\\n.", "importance": 2}]}')
        t = fs[0]["text"]
        self.assertTrue(all(32 <= ord(c) < 127 for c in t), t)
        self.assertIn('"hi"', t)


class DedupeTest(unittest.TestCase):
    def test_drops_equal_and_contained(self):
        existing = ["The player promised a radio part."]
        new = [
            {"kind": "promise", "text": "the player promised a RADIO part", "importance": 3, "secret": False},
            {"kind": "promise", "text": "The player promised a radio part to Vic by tomorrow.", "importance": 3, "secret": False},
            {"kind": "info", "text": "Vic likes radios.", "importance": 2, "secret": False},
            {"kind": "info", "text": "Vic likes radios!", "importance": 2, "secret": False},
        ]
        kept = facts.dedupe(existing, new)
        self.assertEqual([k["text"] for k in kept], ["Vic likes radios."])


class RelationshipTest(unittest.TestCase):
    def test_sum_clamped(self):
        self.assertEqual(facts.sum_relationship([{"trust": 2, "fear": 1}] * 8), {"trust": 10, "fear": 8})
        self.assertEqual(facts.sum_relationship([{"trust": -2}] * 9), {"trust": -10, "fear": 0})
        self.assertEqual(facts.sum_relationship([]), {"trust": 0, "fear": 0})

    def test_words(self):
        self.assertIn("trust", facts.relationship_words({"trust": 8, "fear": 0}).lower())
        neutral = facts.relationship_words({"trust": 0, "fear": 0})
        hostile = facts.relationship_words({"trust": -8, "fear": 0}).lower()
        afraid = facts.relationship_words({"trust": 0, "fear": 7}).lower()
        self.assertTrue(neutral)
        self.assertTrue("distrust" in hostile or "hate" in hostile or "not trust" in hostile, hostile)
        self.assertIn("afraid", afraid)
        self.assertNotEqual(facts.relationship_words({"trust": 2, "fear": 0}), facts.relationship_words({"trust": 9, "fear": 0}))


class SelectTest(unittest.TestCase):
    def test_importance_then_newest(self):
        rows = [{"seq": i, "payload": {"kind": "info", "text": "f%d" % i, "importance": imp, "secret": False}}
                for i, imp in enumerate([1, 5, 3, 5, 2, 4, 1, 3, 2, 5, 1], start=1)]
        picked = facts.select_facts(rows, 4)
        self.assertEqual([p["text"] for p in picked], ["f10", "f4", "f2", "f6"])

    def test_prompt_lines(self):
        rows = [{"seq": 1, "payload": {"kind": "claim", "text": "The player says they are a Vault 13 envoy.", "importance": 3, "secret": False}},
                {"seq": 2, "payload": {"kind": "promise", "text": "The player promised a radio part.", "importance": 4, "secret": False}}]
        lines = facts.prompt_lines(facts.select_facts(rows, 8))
        self.assertEqual(len(lines), 2)
        claim = [l for l in lines if "envoy" in l][0].lower()
        self.assertTrue("claim" in claim or "unverified" in claim, claim)


if __name__ == "__main__":
    unittest.main()
