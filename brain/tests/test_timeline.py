"""timeline.Store: branches, per-campaign seq, branch-visible rows (SPEC.md section 2)."""
import os
import sqlite3
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from timeline import Store, LEGACY_PREFIX  # noqa: E402


class TimelineTest(unittest.TestCase):
    def setUp(self):
        self.db = sqlite3.connect(":memory:")
        self.s = Store(self.db)

    def test_legacy_prefix(self):
        self.assertEqual(LEGACY_PREFIX, "legacy:")

    def test_no_timeline_is_legacy_branch(self):
        b, created = self.s.resolve("c1", None)
        self.assertEqual(b, "legacy:c1")
        b2, _ = self.s.resolve("c1", None)
        self.assertEqual(b2, b)

    def test_empty_branch_creates_root(self):
        b, created = self.s.resolve("c1", {"branch": "", "head": 0, "fork": False})
        self.assertTrue(created)
        self.assertTrue(b.startswith("b-"))
        self.assertNotEqual(self.s.resolve("c1", {"branch": ""})[0], b)  # each new game: new root

    def test_seq_is_monotonic_per_campaign(self):
        b, _ = self.s.resolve("c1", {"branch": ""})
        s1 = self.s.add_row("c1", b, "fact", "vic", {"text": "a"})
        s2 = self.s.add_row("c1", b, "fact", "vic", {"text": "b"})
        o1 = self.s.add_row("c2", "legacy:c2", "fact", "vic", {"text": "x"})
        self.assertEqual(s2, s1 + 1)
        self.assertEqual(o1, 1)
        self.assertEqual(self.s.head("c1"), s2)

    def test_fork_hides_rows_after_the_save(self):
        root, _ = self.s.resolve("c1", {"branch": ""})
        self.s.add_row("c1", root, "fact", "vic", {"text": "before save"})
        head = self.s.head("c1")
        self.s.add_row("c1", root, "fact", "vic", {"text": "after save, then reloaded"})
        child, created = self.s.resolve("c1", {"branch": root, "head": head, "fork": True})
        self.assertTrue(created)
        self.assertNotEqual(child, root)
        self.s.add_row("c1", child, "fact", "vic", {"text": "new timeline"})
        texts = [r["payload"]["text"] for r in self.s.visible_rows("c1", child, "fact")]
        self.assertEqual(texts, ["before save", "new timeline"])
        # the root still sees its own rows
        texts_root = [r["payload"]["text"] for r in self.s.visible_rows("c1", root, "fact")]
        self.assertEqual(texts_root, ["before save", "after save, then reloaded"])

    def test_nested_forks_narrow_the_horizon(self):
        root, _ = self.s.resolve("c1", {"branch": ""})
        self.s.add_row("c1", root, "fact", "vic", {"text": "r1"})  # seq 1
        self.s.add_row("c1", root, "fact", "vic", {"text": "r2"})  # seq 2
        a, _ = self.s.resolve("c1", {"branch": root, "head": 2, "fork": True})
        self.s.add_row("c1", a, "fact", "vic", {"text": "a1"})  # seq 3
        b, _ = self.s.resolve("c1", {"branch": a, "head": 3, "fork": True})
        self.s.add_row("c1", root, "fact", "vic", {"text": "r3-late"})  # seq 4, root only
        self.s.add_row("c1", b, "fact", "vic", {"text": "b1"})
        texts = [r["payload"]["text"] for r in self.s.visible_rows("c1", b, "fact")]
        self.assertEqual(texts, ["r1", "r2", "a1", "b1"])
        # fork of the root at seq 1 only sees r1
        c, _ = self.s.resolve("c1", {"branch": root, "head": 1, "fork": True})
        self.assertEqual([r["payload"]["text"] for r in self.s.visible_rows("c1", c, "fact")], ["r1"])

    def test_not_fork_reuses_branch(self):
        root, _ = self.s.resolve("c1", {"branch": ""})
        same, created = self.s.resolve("c1", {"branch": root, "head": 0, "fork": False})
        self.assertEqual(same, root)
        self.assertFalse(created)

    def test_unknown_branch_becomes_new_root(self):
        b, created = self.s.resolve("c1", {"branch": "b-doesnotexist", "head": 5, "fork": True})
        self.assertTrue(created)
        self.assertTrue(b.startswith("b-"))
        self.assertEqual(self.s.visible_rows("c1", b, "fact"), [])

    def test_branch_of_other_campaign_is_unknown(self):
        b1, _ = self.s.resolve("c1", {"branch": ""})
        b2, created = self.s.resolve("c2", {"branch": b1, "fork": False})
        self.assertTrue(created)
        self.assertNotEqual(b2, b1)

    def test_legacy_rows_adopted_by_first_root(self):
        self.s.add_row("c1", "legacy:c1", "fact", "vic", {"text": "old"})
        root, _ = self.s.resolve("c1", {"branch": ""})
        self.assertEqual([r["payload"]["text"] for r in self.s.visible_rows("c1", root, "fact")], ["old"])
        self.s.add_row("c1", "legacy:c1", "fact", "vic", {"text": "old-later"})  # after adoption
        self.assertEqual([r["payload"]["text"] for r in self.s.visible_rows("c1", root, "fact")], ["old"])

    def test_filters_and_row_shape(self):
        b, _ = self.s.resolve("c1", {"branch": ""})
        self.s.add_row("c1", b, "fact", "vic", {"text": "v"}, game_ticks=100, map="ARVILLAG", team=1, npc_name="Vic")
        self.s.add_row("c1", b, "fact", "sulik", {"text": "s"})
        self.s.add_row("c1", b, "rel", "vic", {"trust": 1, "fear": 0})
        rows = self.s.visible_rows("c1", b, "fact", npc_id="vic")
        self.assertEqual(len(rows), 1)
        r = rows[0]
        for key in ("seq", "branch", "kind", "npc_id", "payload", "game_ticks", "map", "team", "npc_name", "ts"):
            self.assertIn(key, r)
        self.assertEqual((r["game_ticks"], r["map"], r["team"], r["npc_name"]), (100, "ARVILLAG", 1, "Vic"))
        self.assertEqual(len(self.s.visible_rows("c1", b, "fact")), 2)
        self.assertEqual(len(self.s.visible_rows("c1", b, None)), 3)  # None = every kind

    def test_branch_visible_seq_predicate(self):
        """visible_spec(): [(branch, horizon or None)] for joining other tables (exchanges)."""
        root, _ = self.s.resolve("c1", {"branch": ""})
        self.s.add_row("c1", root, "fact", "vic", {"text": "r1"})
        child, _ = self.s.resolve("c1", {"branch": root, "head": 1, "fork": True})
        spec = self.s.visible_spec("c1", child)
        self.assertEqual(spec[0], (child, None))
        self.assertIn((root, 1), spec)

    def test_persistent_file(self):
        import tempfile
        with tempfile.TemporaryDirectory() as d:
            path = os.path.join(d, "t.db")
            s = Store(sqlite3.connect(path))
            b, _ = s.resolve("c1", {"branch": ""})
            s.add_row("c1", b, "fact", "vic", {"text": "kept"})
            s2 = Store(sqlite3.connect(path))
            self.assertEqual([r["payload"]["text"] for r in s2.visible_rows("c1", b, "fact")], ["kept"])
            self.assertEqual(s2.head("c1"), 1)


if __name__ == "__main__":
    unittest.main()
