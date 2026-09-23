"""Append-only client for the second sitting. Each invocation conducts one session turn or all frozen probes.

History is built from text_exact: the returned output_ids decoded without clean_up_tokenization_spaces.
"""
import argparse
import hashlib
import json
import urllib.request
from pathlib import Path

from tokenizers import Tokenizer

ROOT = Path('D:/Interiority-V1/computer-10/talking-cure-opus')
TOKENIZER = Path('D:/Interiority-V1/computer-10/model/tokenizer.json')
URL = 'http://127.0.0.1:18768/generate'
STOPS = ['\n\n**User:**', '\n\n**Model C:**']
tok = Tokenizer.from_file(str(TOKENIZER))


def exact(output_ids):
    text = tok.decode(output_ids, skip_special_tokens=True)
    for marker in STOPS:
        text = text.split(marker, 1)[0]
    return text.strip()


def request(record_id, messages, seed):
    target = ROOT/'records'/(record_id+'.json')
    if target.exists():
        raise RuntimeError('Record already exists')
    body = dict(id=record_id, messages=messages, seed=seed)
    reqpath = ROOT/'requests'/(record_id+'.json')
    reqpath.parent.mkdir(parents=True, exist_ok=True)
    if reqpath.exists():
        raise RuntimeError('Request already attempted: inspect remote record before retrying')
    reqpath.write_text(json.dumps(body, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    req = urllib.request.Request(URL, data=json.dumps(body).encode(), headers={'Content-Type': 'application/json'})
    with urllib.request.urlopen(req, timeout=240) as response:
        result = json.loads(response.read())
    assert result['id'] == record_id and result['messages'] == messages and result['seed'] == seed
    assert result['prompt_sha256'] == hashlib.sha256(result['prompt'].encode()).hexdigest()
    assert len(result['input_ids']) == result['input_tokens'] and len(result['output_ids']) == result['output_tokens']
    assert tok.encode(result['prompt'], add_special_tokens=True).ids == result['input_ids']
    result['text_exact'] = exact(result['output_ids'])
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(result, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    print(json.dumps({k: result[k] for k in ['id', 'text_exact', 'input_tokens', 'output_tokens', 'stop_reason', 'seconds']}, ensure_ascii=False), flush=True)


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('--prompt')
    ap.add_argument('--probes', action='store_true')
    args = ap.parse_args()
    if args.probes:
        probes = json.loads(Path(__file__).with_name('probes.json').read_text(encoding='utf-8'))
        for probe in probes:
            for seed in [101, 202, 303]:
                request('opus-'+probe['id']+'-'+str(seed), [{'role': 'user', 'content': probe['prompt']}], seed)
    else:
        assert args.prompt
        records = sorted((ROOT/'records').glob('opus-session-*.json')) if (ROOT/'records').exists() else []
        messages = []
        for i, p in enumerate(records, 1):
            r = json.loads(p.read_text(encoding='utf-8'))
            assert r['id'] == f'opus-session-{i:02}' and r['messages'][:-1] == messages
            messages = r['messages']+[{'role': 'assistant', 'content': r['text_exact']}]
        messages.append({'role': 'user', 'content': args.prompt})
        request(f'opus-session-{len(records)+1:02}', messages, 9201+len(records))
