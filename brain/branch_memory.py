"""Branch-aware SQLite exchanges and immutable summary versions.

The timeline row and its exchange share a campaign sequence. Summary versions
are timeline rows, so a fork can never inherit a summary of a discarded future.
"""
import json
import os
import sqlite3
import threading
import time

from timeline import Store, LEGACY_PREFIX


class BranchView:
    def __init__(self, memory, branch):
        self.memory, self.branch = memory, branch

    def __getattr__(self, name):
        fn = getattr(self.memory, name)
        return lambda *a, **kw: fn(*a, branch=self.branch, **kw)


class BranchMemory:
    def __init__(self, path, schema, columns):
        os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
        self.lock = threading.RLock()
        self.columns = columns
        self.db = sqlite3.connect(path, check_same_thread=False, timeout=30)
        self.db.execute('PRAGMA journal_mode=WAL')
        self.db.execute('PRAGMA busy_timeout=30000')
        self.db.executescript(schema)
        for table in ('exchanges', 'summaries'):
            cols = {r[1] for r in self.db.execute('PRAGMA table_info(%s)' % table)}
            for name, kind in (('branch', 'TEXT'), ('seq', 'INTEGER')):
                if name not in cols:
                    self.db.execute('ALTER TABLE %s ADD COLUMN %s %s' % (table, name, kind))
        self.db.commit()
        self.timeline = Store(self.db)
        # One reentrant lock covers every user of this shared connection.
        self.timeline._lock = self.lock
        self._migrate()

    def _migrate(self):
        with self.lock:
            old = self.db.execute('SELECT id,campaign,npc_id FROM exchanges WHERE seq IS NULL ORDER BY id').fetchall()
            for ident, campaign, npc in old:
                branch = LEGACY_PREFIX + campaign
                self.timeline.resolve(campaign, None)
                prior = self.db.execute("SELECT seq FROM rows WHERE campaign=? AND kind='exchange' "
                                        "AND json_extract(payload,'$.exchange_id')=?", (campaign, ident)).fetchone()
                seq = prior[0] if prior else self.timeline.add_row(campaign, branch, 'exchange', npc, {'exchange_id': ident})
                self.db.execute('UPDATE exchanges SET branch=?,seq=? WHERE id=?', (branch, seq, ident))
                self.db.commit()
            for campaign, npc, summary, covered, total in self.db.execute(
                    'SELECT campaign,npc_id,summary,covered_upto,total_at FROM summaries WHERE seq IS NULL').fetchall():
                branch = LEGACY_PREFIX + campaign
                seq = self.timeline.add_row(campaign, branch, 'summary', npc,
                                            {'summary': summary, 'covered_upto': covered, 'total_at': total})
                self.db.execute('UPDATE summaries SET branch=?,seq=? WHERE campaign=? AND npc_id=?',
                                (branch, seq, campaign, npc))
            self.db.commit()

    def close(self):
        with self.lock:
            self.db.close()

    def view(self, branch):
        return BranchView(self, branch)

    def add(self, campaign, npc_id, row, branch=None):
        branch = branch or LEGACY_PREFIX + campaign
        cols = [c for c in self.columns if c != 'id']
        with self.lock:
            cur = self.db.execute('INSERT INTO exchanges (campaign,npc_id,%s,branch) VALUES (?,?,%s,?)' %
                                  (','.join(cols), ','.join('?' for _ in cols)),
                                  [campaign, npc_id] + [row.get(c) for c in cols] + [branch])
            ident = cur.lastrowid
            seq = self.timeline.add_row(campaign, branch, 'exchange', npc_id, {'exchange_id': ident})
            self.db.execute('UPDATE exchanges SET seq=? WHERE id=?', (seq, ident))
            self.db.commit()
            return ident

    def exchange_seq(self, ident):
        with self.lock:
            return self.db.execute('SELECT seq FROM exchanges WHERE id=?', (ident,)).fetchone()[0]

    def _predicate(self, campaign, branch):
        if branch is None or branch == LEGACY_PREFIX + campaign:
            return '', []  # original engines retain their campaign-wide legacy view
        spec = self.timeline.visible_spec(campaign, branch)
        clauses, args = [], []
        for bid, horizon in spec:
            clauses.append('(branch=?%s)' % (' AND seq<=?' if horizon is not None else ''))
            args.append(bid)
            if horizon is not None:
                args.append(horizon)
        return ' AND (' + ' OR '.join(clauses) + ')', args

    def all(self, campaign, npc_id, branch=None):
        with self.lock:
            predicate, args = self._predicate(campaign, branch)
            cols = list(self.columns) + ['branch', 'seq']
            cur = self.db.execute('SELECT %s FROM exchanges WHERE campaign=? AND npc_id=?%s ORDER BY seq,id' %
                                  (','.join(cols), predicate), [campaign, npc_id] + args)
            return [dict(zip(cols, r)) for r in cur.fetchall()]

    def recent(self, campaign, npc_id, n=8, branch=None):
        return self.all(campaign, npc_id, branch)[-n:] if n else []

    def first(self, campaign, npc_id, branch=None):
        rows = self.all(campaign, npc_id, branch)
        return rows[0] if rows else None

    def count(self, campaign, npc_id, branch=None):
        return len(self.all(campaign, npc_id, branch))

    def rows(self, campaign, branch, kind=None, npc_id=None):
        with self.lock:
            if branch != LEGACY_PREFIX + campaign:
                return self.timeline.visible_rows(campaign, branch, kind, npc_id)
            # Legacy clients historically inspect all NPC memories in the campaign.
            sql = 'SELECT seq,branch,kind,npc_id,payload,game_ticks,map,team,npc_name,ts FROM rows WHERE campaign=?'
            args = [campaign]
            for key, val in (('kind', kind), ('npc_id', npc_id)):
                if val is not None:
                    sql += ' AND %s=?' % key
                    args.append(val)
            keys = ('seq','branch','kind','npc_id','payload','game_ticks','map','team','npc_name','ts')
            rows = [dict(zip(keys, r)) for r in self.db.execute(sql+' ORDER BY seq', args)]
            for row in rows:
                row['payload'] = json.loads(row['payload'])
            return rows

    def summary(self, campaign, npc_id, branch=None):
        rows = self.rows(campaign, branch or LEGACY_PREFIX + campaign, 'summary', npc_id)
        return rows[-1]['payload'] if rows else {'summary': '', 'covered_upto': 0, 'total_at': 0}

    def set_summary(self, campaign, npc_id, text, covered_upto, total_at, branch=None):
        branch = branch or LEGACY_PREFIX + campaign
        with self.lock:
            payload = {'summary': text, 'covered_upto': covered_upto, 'total_at': total_at}
            seq = self.timeline.add_row(campaign, branch, 'summary', npc_id, payload)
            self.db.execute('INSERT INTO summaries (campaign,npc_id,summary,covered_upto,total_at,updated_ts,branch,seq) '
                            'VALUES (?,?,?,?,?,?,?,?) ON CONFLICT(campaign,npc_id) DO UPDATE SET '
                            'summary=excluded.summary,covered_upto=excluded.covered_upto,total_at=excluded.total_at,'
                            'updated_ts=excluded.updated_ts,branch=excluded.branch,seq=excluded.seq',
                            (campaign,npc_id,text,covered_upto,total_at,time.time(),branch,seq))
            self.db.commit()

    def unsummarized_old(self, campaign, npc_id, covered_upto, keep=8, branch=None):
        rows = self.all(campaign, npc_id, branch)
        old = rows[:-keep] if keep else rows
        return [r for r in old if r['id'] > covered_upto]
