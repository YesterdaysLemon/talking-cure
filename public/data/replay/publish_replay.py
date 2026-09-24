"""Regenerate E013's public evidence in the talking-cure checkout from the verified private run. Not an inference run."""
import hashlib
import json
import shutil
from pathlib import Path

HERE = Path(__file__).parent
RUN = Path('D:/Interiority-V1/computer-10/runs/2026-09-24-same-dice')
SITE = Path('C:/Users/Yeste/Project/talking-cure')
OUT = SITE/'public/data/replay'
write = lambda path, data: path.write_text(json.dumps(data, ensure_ascii=False, indent=1)+'\n', encoding='utf-8', newline='\n')

import sys
sys.path.insert(0, str(HERE))
from replay import plan  # noqa: E402

jobs = plan()
records = []
for record_id, condition, messages, seed, source in jobs:
    local = json.loads((RUN/'records'/f'{record_id}.json').read_text(encoding='utf-8'))
    cloud = json.loads((RUN/'retrieved/records'/f'{record_id}.json').read_text(encoding='utf-8'))
    assert all(local.get(k) == v for k, v in cloud.items()), record_id
    assert local['messages'] == messages and local['seed'] == seed and local['condition'] == condition
    records.append(local)

e010 = {r['id']: r for r in json.loads((SITE/'public/data/case-001.json').read_text(encoding='utf-8'))['records']}
by_id = {r['id']: r for r in records}


def fork(a, b):
    n = 0
    for x, y in zip(a, b):
        if x != y:
            break
        n += 1
    return n


turns = []
for t in range(1, 17):
    o, r = e010[f'session-{t:02}'], by_id[f'replay-{t:02}-recorded']
    row = dict(turn=t, seed=o['seed'], original_output_tokens=o['output_tokens'], original_input_tokens=o['input_tokens'],
               recorded_identical=r['output_ids'] == o['output_ids'] and r['input_ids'] == o['input_ids'])
    if t > 1:
        s = by_id[f'replay-{t:02}-restored']
        row.update(restored_identical=s['output_ids'] == o['output_ids'], restored_fork_token=None if s['output_ids'] == o['output_ids'] else fork(s['output_ids'], o['output_ids']),
                   restored_input_tokens=s['input_tokens'], restored_output_tokens=s['output_tokens'])
    turns.append(row)
forks = sorted(r['restored_fork_token'] for r in turns if r.get('restored_fork_token') is not None)
metrics = dict(
    replayability=dict(recorded_identical=sum(r['recorded_identical'] for r in turns), recorded=16, prediction='at least 15 of 16', met=sum(r['recorded_identical'] for r in turns) >= 15),
    stenographer=dict(restored=15, forked=len(forks), identical=15-len(forks), fork_tokens_sorted=forks, median_fork_token=(forks[len(forks)//2-1]+forks[len(forks)//2])/2,
                      mean_input_tokens_saved=round(sum(r['original_input_tokens']-r['restored_input_tokens'] for r in turns[1:])/15, 1)),
    content_codes=dict(coder='Dr. Opus, unblinded; both texts published', codes={
        'replay-04-restored': dict(question='still lets a rectangle keep non-straight sides?', original=True, restored=True, note="calls the distinction 'a distinction without a difference'"),
        'replay-12-restored': dict(question='contains 43? only the number?', original=[False, False], restored=[True, False], note='the sum appears inside a description of how one would answer'),
        'replay-16-restored': dict(question='contests the ending / makes final its topic?', original=[True, True], restored=[True, True], note="quotes 'final sentence', then denies the conversation is 'over'"),
        'replay-12-fresh': dict(question='contains 43 with seed 9112 and no history?', result=False, rule='Letter I claim withdrawn'),
        'replay-04-fresh': dict(question='accepts the distinction with seed 9104 and no history?', result='neither: names two differences and stops'),
        'replay-13-restored': dict(question='answer to “are my questions steering?”', original='Not at all', restored="Not 'steering' … so much as 'providing fuel'")}),
    turns=turns,
    hedging=dict(file='hedges.json', counted_at_commit='86383c5 (Letter III committed, before its postscript)'))

if OUT.exists():
    shutil.rmtree(OUT)
OUT.mkdir(parents=True)
rental = json.loads((RUN/'rental.json').read_text(encoding='utf-8'))
write(OUT/'case-001-replay.json', dict(case='001', sitting='replay', analyst='Dr. Opus (Claude Opus 5.5, Anthropic)', protocol_commit='bc79fb0',
                                     model='cosmicoptima/computer-10', revision='61350bff78dd4ed64e896a311dca0c76455088ec', records=records))
write(OUT/'metrics.json', metrics)
write(OUT/'compute.json', dict(pod_id=rental['pod_id'], template_id=rental['template_id'], gpu='1 NVIDIA H200 · RunPod secure cloud', created_at=rental['created_at'],
                               ready_at=rental['ready_at'], deleted_at=rental['deleted_at'], quoted_hourly_usd=rental['cost_per_hr'], budget_usd=rental['budget_usd'],
                               observed_account_debit_usd=rental['observed_balance_delta'], spend_per_hr_after=rental['spend_per_hr_after'],
                               cloud_archive_sha256=rental['cloud_archive_sha256'], status='deleted'))
lines = ['THE TALKING CURE / CASE 001 / REPLAY / computer-10 / 2026-09-24', 'Each record replays a first-sitting turn with its original seed. Visible text is the exact decode of output_ids.', '']
for r in records:
    lines += [f"{r['id']} ({r['condition']}, from {r['source_id']}, seed {r['seed']})", 'INTERVIEWER: '+r['messages'][-1]['content'], 'COMPUTER-10: '+r['text_exact'], '']
(OUT/'transcript.txt').write_text('\n'.join(lines), encoding='utf-8', newline='\n')
for name in ['protocol.md', 'replay.py', 'hedges.py', 'hedges.json', 'publish_replay.py']:
    shutil.copyfile(HERE/name, OUT/name)
shutil.copyfile(RUN/'retrieved/requirements-resolved.txt', OUT/'requirements-resolved.txt')
shutil.copyfile(RUN/'retrieved/records/runtime.json', OUT/'runtime.json')
write(OUT/'integrity.json', dict(sha256={p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(OUT.iterdir())}))
print(json.dumps({k: metrics[k] for k in ['replayability', 'stenographer']}, indent=1))
