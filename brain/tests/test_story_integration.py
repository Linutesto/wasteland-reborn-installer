"""Whole-service story contract with a fake LLM, unchanged crew acceptance tests."""
import json
import os
import sqlite3
import time
from urllib.parse import urlencode
import unittest

import server as brain
from test_server import BrainCase, talk_body, VIC
from timeline import Store


class StoryIntegration(BrainCase):
    def post(self, **kwargs):
        status, response = self.talk(**kwargs)
        self.assertEqual(status, 200, response)
        self.assertIn('timeline', response)
        return response

    def wait_facts(self):
        self.srv.brain.story.wait()

    def test_ground_truth_and_effect_schema(self):
        self.post(timeline={'branch': ''}, story={'karma_title': 'Defender',
                  'quests': [{'location': 'Arroyo', 'text': 'Retrieve GECK', 'state': 'active'}],
                  'kills': {'total': 8, 'children': 1}},
                  allowed_effects={'side_quest': {'max_caps': 200, 'max_xp': 100, 'fetch_items': [{'pid': 19, 'name': 'Rock'}]}})
        req = self.llm.talk_requests()[-1]
        prompt = req['messages'][0]['content']
        for word in ('ground truth', 'outranks', 'Retrieve GECK', 'Defender', 'child', 'Relationship'):
            self.assertIn(word.lower(), prompt.lower())
        self.assertEqual(req['response_format']['json_schema']['schema']['properties']['effects']['maxItems'], 2)

    def test_fork_discards_future_exchange_facts_relationship_summary_and_effect(self):
        before = self.post(timeline={'branch': ''}, say='before-save')
        self.wait_facts()
        tl = before['timeline']
        mem = self.srv.brain.mem
        c = talk_body()['campaign']
        self.post(timeline=tl, say='discarded-cobalt-potato')
        self.wait_facts()
        with mem.lock:
            for kind, payload in [('fact', {'kind': 'claim', 'text': 'discarded-cobalt-potato', 'importance': 5, 'secret': False}),
                                  ('rel', {'trust': -10, 'fear': 10}), ('effect', {'type': 'discount', 'percent': 20})]:
                mem.timeline.add_row(c, tl['branch'], kind, 'vic', payload)
        mem.set_summary(c, 'vic', 'discarded-cobalt-potato', 2, 2, branch=tl['branch'])
        after = self.post(timeline=dict(tl, fork=True), say='after-load')
        self.assertNotEqual(after['timeline']['branch'], tl['branch'])
        prompt = json.dumps(self.llm.talk_requests()[-1]['messages'])
        self.assertIn('before-save', prompt)
        self.assertNotIn('discarded-cobalt-potato', prompt)
        self.assertNotIn('Previous consequence proposals', prompt)
        st, result = self.request('GET', '/v1/npc/memory?' + urlencode({'campaign': c, 'pid': VIC, 'branch': after['timeline']['branch']}))
        self.assertEqual(st, 200)
        self.assertEqual([r['player_line'] for r in result['exchanges']], ['before-save', 'after-load'])
        self.assertEqual(result['summary'], '')
        self.assertEqual(len(mem.all(c, 'vic')), 3)  # legacy inspection remains campaign-wide

    def test_async_extraction_never_delays_talk(self):
        self.llm.facts_delay = .5
        self.llm.facts_reply = {'facts': [{'kind': 'promise', 'text': 'The player promised a radio.', 'importance': 4}],
                               'relationship': {'trust': 2, 'fear': 0}}
        start = time.monotonic()
        out = self.post(timeline={'branch': ''})
        self.assertLess(time.monotonic() - start, .4)
        self.wait_facts()
        self.llm.facts_delay = 0
        self.post(timeline=out['timeline'])
        self.assertIn('The player promised a radio.', self.llm.talk_requests()[-1]['messages'][0]['content'])

    def test_relationship_gates_dedupe_and_persist(self):
        self.llm.facts_reply = {'facts': [{'kind': 'favor', 'text': 'The player helped Vic.', 'importance': 4}],
                               'relationship': {'trust': 2, 'fear': 0}}
        tl = {'branch': ''}
        bounds = {'discount': {'max_percent': 20}, 'gift': {'items': [{'pid': 40, 'name': 'Stimpak', 'max_qty': 1}]}}
        self.llm.reply['effects'] = [{'type': 'discount', 'percent': 10}, {'type': 'gift', 'pid': 40, 'qty': 1}]
        accepted = []
        for i in range(4):
            out = self.post(timeline=tl, allowed_effects=bounds)
            tl = out['timeline']
            accepted.append([e['type'] for e in out['effects']])
            self.wait_facts()
        self.assertEqual(accepted, [[], [], ['discount'], ['discount', 'gift']])
        mem = self.srv.brain.mem
        c = talk_body()['campaign']
        self.assertEqual(len(mem.rows(c, tl['branch'], 'fact', 'vic')), 1)
        self.restart()
        self.post(timeline=tl)
        self.assertIn('helped Vic', self.llm.talk_requests()[-1]['messages'][0]['content'])

    def test_gossip_time_source_and_branch_visibility(self):
        tl = self.post(timeline={'branch': ''})['timeline']
        self.wait_facts()
        mem = self.srv.brain.mem
        c = talk_body()['campaign']
        with mem.lock:
            mem.timeline.add_row(c, tl['branch'], 'fact', 'vic',
                                 {'kind': 'info', 'text': 'The player rescued a caravan.', 'importance': 4, 'secret': False},
                                 game_ticks=10, map='ARVILLAG', team=3, npc_name='Vic')
            head = mem.timeline.head(c)
        witness = dict(talk_body()['npc'], pid=16777290, name='Witness', instance='22')
        for ticks, expected in ((864009, False), (864010, True)):
            self.post(timeline={'branch': tl['branch'], 'head': head}, npc=witness, story={'game_ticks': ticks, 'npc_team': 8})
            prompt = self.llm.talk_requests()[-1]['messages'][0]['content']
            self.assertEqual('caravan' in prompt, expected)
            if expected:
                self.assertIn('Vic', prompt)
        self.post(timeline=dict(tl, fork=True), npc=dict(witness, instance='23'), story={'game_ticks': 864010, 'npc_team': 8})
        self.assertNotIn('caravan', self.llm.talk_requests()[-1]['messages'][0]['content'])

    def test_side_quest_duplicate_rejected_and_abandonment_uses_engine_truth(self):
        q = {'type': 'side_quest', 'title': 'Rock', 'objective': 'Bring rock', 'kind': 'fetch', 'pid': 19,
             'qty': 1, 'reward_caps': 100, 'reward_xp': 50}
        self.llm.reply['effects'] = [q, q]
        bounds = {'side_quest': {'max_caps': 200, 'max_xp': 100, 'fetch_items': [{'pid': 19, 'name': 'Rock'}]}}
        first = self.post(timeline={'branch': ''}, allowed_effects=bounds)
        self.assertEqual(len(first['effects']), 1)
        active = self.post(timeline=first['timeline'], allowed_effects=bounds)
        self.assertEqual(active['effects'], [])
        abandoned = self.post(timeline=active['timeline'], allowed_effects=bounds, story={'wasteland': {'quests': []}})
        self.assertEqual(len(abandoned['effects']), 1)

    def test_malformed_new_fields_rejected_without_crashing(self):
        for field, value in [('timeline', []), ('timeline', {'head': True}), ('timeline', {'head': -1}),
                             ('timeline', {'fork': 1}), ('story', []), ('allowed_effects', [])]:
            status, _ = self.talk(**{field: value})
            self.assertEqual(status, 422, (field, value))
        self.post(timeline={'branch': 'unknown-branch', 'head': 42, 'fork': True})

    def test_other_campaign_branch_is_not_adopted(self):
        first = self.post(campaign='private', timeline={'branch': ''}, say='private passphrase')
        self.post(campaign='public', timeline=first['timeline'])
        self.assertNotIn('private passphrase', json.dumps(self.llm.talk_requests()[-1]['messages']))

    def test_malformed_nested_effect_bounds_fail_closed(self):
        self.llm.reply['effects'] = [{'type': 'gift', 'pid': 40, 'qty': 1}]
        for bounds in ({'gift': {'items': 8}}, {'gift': {'items': [{'pid': True, 'name': 8, 'max_qty': 1}]}},
                       {'reveal_location': {'names': 42}}, {'side_quest': {'fetch_items': True}},
                       {'discount': {'max_percent': True}}, {'turn_hostile': []}):
            out = self.post(timeline={'branch': ''}, allowed_effects=bounds)
            self.assertEqual(out['effects'], [])

    def test_original_database_migration_and_legacy_adoption(self):
        self.stop()
        path = os.path.join(self.tmp, 'brain.db')
        os.unlink(path)
        db = sqlite3.connect(path)
        db.executescript(brain.SCHEMA)
        db.execute('INSERT INTO exchanges(campaign,npc_id,ts,pid,player_line,npc_line) VALUES(?,?,?,?,?,?)',
                   ('old-campaign','vic',1,VIC,'old remembered line','Hello'))
        db.execute('INSERT INTO summaries VALUES(?,?,?,?,?,?)', ('old-campaign','vic','Old summary',1,1,1))
        db.commit(); db.close()
        self.start()
        out = self.post(campaign='old-campaign', timeline={'branch': ''})
        prompt = json.dumps(self.llm.talk_requests()[-1]['messages'])
        self.assertIn('old remembered line', prompt)
        self.assertIn('Old summary', prompt)
        self.assertGreaterEqual(out['timeline']['head'], 3)
        self.wait_facts()
        self.restart()
        self.post(campaign='old-campaign', timeline=out['timeline'])
        self.assertEqual(len(self.srv.brain.mem.all('old-campaign', 'vic')), 3)


class AdditionalTimelineTests(unittest.TestCase):
    def test_nested_fork_can_narrow_below_parent_fork(self):
        connection = sqlite3.connect(':memory:')
        self.addCleanup(connection.close)
        store = Store(connection)
        root, _ = store.resolve('c', {'branch': ''})
        for text in ('a', 'b', 'c'):
            store.add_row('c', root, 'fact', 'vic', {'text': text})
        a, _ = store.resolve('c', {'branch': root, 'head': 3, 'fork': True})
        b, _ = store.resolve('c', {'branch': a, 'head': 1, 'fork': True})
        self.assertEqual([r['payload']['text'] for r in store.visible_rows('c', b, 'fact')], ['a'])

    def test_false_and_infinite_model_integers_are_ignored(self):
        import facts
        parsed, rel = facts.parse_extraction('{"facts":[],"relationship":{"trust":true,"fear":1e999}}')
        self.assertEqual(rel, {'trust': 0, 'fear': 0})

if __name__ == '__main__':
    unittest.main()
