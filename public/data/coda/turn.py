"""Talk to a launched computer-10. Every generation is kept; nothing is retried or overwritten.

Session turn (history rebuilt from exact decodes of earlier turns):
  python turn.py --run NAME --session opus-session --seed-base 9301 --prompt "Go on."
Fresh context (empty history):
  python turn.py --run NAME --fresh greeting-neutral-101 --seed 101 --prompt "Hello."
"""
import argparse
import hashlib
import json
import sys
import urllib.request

from common import exact_decoder, load_rental, run_dir


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--run', required=True)
    ap.add_argument('--prompt', required=True)
    ap.add_argument('--session', help='Record id prefix for a multi-turn session, e.g. third-session')
    ap.add_argument('--seed-base', type=int, default=1000, help='Seed of turn 1; turn n uses seed-base + n - 1')
    ap.add_argument('--fresh', help='Record id for one empty-history generation')
    ap.add_argument('--seed', type=int)
    args = ap.parse_args()
    if bool(args.session) == bool(args.fresh):
        sys.exit('Pass exactly one of --session or --fresh.')
    rental = load_rental(args.run)
    if rental.get('status') != 'ready':
        sys.exit(f"Run {args.run} is {rental.get('status')}, not ready.")
    folder = run_dir(args.run)
    records = folder/'records'
    records.mkdir(exist_ok=True)
    decode = exact_decoder(args.run)
    if not decode:
        print('WARNING: tokenizers or tokenizer.json unavailable; history falls back to the server text, '
              'which drops spaces before some quotation marks. pip install --user tokenizers', file=sys.stderr)

    if args.fresh:
        if args.seed is None:
            sys.exit('--fresh needs --seed.')
        record_id, seed, messages = args.fresh, args.seed, [{'role': 'user', 'content': args.prompt}]
    else:
        turns = sorted(records.glob(f'{args.session}-[0-9][0-9].json'))
        messages = []
        for i, path in enumerate(turns, 1):
            r = json.loads(path.read_text(encoding='utf-8'))
            assert r['id'] == f'{args.session}-{i:02}' and r['messages'][:-1] == messages, f'Broken chain at {path.name}'
            messages = r['messages']+[{'role': 'assistant', 'content': r.get('text_exact', r['text'])}]
        messages.append({'role': 'user', 'content': args.prompt})
        record_id, seed = f'{args.session}-{len(turns)+1:02}', args.seed_base+len(turns)

    target = records/f'{record_id}.json'
    attempted = folder/'requests'/f'{record_id}.json'
    if target.exists() or attempted.exists():
        sys.exit(f'{record_id} was already requested. Records are never regenerated; inspect it instead.')
    attempted.parent.mkdir(exist_ok=True)
    body = dict(id=record_id, messages=messages, seed=seed)
    attempted.write_text(json.dumps(body, ensure_ascii=False, indent=2)+'\n', encoding='utf-8', newline='\n')
    request = urllib.request.Request(f"http://127.0.0.1:{rental['local_port']}/generate", data=json.dumps(body).encode(),
                                     headers={'Content-Type': 'application/json'})
    with urllib.request.urlopen(request, timeout=300) as response:
        result = json.loads(response.read())
    assert result['id'] == record_id and result['messages'] == messages and result['seed'] == seed
    assert result['prompt_sha256'] == hashlib.sha256(result['prompt'].encode()).hexdigest()
    assert len(result['output_ids']) == result['output_tokens']
    if decode:
        result['text_exact'] = decode(result['output_ids'])
    target.write_text(json.dumps(result, ensure_ascii=False, indent=2)+'\n', encoding='utf-8', newline='\n')
    print(json.dumps({k: result.get(k) for k in ['id', 'seed', 'text_exact', 'output_tokens', 'stop_reason', 'seconds']},
                     ensure_ascii=False))


if __name__ == '__main__':
    main()
