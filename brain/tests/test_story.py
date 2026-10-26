"""story: validate + render the engine's story snapshot (SPEC.md section 1)."""
import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import story  # noqa: E402

SNAP = {
    "quests": [{"location": "Arroyo", "text": "Retrieve the G.E.C.K.", "state": "active"},
               {"location": "Klamath", "text": "Rescue Smiley the Trapper", "state": "done"},
               {"location": "Klamath", "text": "Kill the rat god", "state": "failed"}],
    "towns": [{"name": "Klamath", "reputation": 12, "title": "Accepted"}],
    "karma_title": "Defender",
    "kills": {"total": 31, "men": 4, "women": 0, "children": 0},
    "party": ["Vic", "Sulik"],
    "perks_titles": ["Made Man"],
    "known_locations": ["Arroyo", "Klamath", "The Den"],
    "game_ticks": 302400000,
    "npc_team": 4,
    "wasteland": {"quests": [{"id": "q-3", "giver": "Vic", "title": "Radio part for Vic", "state": "active"}],
                  "discount_percent": 10},
}


class ValidateTest(unittest.TestCase):
    def test_valid_passes_through(self):
        s = story.validate_story(SNAP)
        self.assertEqual(s["karma_title"], "Defender")
        self.assertEqual(len(s["quests"]), 3)
        self.assertEqual(s["game_ticks"], 302400000)
        self.assertEqual(s["npc_team"], 4)

    def test_none_and_garbage(self):
        self.assertEqual(story.validate_story(None), {})
        self.assertEqual(story.validate_story("x"), {})
        s = story.validate_story({"quests": "nope", "kills": {"total": "many"}, "game_ticks": "1", "party": [1, "Vic", ""]})
        self.assertEqual(s.get("quests", []), [])
        self.assertNotIn("game_ticks", s)
        self.assertEqual(s.get("party"), ["Vic"])

    def test_limits_and_sanitize(self):
        s = story.validate_story({
            "quests": [{"location": "L", "text": "q%d" % i, "state": "active"} for i in range(100)]
                      + [{"location": "L", "text": "bad state", "state": "maybe"}],
            "towns": [{"name": "T%d" % i, "reputation": 1, "title": "x"} for i in range(50)],
            "karma_title": "“Hero” " + "x" * 1000,
        })
        self.assertEqual(len(s["quests"]), 40)
        self.assertEqual(len(s["towns"]), 20)
        self.assertLessEqual(len(s["karma_title"]), 300)
        self.assertTrue(all(32 <= ord(c) < 127 for c in s["karma_title"]))


class RenderTest(unittest.TestCase):
    def test_render(self):
        lines = story.render_story(story.validate_story(SNAP))
        text = "\n".join(lines)
        for needle in ("Retrieve the G.E.C.K.", "Rescue Smiley", "Klamath", "Accepted", "Defender",
                       "Vic", "Sulik", "Made Man", "Radio part for Vic", "10"):
            self.assertIn(needle, text)
        self.assertIn("31", text)  # total kills
        low = text.lower()
        self.assertIn("done", low) if "done" in low else self.assertIn("completed", low)
        self.assertIn("failed", low)

    def test_children_kills_called_out(self):
        text = "\n".join(story.render_story(story.validate_story(dict(SNAP, kills={"total": 3, "children": 1}))))
        self.assertIn("child", text.lower())

    def test_empty(self):
        self.assertEqual(story.render_story({}), [])

    def test_header_marks_ground_truth(self):
        h = story.SECTION_HEADER.lower()
        self.assertTrue("true" in h or "fact" in h)


if __name__ == "__main__":
    unittest.main()
