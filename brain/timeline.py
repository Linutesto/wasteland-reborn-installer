"""Save-bound memory timelines (SPEC.md section 2).

Every stored row (exchange, fact, relationship delta, gossip, effect) belongs
to a *branch* and carries a per-campaign monotonic ``seq``. Loading an older
save creates a child branch forked at the saved head, so rows written after
the save stop being visible on the new timeline; the old timeline still sees
them.

Schema (created by :class:`Store` on first use)::

    branches(id TEXT PK, campaign TEXT, parent_id TEXT NULL,
             fork_seq INTEGER NULL, created_ts REAL)
    rows(seq INTEGER, campaign TEXT, branch TEXT, kind TEXT, npc_id TEXT,
         payload TEXT (JSON), game_ticks INTEGER NULL, map TEXT NULL,
         team INTEGER NULL, npc_name TEXT NULL, ts REAL,
         PRIMARY KEY (campaign, seq))

Visibility: a row is visible on branch B if it is on B, or on an ancestor A
of B with ``row.seq <= fork_seq`` of the child of A on the path to B (walk up
the parent chain; each hop narrows the horizon to ``min(horizon, fork_seq)``).

Thread safety: one lock serializes operations per :class:`Store`; the
underlying sqlite3 connection must be created with the default (per-thread
or shared) usage of the caller — :class:`Store` itself never opens one.
"""

from __future__ import annotations

import json
import sqlite3
import threading
import uuid

#: Legacy branch id prefix: ``legacy:<campaign>`` holds all pre-timeline rows.
LEGACY_PREFIX = "legacy:"

_SCHEMA = """
CREATE TABLE IF NOT EXISTS branches (
    id          TEXT PRIMARY KEY,
    campaign    TEXT NOT NULL,
    parent_id   TEXT,
    fork_seq    INTEGER,
    created_ts  REAL NOT NULL
);
CREATE TABLE IF NOT EXISTS rows (
    seq        INTEGER NOT NULL,
    campaign   TEXT NOT NULL,
    branch     TEXT NOT NULL,
    kind       TEXT NOT NULL,
    npc_id     TEXT NOT NULL,
    payload    TEXT NOT NULL,
    game_ticks INTEGER,
    map        TEXT,
    team       INTEGER,
    npc_name   TEXT,
    ts         REAL NOT NULL,
    PRIMARY KEY (campaign, seq)
);
CREATE INDEX IF NOT EXISTS idx_rows_branch ON rows (campaign, branch);
"""


def _now() -> float:
    """Current unix timestamp (second resolution is plenty here)."""
    import time

    return time.time()


