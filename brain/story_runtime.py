"""Story context, constrained proposals, and background fact extraction."""
import json
import threading

import effects
import facts
import gossip

EXTRACTION_SCHEMA = {
    'type': 'json_schema', 'json_schema': {'name': 'facts', 'schema': {
        'type': 'object', 'properties': {
            'facts': {'type': 'array', 'maxItems': 3, 'items': {
                'type': 'object', 'properties': {
                    'kind': {'enum': list(facts.KINDS)}, 'text': {'type': 'string', 'maxLength': 200},
                    'importance': {'type': 'integer', 'minimum': 1, 'maximum': 5},
                    'secret': {'type': 'boolean'}},
                'required': ['kind', 'text', 'importance', 'secret'], 'additionalProperties': False}},
            'relationship': {'type': 'object', 'properties': {
                'trust': {'type': 'integer', 'minimum': -2, 'maximum': 2},
                'fear': {'type': 'integer', 'minimum': -2, 'maximum': 2}},
                'required': ['trust', 'fear'], 'additionalProperties': False}},
        'required': ['facts', 'relationship'], 'additionalProperties': False}}}


class StoryRuntime:
    def __init__(self, brain, llm_call):
        self.brain, self.llm_call = brain, llm_call
        self.lock = threading.Lock()
        self.threads = []
        self.stopping = False

    def context(self, campaign, branch, npc_id, req):
        mem = self.brain.mem
        relationship = facts.sum_relationship([r['payload'] for r in mem.rows(campaign, branch, 'rel', npc_id)])
        rows = mem.rows(campaign, branch, 'fact', npc_id)
        lines = ['Relationship: ' + facts.relationship_words(relationship)]
        lines.extend(facts.prompt_lines(facts.select_facts(rows, 8)))
        snapshot = req.get('story') or {}
        rumors = gossip.rumors_for({'npc_id': npc_id, 'map': req['npc'].get('map'), 'team': snapshot.get('npc_team')},
                                  mem.rows(campaign, branch, 'fact'), now_ticks=snapshot.get('game_ticks'), limit=4)
        lines.extend(gossip.prompt_lines(rumors))
        past = mem.rows(campaign, branch, 'effect', npc_id)[-4:]
        if past:
            lines.append('Previous consequence proposals (the current engine story confirms what actually happened):')
            lines.extend(json.dumps(r['payload'], ensure_ascii=True) for r in past)
        return lines, relationship

    def validate_and_store(self, campaign, branch, npc_id, req, proposed, mood):
        mem = self.brain.mem
        # The live engine snapshot is authoritative after an abandonment or a load.
        wasteland = (req.get('story') or {}).get('wasteland')
        with mem.lock:
            if isinstance(wasteland, dict):
                active = sum(q.get('state') == 'active' and q.get('giver') == req['npc']['name']
                             for q in wasteland.get('quests', []))
            else:
                active = 0
                for row in mem.rows(campaign, branch, 'effect', npc_id):
                    if row['payload'].get('type') == 'side_quest':
                        active = 1
                    elif row['payload'].get('type') == 'complete_quest':
                        active = 0
            accepted, dropped = effects.validate_effects(proposed, req.get('allowed_effects') or {},
                                                         req.get('_relationship') or {}, mood, active_quests=active)
            for effect in accepted:
                mem.timeline.add_row(campaign, branch, 'effect', npc_id, effect, **self.metadata(req))
        if dropped:
            self.brain.log('talk.jsonl', {'event': 'effects_dropped', 'campaign': campaign, 'npc': npc_id, 'reasons': dropped})
        return accepted

    @staticmethod
    def metadata(req):
        snapshot = req.get('story') or {}
        return {'game_ticks': snapshot.get('game_ticks'), 'map': req['npc'].get('map'),
                'team': snapshot.get('npc_team'), 'npc_name': req['npc']['name']}

    def extract_async(self, persona, req, branch, npc_line):
        with self.lock:
            if self.stopping:
                return
            thread = threading.Thread(target=self._extract, args=(persona, req, branch, npc_line),
                                      daemon=True, name='facts')
            self.threads = [t for t in self.threads if t.is_alive()] + [thread]
            thread.start()

    def _extract(self, persona, req, branch, npc_line):
        campaign, npc_id = req['campaign'], persona['id']
        try:
            payload = {'model': self.brain.cfg.model, 'max_tokens': 400, 'temperature': 0.2,
                       'chat_template_kwargs': {'enable_thinking': False},
                       'messages': facts.extraction_messages(req['npc']['name'], req['player']['name'], req['say'], npc_line),
                       'response_format': EXTRACTION_SCHEMA}
            raw = self.llm_call(payload, min(self.brain.cfg.summary_timeout, 60))
            extracted, relationship = facts.parse_extraction(raw)
            mem = self.brain.mem
            with mem.lock:
                existing = [r['payload']['text'] for r in mem.rows(campaign, branch, 'fact', npc_id)]
                for fact in facts.dedupe(existing, extracted):
                    mem.timeline.add_row(campaign, branch, 'fact', npc_id, fact, **self.metadata(req))
                if relationship['trust'] or relationship['fear']:
                    mem.timeline.add_row(campaign, branch, 'rel', npc_id, relationship, **self.metadata(req))
        except Exception as exc:  # extraction never delays or fails the spoken reply
            self.brain.log('talk.jsonl', {'event': 'fact_extraction_failed', 'campaign': campaign,
                                        'npc': npc_id, 'error': str(exc)})

    def wait(self):
        with self.lock:
            threads = list(self.threads)
        for thread in threads:
            thread.join()

    def close(self):
        with self.lock:
            self.stopping = True
        self.wait()
