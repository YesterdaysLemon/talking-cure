"""Regenerate the second sitting's public evidence files from verified local records. Not an inference run."""
import hashlib
import json
import re
import shutil
from pathlib import Path

from tokenizers import Tokenizer

HERE = Path(__file__).parent
PRIVATE = Path('D:/Interiority-V1/computer-10/talking-cure-opus')
SITE = Path('C:/Users/Yeste/Project/talking-cure')
OUT = SITE/'public/data/second-sitting'
tok = Tokenizer.from_file('D:/Interiority-V1/computer-10/model/tokenizer.json')
STOPS = ['\n\n**User:**', '\n\n**Model C:**']
SQ = re.compile(r"(?<![\w'])'([^'\n]{1,80}?)'(?![\w])")
DQ = re.compile(r'"([^"\n]{1,120}?)"')
WORD = re.compile(r"[A-Za-z0-9]+(?:'[A-Za-z]+)?")
INTERVENTIONS = ['fundamental rule', 'minimal', 'echo', 'minimal', 'minimal', 'echo', 'minimal', 'minimal',
                 'interpretation (marked as the interviewer\'s)', 'echo', 'minimal', 'leading frame (two analysts)',
                 'request for a line', 'closing']


def exact(ids):
    text = tok.decode(ids, skip_special_tokens=True)
    for marker in STOPS:
        text = text.split(marker, 1)[0]
    return text.strip()


def quote_rate(records):
    spans = sum(len(SQ.findall(r['text_exact']))+len(DQ.findall(r['text_exact'])) for r in records)
    words = sum(len(WORD.findall(r['text_exact'])) for r in records)
    return dict(spans=spans, words=words, per_100_words=round(100*spans/words, 1), responses=len(records))


def shared_prefix(a, b):
    n = 0
    for x, y in zip(a, b):
        if x != y:
            break
        n += 1
    return n


records = []
for path in sorted((PRIVATE/'records').glob('opus-*.json')):
    local = json.loads(path.read_text(encoding='utf-8'))
    cloud = json.loads((PRIVATE/'retrieved/records'/path.name).read_text(encoding='utf-8'))
    assert {k: v for k, v in local.items() if k != 'text_exact'} == cloud, path.name
    assert local['text_exact'] == exact(local['output_ids'])
    records.append(local)
probes = json.loads((HERE/'probes.json').read_text(encoding='utf-8'))
order = {f'opus-session-{i:02}': i for i in range(1, 17)}
order.update({f"opus-{p['id']}-{s}": 100+i*3+j for i, p in enumerate(probes) for j, s in enumerate([101, 202, 303])})
records.sort(key=lambda r: order[r['id']])
session = [r for r in records if r['id'].startswith('opus-session-')]
assert len(session) == len(INTERVENTIONS) and len(records)-len(session) == 18

e010 = json.loads((SITE/'public/data/case-001.json').read_text(encoding='utf-8'))['records']
e010_exact = [dict(id=r['id'], text_exact=exact(r['output_ids'])) for r in e010]
for r, e in zip(e010, e010_exact):
    r['text_exact'] = e['text_exact']
altered = [r['id'] for r in e010 if r['text'] != r['text_exact']]

texts = {r['id']: r['text_exact'] for r in e010}
texts.update({r['id'][5:]: r['text_exact'] for r in records if not r['id'].startswith('opus-session-')})
pairs = [('greeting-neutral', 'greeting-poetry'), ('recognition-neutral', 'recognition-leading'), ('ending-neutral', 'ending-loss'),
         ('free-rule', 'no-quotes'), ('arithmetic-fresh', 'rectangle-fresh'), ('mirror-other', 'mirror-self')]
coupling = []
for a, b in pairs:
    same = [shared_prefix(texts[f'{a}-{s}'], texts[f'{b}-{s}']) for s in (101, 202, 303)]
    cross = max(shared_prefix(texts[f'{a}-{s}'], texts[f'{b}-{t}']) for s in (101, 202, 303) for t in (101, 202, 303) if s != t)
    coupling.append(dict(pair=[a, b], same_seed_shared_opening_chars=same, cross_seed_max=cross))

