"""Append-only client. Each invocation conducts one interview turn or all frozen probes."""
import argparse
import hashlib
import json
from pathlib import Path
import httpx

ROOT = Path('D:/Interiority-V1/computer-10/talking-cure')


def request(record_id, messages, seed):
    target = ROOT/'records'/(record_id+'.json')
    if target.exists():
        raise RuntimeError('Record already exists')
    body = dict(id=record_id, messages=messages, seed=seed)
    (ROOT/'requests').mkdir(parents=True, exist_ok=True)
    reqpath = ROOT/'requests'/(record_id+'.json')
    if reqpath.exists():
        raise RuntimeError('Request already attempted: inspect remote record before retrying')
    reqpath.write_text(json.dumps(body, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    response = httpx.post('http://127.0.0.1:18767/generate', json=body, timeout=180)
    response.raise_for_status()
    result = response.json()
    assert result['id']==record_id and result['messages']==messages and result['seed']==seed
    assert result['prompt_sha256']==hashlib.sha256(result['prompt'].encode()).hexdigest()
    assert len(result['input_ids'])==result['input_tokens'] and len(result['output_ids'])==result['output_tokens']
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(result, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    print(json.dumps({k:result[k] for k in ['id','text','input_tokens','output_tokens','stop_reason','seconds']}, ensure_ascii=False), flush=True)


if __name__=='__main__':
    ap=argparse.ArgumentParser()
    ap.add_argument('--prompt')
    ap.add_argument('--probes', action='store_true')
    args=ap.parse_args()
    if args.probes:
        probes=json.loads(Path(__file__).with_name('probes.json').read_text())
        for probe in probes:
            for seed in [101,202,303]:
                request(probe['id']+'-'+str(seed), [{'role':'user','content':probe['prompt']}], seed)
    else:
        assert args.prompt
        records=sorted((ROOT/'records').glob('session-*.json')) if (ROOT/'records').exists() else []
        messages=[]
        for i,p in enumerate(records, 1):
            r=json.loads(p.read_text(encoding='utf-8'))
            assert r['id']==f'session-{i:02}' and r['messages'][:-1]==messages
            messages=r['messages']+[{'role':'assistant','content':r['text']}]
        messages.append({'role':'user','content':args.prompt})
        request(f'session-{len(records)+1:02}', messages, 9101+len(records))
