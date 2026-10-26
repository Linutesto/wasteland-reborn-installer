"""gossip.rumors_for: who hears what, when (SPEC.md section 4)."""
import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import gossip  # noqa: E402

DAY = 864000


def fact(seq, npc_id, text, imp=3, secret=False, ticks=0, map_="DEN", team=5, name=None):
    return {"seq": seq, "npc_id": npc_id, "npc_name": name or npc_id.title(), "game_ticks": ticks,
            "map": map_, "team": team, "payload": {"kind": "info", "text": text, "importance": imp, "secret": secret}}


class GossipTest(unittest.TestCase):
    def test_constants(self):
        self.assertEqual(gossip.SAME_MAP_DELAY, DAY)
        self.assertEqual(gossip.SAME_TEAM_DELAY, 3 * DAY)

    def test_same_map_after_one_day(self):
        rows = [fact(1, "becky", "The player robbed the casino.", ticks=0, map_="DEN", team=7)]
        me = {"npc_id": "joey", "map": "DEN", "team": 9}
        self.assertEqual(gossip.rumors_for(me, rows, now_ticks=DAY - 1), [])
        got = gossip.rumors_for(me, rows, now_ticks=DAY)
        self.assertEqual(got, [{"source": "Becky", "text": "The player robbed the casino.", "seq": 1}])

    def test_same_team_elsewhere_after_three_days(self):
        rows = [fact(1, "slaver1", "The player freed slaves.", ticks=10, map_="DEN", team=5)]
        me = {"npc_id": "slaver2", "map": "REDDING", "team": 5}
        self.assertEqual(gossip.rumors_for(me, rows, now_ticks=10 + 3 * DAY - 1), [])
        self.assertEqual(len(gossip.rumors_for(me, rows, now_ticks=10 + 3 * DAY)), 1)

    def test_other_map_other_team_never(self):
        rows = [fact(1, "a", "x", map_="DEN", team=5)]
        self.assertEqual(gossip.rumors_for({"npc_id": "b", "map": "KLAMATH", "team": 6}, rows, now_ticks=100 * DAY), [])

    def test_filters(self):
        rows = [
            fact(1, "joey", "my own fact"),                       # own
            fact(2, "a", "secret", secret=True),                    # secret
            fact(3, "b", "minor", imp=2),                            # unimportant
            fact(4, "c", "ok"),
        ]
        got = gossip.rumors_for({"npc_id": "joey", "map": "DEN", "team": 5}, rows, now_ticks=10 * DAY)
        self.assertEqual([g["text"] for g in got], ["ok"])

    def test_missing_team_or_map_is_not_a_match(self):
        rows = [fact(1, "a", "t", map_=None, team=None)]
        self.assertEqual(gossip.rumors_for({"npc_id": "b", "map": None, "team": None}, rows, now_ticks=10 * DAY), [])

    def test_limit_importance_then_newest_and_dedupe(self):
        rows = [fact(i, "n%d" % i, "rumor %d" % i, imp=3 + (i % 3)) for i in range(1, 10)]
        rows.append(fact(20, "zz", "rumor 8", imp=5))  # same text as seq 8 → one rumor
        got = gossip.rumors_for({"npc_id": "me", "map": "DEN", "team": 5}, rows, now_ticks=10 * DAY, limit=4)
        self.assertEqual(len(got), 4)
        self.assertEqual(len({g["text"] for g in got}), 4)
        self.assertEqual(got[0]["text"], "rumor 8")
        self.assertEqual(got[0]["seq"], 20)

    def test_no_now_ticks_means_no_rumors(self):
        rows = [fact(1, "a", "t")]
        self.assertEqual(gossip.rumors_for({"npc_id": "b", "map": "DEN", "team": 5}, rows, now_ticks=None), [])

    def test_prompt_lines(self):
        lines = gossip.prompt_lines([{"source": "Becky", "text": "The player robbed the casino.", "seq": 1}])
        self.assertEqual(len(lines), 1)
        self.assertIn("Becky", lines[0])
        self.assertIn("robbed the casino", lines[0])


if __name__ == "__main__":
    unittest.main()