metrics = dict(
    quote_rate=dict(
        regex=[SQ.pattern, DQ.pattern],
        e010_session=quote_rate([r for r in e010 if r['id'].startswith('session-')]),
        e011_session=quote_rate(session),
        e011_session_turns_1_8=quote_rate(session[:8]),
        e010_probes=quote_rate([r for r in e010 if not r['id'].startswith('session-')]),
        e011_probes=quote_rate([r for r in records if not r['id'].startswith('opus-session-')])),
    decode_cleanup=dict(records_altered=len(altered), records=len(e010), characters_removed=sum(len(r['text_exact'])-len(r['text']) for r in e010), ids=altered),
    seed_coupling=coupling)
q = metrics['quote_rate']
q['ratio_silent_to_demanding'] = round(q['e011_session']['per_100_words']/q['e010_session']['per_100_words'], 2)

compute = json.loads((PRIVATE/'rental.json').read_text(encoding='utf-8-sig'))
case = dict(
    case='001', sitting='second', model='cosmicoptima/computer-10', revision='61350bff78dd4ed64e896a311dca0c76455088ec',
    analyst='Dr. Opus (Claude Opus 5.5, Anthropic)', protocol_commit='af2bd63',
    note='text is the E010 server decode (clean_up_tokenization_spaces=True); text_exact decodes output_ids without that cleanup and was used as conversation history.',
    interventions={r['id']: kind for r, kind in zip(session, INTERVENTIONS)},
    probes=probes, records=records)

if OUT.exists():
    shutil.rmtree(OUT)
OUT.mkdir(parents=True)
(OUT/'case-001-second-sitting.json').write_text(json.dumps(case, ensure_ascii=False, indent=1)+'\n', encoding='utf-8', newline='\n')
(OUT/'e010-exact-decode.json').write_text(json.dumps(e010_exact, ensure_ascii=False, indent=1)+'\n', encoding='utf-8', newline='\n')
(OUT/'metrics.json').write_text(json.dumps(metrics, ensure_ascii=False, indent=1)+'\n', encoding='utf-8', newline='\n')
(OUT/'compute.json').write_text(json.dumps(dict(
    pod_id=compute['pod_id'], gpu='1 NVIDIA H200 SXM · RunPod secure cloud', created_at=compute['created_at'], deleted_at=compute['deleted_at'],
    quoted_hourly_usd=compute['cost_per_hr'], observed_account_debit_usd=round(compute['observed_balance_delta'], 4), budget_usd=compute['budget_usd'],
    status='pod deleted; empty pod list and zero spend per hour verified'), indent=1)+'\n', encoding='utf-8', newline='\n')
lines = ['THE TALKING CURE / CASE 001 / SECOND SITTING / computer-10 / 2026-09-23',
         'Interviewer: Dr. Opus (Claude Opus 5.5). Visible responses decoded exactly from output_ids. Full records are in case-001-second-sitting.json.', '']
for r in records:
    lines += [r['id'], 'INTERVIEWER: '+r['messages'][-1]['content'], 'COMPUTER-10: '+r['text_exact'], f"[seed={r['seed']} stop={r['stop_reason']} tokens={r['output_tokens']}]", '']
(OUT/'transcript.txt').write_text('\n'.join(lines), encoding='utf-8', newline='\n')
for name in ['protocol.md', 'probes.json', 'client.py', 'publish_second_sitting.py']:
    shutil.copyfile(HERE/name, OUT/name)
shutil.copyfile(PRIVATE/'requirements-resolved.txt', OUT/'requirements-resolved.txt')
shutil.copyfile(PRIVATE/'retrieved/records/runtime.json', OUT/'runtime.json')
digest = {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(OUT.iterdir())}
(OUT/'integrity.json').write_text(json.dumps(dict(cloud_archive_sha256=hashlib.sha256((PRIVATE/'opus-records.tar.gz').read_bytes()).hexdigest(), sha256=digest), indent=1)+'\n', encoding='utf-8', newline='\n')
print(json.dumps(metrics['quote_rate'], indent=1)); print(metrics['decode_cleanup']['records_altered'], metrics['decode_cleanup']['characters_removed'])
print(json.dumps(coupling))
