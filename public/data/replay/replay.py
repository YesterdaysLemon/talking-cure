"""E013 Part A: replay the first sitting's turns with their original seeds. Append-only; nothing is retried.

python replay.py --run RUN [--plan-only]
"""
import argparse
import hashlib
import json
import sys
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path.home()/'.agents/skills/computer-10-runpod/scripts'))
from common import exact_decoder, load_rental, run_dir  # noqa: E402

SITE = Path('C:/Users/Yeste/Project/talking-cure')


def plan():
    records = json.loads((SITE/'public/data/case-001.json').read_text(encoding='utf-8'))['records']
    exact = {e['id']: e['text_exact'] for e in json.loads((SITE/'public/data/second-sitting/e010-exact-decode.json').read_text(encoding='utf-8'))}
    session = sorted((r for r in records if r['id'].startswith('session-')), key=lambda r: r['id'])
    assert [r['seed'] for r in session] == list(range(9101, 9117))
    jobs = [(f"replay-{r['id'][-2:]}-recorded", 'recorded', r['messages'], r['seed'], r['id']) for r in session]
    for r in session[1:]:
        restored = []
        for j, m in enumerate(r['messages']):
            if m['role'] == 'assistant':
                source = session[j//2]
                assert m['content'] == source['text']
                restored.append({'role': 'assistant', 'content': exact[source['id']]})
            else:
                restored.append(m)
        jobs.append((f"replay-{r['id'][-2:]}-restored", 'restored', restored, r['seed'], r['id']))
    for n in ['04', '12']:
        r = session[int(n)-1]
        jobs.append((f'replay-{n}-fresh', 'fresh', [r['messages'][-1]], r['seed'], r['id']))
    return jobs


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--run')
    ap.add_argument('--plan-only', action='store_true')
    args = ap.parse_args()
    jobs = plan()
    digest = hashlib.sha256(json.dumps(jobs, ensure_ascii=False).encode()).hexdigest()
    print(f'{len(jobs)} generations planned; plan sha256 {digest}')
    if args.plan_only:
        return
    rental = load_rental(args.run)
    assert rental.get('status') == 'ready', rental.get('status')
    decode = exact_decoder(args.run)
    assert decode, 'tokenizers and tokenizer.json are required for exact decodes'
    folder = run_dir(args.run)
    (folder/'records').mkdir(exist_ok=True)
    (folder/'requests').mkdir(exist_ok=True)
    for record_id, condition, messages, seed, source in jobs:
        target, attempted = folder/'records'/f'{record_id}.json', folder/'requests'/f'{record_id}.json'
        if target.exists() or attempted.exists():
            print(f'skip {record_id}: already requested')
            continue
        body = dict(id=record_id, messages=messages, seed=seed)
        attempted.write_text(json.dumps(body, ensure_ascii=False)+'\n', encoding='utf-8', newline='\n')
        request = urllib.request.Request(f"http://127.0.0.1:{rental['local_port']}/generate", data=json.dumps(body).encode(),
                                         headers={'Content-Type': 'application/json'})
        with urllib.request.urlopen(request, timeout=300) as response:
            result = json.loads(response.read())
        assert result['id'] == record_id and result['messages'] == messages and result['seed'] == seed
        assert result['prompt_sha256'] == hashlib.sha256(result['prompt'].encode()).hexdigest()
        result.update(condition=condition, source_id=source, text_exact=decode(result['output_ids']))
        target.write_text(json.dumps(result, ensure_ascii=False, indent=1)+'\n', encoding='utf-8', newline='\n')
        print(json.dumps({'id': record_id, 'tokens': result['output_tokens'], 'text': result['text_exact'][:140]}, ensure_ascii=False), flush=True)


if __name__ == '__main__':
    main()
