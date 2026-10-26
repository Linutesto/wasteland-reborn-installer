"""effects: validation of LLM-proposed consequences against allowed_effects (SPEC.md section 5)."""
import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import effects  # noqa: E402

ALLOWED = {
    "discount": {"max_percent": 20},
    "gift": {"items": [{"pid": 40, "name": "Stimpak", "max_qty": 2}]},
    "reveal_location": {"names": ["Klamath", "The Den"]},
    "side_quest": {"max_caps": 200, "max_xp": 100, "fetch_items": [{"pid": 19, "name": "Rock"}],
                   "visit_locations": ["The Den"]},
    "complete_quest": {"ids": ["q-3"]},
    "turn_hostile": {},
}
FRIEND = {"trust": 6, "fear": 0}
NEUTRAL = {"trust": 0, "fear": 0}
ENEMY = {"trust": -7, "fear": 0}


def v(proposed, rel=FRIEND, mood="friendly", active=0, allowed=ALLOWED):
    return effects.validate_effects(proposed, allowed, rel, mood, active_quests=active)


class ValidateTest(unittest.TestCase):
    def test_types(self):
        self.assertEqual(set(effects.TYPES), {"discount", "gift", "reveal_location", "side_quest", "complete_quest", "turn_hostile"})

    def test_not_allowed_type_dropped(self):
        kept, dropped = v([{"type": "discount", "percent": 10}], allowed={"gift": ALLOWED["gift"]})
        self.assertEqual(kept, [])
        self.assertEqual(len(dropped), 1)
        kept, dropped = v([{"type": "nuke"}, "garbage", None, {"no": "type"}])
        self.assertEqual(kept, [])
        self.assertEqual(len(dropped), 4)

    def test_at_most_two(self):
        kept, dropped = v([{"type": "discount", "percent": 5}, {"type": "reveal_location", "name": "Klamath"},
                           {"type": "gift", "pid": 40, "qty": 1}])
        self.assertEqual(len(kept), 2)
        self.assertEqual(len(dropped), 1)

    def test_not_a_list(self):
        self.assertEqual(v({"type": "discount", "percent": 5}), ([], []))
        self.assertEqual(v(None), ([], []))

    def test_discount(self):
        self.assertEqual(v([{"type": "discount", "percent": 10}])[0], [{"type": "discount", "percent": 10}])
        self.assertEqual(v([{"type": "discount", "percent": 50}])[0], [{"type": "discount", "percent": 20}])  # clamped
        self.assertEqual(v([{"type": "discount", "percent": 0}])[0], [])
        self.assertEqual(v([{"type": "discount", "percent": "ten"}])[0], [])
        self.assertEqual(v([{"type": "discount", "percent": 10}], rel={"trust": 2, "fear": 0})[0], [])  # trust >= 3

    def test_gift(self):
        self.assertEqual(v([{"type": "gift", "pid": 40, "qty": 5}])[0], [{"type": "gift", "pid": 40, "qty": 2}])
        self.assertEqual(v([{"type": "gift", "pid": 41, "qty": 1}])[0], [])  # not offered
        self.assertEqual(v([{"type": "gift", "pid": 40, "qty": 1}], rel={"trust": 4, "fear": 0})[0], [])  # trust >= 5
        self.assertEqual(v([{"type": "gift", "pid": 40}])[0], [{"type": "gift", "pid": 40, "qty": 1}])  # default qty

    def test_reveal(self):
        self.assertEqual(v([{"type": "reveal_location", "name": "klamath"}], rel=NEUTRAL)[0],
                         [{"type": "reveal_location", "name": "Klamath"}])  # canonical name
        self.assertEqual(v([{"type": "reveal_location", "name": "Navarro"}])[0], [])

    def test_side_quest_fetch(self):
        q = {"type": "side_quest", "title": "Rocks for Vic", "objective": "Bring Vic 3 rocks.", "kind": "fetch",
             "pid": 19, "qty": 3, "reward_caps": 500, "reward_xp": 50}
        kept, _ = v([q], rel=NEUTRAL)
        self.assertEqual(kept[0]["reward_caps"], 200)
        self.assertEqual(kept[0]["reward_xp"], 50)
        self.assertEqual((kept[0]["kind"], kept[0]["pid"], kept[0]["qty"]), ("fetch", 19, 3))
        self.assertEqual(v([dict(q, pid=999)], rel=NEUTRAL)[0], [])
        self.assertEqual(v([dict(q, title="")], rel=NEUTRAL)[0], [])
        self.assertEqual(v([q], rel=NEUTRAL, active=1)[0], [])  # one active quest per NPC
        long_q = dict(q, title="t" * 200, objective="o" * 900)
        k = v([long_q], rel=NEUTRAL)[0][0]
        self.assertLessEqual(len(k["title"]), 60)
        self.assertLessEqual(len(k["objective"]), 200)
        self.assertEqual(v([dict(q, qty=0)], rel=NEUTRAL)[0][0]["qty"], 1)
        self.assertLessEqual(v([dict(q, qty=50)], rel=NEUTRAL)[0][0]["qty"], 10)

    def test_side_quest_visit(self):
        q = {"type": "side_quest", "title": "Scout the Den", "objective": "Go to the Den.", "kind": "visit",
             "location": "the den", "reward_caps": 10, "reward_xp": -5}
        kept, _ = v([q], rel=NEUTRAL)
        self.assertEqual(kept[0]["location"], "The Den")
        self.assertEqual(kept[0]["reward_xp"], 0)
        self.assertNotIn("pid", kept[0])
        self.assertEqual(v([dict(q, location="Klamath")], rel=NEUTRAL)[0], [])
        self.assertEqual(v([dict(q, kind="kill")], rel=NEUTRAL)[0], [])

    def test_complete_quest(self):
        self.assertEqual(v([{"type": "complete_quest", "id": "q-3"}], rel=NEUTRAL)[0], [{"type": "complete_quest", "id": "q-3"}])
        self.assertEqual(v([{"type": "complete_quest", "id": "q-9"}], rel=NEUTRAL)[0], [])

    def test_turn_hostile(self):
        self.assertEqual(v([{"type": "turn_hostile"}], rel=ENEMY, mood="hostile")[0], [{"type": "turn_hostile"}])
        self.assertEqual(v([{"type": "turn_hostile"}], rel=ENEMY, mood="wary")[0], [])
        self.assertEqual(v([{"type": "turn_hostile"}], rel={"trust": -5, "fear": 0}, mood="hostile")[0], [])

    def test_output_has_only_known_keys(self):
        kept, _ = v([{"type": "discount", "percent": 10, "evil": "x"}])
        self.assertEqual(kept, [{"type": "discount", "percent": 10}])


class PromptTest(unittest.TestCase):
    def test_prompt_mentions_only_allowed(self):
        text = "\n".join(effects.prompt_lines({"discount": {"max_percent": 15}, "reveal_location": {"names": ["Klamath"]}}, NEUTRAL))
        self.assertIn("discount", text)
        self.assertIn("15", text)
        self.assertIn("Klamath", text)
        self.assertNotIn("turn_hostile", text)
        self.assertNotIn("gift", text)
        self.assertEqual(effects.prompt_lines({}, NEUTRAL), [])

    def test_schema(self):
        s = effects.response_schema_fragment(ALLOWED)
        self.assertEqual(s["type"], "array")
        self.assertEqual(s["maxItems"], 2)


if __name__ == "__main__":
    unittest.main()