class Store:
    """Branch store over a caller-supplied sqlite3 connection.

    Creates its own tables (``branches`` + ``rows``). All writes commit
    before returning. All public methods are safe to call from multiple
    threads (serialized by an internal lock).
    """

    def __init__(self, conn: sqlite3.Connection) -> None:
        self._conn = conn
        self._lock = threading.Lock()
        with self._lock:
            cur = self._conn.execute(
                "SELECT COUNT(*) FROM pragma_table_list WHERE name IN ('branches','rows')"
            )
            if cur.fetchone()[0] < 2:
                self._conn.executescript(_SCHEMA)
                self._conn.commit()

    # ------------------------------------------------------------------ #
    # branches
    # ------------------------------------------------------------------ #

    def _get_branch(self, branch_id: str, campaign: str) -> dict | None:
        cur = self._conn.execute(
            "SELECT id, campaign, parent_id, fork_seq FROM branches WHERE id = ? AND campaign = ?",
            (branch_id, campaign),
        )
        row = cur.fetchone()
        if row is None:
            return None
        return {"id": row[0], "campaign": row[1], "parent_id": row[2], "fork_seq": row[3]}

    def _insert_branch(self, branch_id: str, campaign: str, parent_id: str | None, fork_seq: int | None) -> None:
        self._conn.execute(
            "INSERT INTO branches (id, campaign, parent_id, fork_seq, created_ts) VALUES (?, ?, ?, ?, ?)",
            (branch_id, campaign, parent_id, fork_seq, _now()),
        )

    @staticmethod
    def _legacy_branch(campaign: str) -> str:
        return LEGACY_PREFIX + campaign

    def _legacy_head(self, campaign: str) -> int:
        cur = self._conn.execute(
            "SELECT COALESCE(MAX(seq), 0) FROM rows WHERE campaign = ? AND branch = ?",
            (campaign, self._legacy_branch(campaign)),
        )
        return cur.fetchone()[0]

    def resolve(self, campaign: str, timeline_dict: dict | None) -> tuple[str, bool]:
        """Resolve a request's ``timeline`` field to a branch id.

        Returns ``(branch_id, created)`` where ``created`` is True when a new
        branch row was inserted. Rules (SPEC.md section 2):

        * ``timeline_dict`` is None (old engine) → legacy branch
          ``legacy:<campaign>``, never created here.
        * ``branch`` empty/missing → new root branch. If the legacy branch has
          any rows they are adopted: parent = legacy branch, fork_seq = its
          current max seq.
        * ``fork: true`` → new child of ``branch`` with fork_seq = head.
          Unknown parent (replaced database, other campaign) → new root.
        * Otherwise → the given ``branch`` as-is, if it exists for this
          campaign; unknown → new root (a talk never fails because of the
          timeline).
        """
        with self._lock:
            if timeline_dict is None:
                legacy = self._legacy_branch(campaign)
                if self._get_branch(legacy, campaign) is None:
                    self._insert_branch(legacy, campaign, None, None)
                    self._conn.commit()
                return legacy, False

            branch = (timeline_dict.get("branch") or "").strip()
            head = int(timeline_dict.get("head") or 0)
            fork = bool(timeline_dict.get("fork"))

            if not branch:
                new_id = "b-" + uuid.uuid4().hex
                legacy = self._legacy_branch(campaign)
                legacy_head = self._legacy_head(campaign)
                parent, fork_seq = (legacy, legacy_head) if legacy_head else (None, None)
                self._insert_branch(new_id, campaign, parent, fork_seq)
                self._conn.commit()
                return new_id, True

            parent = self._get_branch(branch, campaign)
            if parent is None:
                # Unknown branch id (database replaced / other campaign):
                # a talk never fails because of the timeline.
                new_id = "b-" + uuid.uuid4().hex
                self._insert_branch(new_id, campaign, None, None)
                self._conn.commit()
                return new_id, True

            if not fork:
                return branch, False

            new_id = "b-" + uuid.uuid4().hex
            self._insert_branch(new_id, campaign, branch, head)
            self._conn.commit()
            return new_id, True

    # ------------------------------------------------------------------ #
    # rows
    # ------------------------------------------------------------------ #

    def add_row(
        self,
        campaign: str,
        branch: str,
        kind: str,
        npc_id: str,
        payload: dict,
        game_ticks: int | None = None,
        map: str | None = None,
        team: int | None = None,
        npc_name: str | None = None,
    ) -> int:
        """Append a row under ``branch`` and return its campaign seq (starts at 1)."""
        with self._lock:
            cur = self._conn.execute(
                "SELECT COALESCE(MAX(seq), 0) + 1 FROM rows WHERE campaign = ?",
                (campaign,),
            )
            seq = cur.fetchone()[0]
            self._conn.execute(
                """INSERT INTO rows
                   (seq, campaign, branch, kind, npc_id, payload,
                    game_ticks, map, team, npc_name, ts)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    seq,
                    campaign,
                    branch,
                    kind,
                    npc_id,
                    json.dumps(payload, ensure_ascii=False),
                    game_ticks,
                    map,
                    team,
                    npc_name,
                    _now(),
                ),
            )
            self._conn.commit()
            return seq

    def head(self, campaign: str) -> int:
        """Highest seq written for this campaign (0 if none)."""
        with self._lock:
            cur = self._conn.execute(
                "SELECT COALESCE(MAX(seq), 0) FROM rows WHERE campaign = ?",
                (campaign,),
            )
            return cur.fetchone()[0]

    # ------------------------------------------------------------------ #
    # visibility
    # ------------------------------------------------------------------ #

    def _walk_to_root(self, campaign: str, branch: str) -> list[tuple[str, int | None]]:
        """Path from ``branch`` up to its root: ``[(id, fork_seq), ...]``,
        own branch first with horizon None. Unknown branches yield
        ``[(branch, None)]`` (treated as their own root)."""
        spec: list[tuple[str, int | None]] = [(branch, None)]
        node = self._get_branch(branch, campaign)
        horizon = None
        seen = {branch}
        while node is not None and node["parent_id"]:
            bid = node["parent_id"]
            if bid in seen:
                break
            seen.add(bid)
            cutoff = node["fork_seq"]
            horizon = cutoff if horizon is None else min(horizon, cutoff)
            spec.append((bid, horizon))
            node = self._get_branch(bid, campaign)
        return spec

    def visible_spec(self, campaign: str, branch: str) -> list[tuple[str, int | None]]:
        """Visibility predicate as ``[(branch_id, horizon_or_None), ...]``.

        First entry is always ``(branch, None)``. Each ancestor entry carries
        the fork_seq of the child below it, so a row on ancestor A with
        ``seq <= horizon`` is visible. For joining other tables (e.g.
        exchanges) from outside this module.
        """
        with self._lock:
            return self._walk_to_root(campaign, branch)

    def visible_rows(
        self,
        campaign: str,
        branch: str,
        kind: str | None = None,
        npc_id: str | None = None,
    ) -> list[dict]:
        """All rows visible on ``branch``, ordered by seq ascending.

        ``kind=None`` matches every kind; ``npc_id`` is an exact-match filter.
        """
        with self._lock:
            spec = self._walk_to_root(campaign, branch)
            where: list[str] = ["campaign = ?"]
            args: list[object] = []
            clauses = []
            args.append(campaign)
            for bid, horizon in spec:
                clause = "branch = ?"
                args.append(bid)
                if horizon is not None:
                    clause += " AND seq <= ?"
                    args.append(horizon)
                clauses.append(clause)
            where.append("(" + " OR ".join(clauses) + ")")

            if kind is not None:
                where.append("kind = ?")
                args.append(kind)
            if npc_id is not None:
                where.append("npc_id = ?")
                args.append(npc_id)

            cur = self._conn.execute(
                """SELECT seq, branch, kind, npc_id, payload, game_ticks, map, team, npc_name, ts
                   FROM rows WHERE {} ORDER BY seq ASC""".format(" AND ".join(where)),
                args,
            )
            return [
                {
                    "seq": r[0],
                    "branch": r[1],
                    "kind": r[2],
                    "npc_id": r[3],
                    "payload": json.loads(r[4]),
                    "game_ticks": r[5],
                    "map": r[6],
                    "team": r[7],
                    "npc_name": r[8],
                    "ts": r[9],
                }
                for r in cur.fetchall()
            ]
