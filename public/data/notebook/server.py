"""Bounded, auditable research inference; SSH loopback only."""
import argparse
import hashlib
import json
import threading
import time
from datetime import datetime, timezone
from pathlib import Path

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

app = FastAPI(docs_url=None, redoc_url=None)
gate = threading.Lock()
STOPS = ['\n\n**User:**', '\n\n**Model C:**']
REVISION = '61350bff78dd4ed64e896a311dca0c76455088ec'


class Request(BaseModel):
    id: str = Field(pattern=r'^[a-z0-9-]+$', max_length=80)
    messages: list[dict[str, str]]
    seed: int = Field(ge=0, le=2**31-1)


def render(messages):
    if not messages or len(messages) % 2 != 1:
        raise ValueError('Expected alternating conversation ending with user')
    for i, m in enumerate(messages):
        if set(m) != {'role', 'content'} or m['role'] != ('user' if i % 2 == 0 else 'assistant') or not m['content'].strip():
            raise ValueError('Invalid message')
    return ('As follows is a conversation between another user and Model C.\n\n'
            'Full conversation with Model C:\n\n' + '\n\n'.join(
                ('**User:** ' if m['role'] == 'user' else '**Model C:** ') + m['content'].strip()
                for m in messages) + '\n\n**Model C:**')


@app.get('/health')
def health():
    return metadata


@app.post('/generate')
def generate(body: Request):
    if not gate.acquire(blocking=False):
        raise HTTPException(409, 'Busy')
    try:
        target = args.root / 'records' / (body.id + '.json')
        if target.exists():
            raise HTTPException(409, 'Record exists; no overwrite or silent regeneration')
        try:
            prompt = render(body.messages)
        except ValueError as e:
            raise HTTPException(422, str(e))
        inputs = tokenizer(prompt, add_special_tokens=True, return_tensors='pt')
        n = inputs.input_ids.shape[1]
        if n + 512 > 8192:
            raise HTTPException(413, 'Context limit; history must not be truncated')
        torch.manual_seed(body.seed)
        torch.cuda.manual_seed_all(body.seed)

        class Halt(StoppingCriteria):
            def __call__(self, ids, scores, **kwargs):
                return any(s in tokenizer.decode(ids[0, n:], skip_special_tokens=True) for s in STOPS)

        started = datetime.now(timezone.utc).isoformat()
        tick = time.monotonic()
        with torch.inference_mode():
            output = model.generate(**inputs.to('cuda'), do_sample=True, temperature=1., top_p=.98,
                top_k=0, max_new_tokens=512, pad_token_id=tokenizer.eos_token_id,
                eos_token_id=[tokenizer.eos_token_id, 128009], use_cache=True,
                stopping_criteria=StoppingCriteriaList([Halt()]))[0, n:].tolist()
        raw = tokenizer.decode(output, skip_special_tokens=False)
        visible = tokenizer.decode(output, skip_special_tokens=True)
        reason = 'role' if any(s in visible for s in STOPS) else 'eos' if output[-1] in [tokenizer.eos_token_id, 128009] else 'length'
        for marker in STOPS:
            visible = visible.split(marker, 1)[0]
        result = dict(id=body.id, messages=body.messages, seed=body.seed, prompt=prompt,
            prompt_sha256=hashlib.sha256(prompt.encode()).hexdigest(), input_ids=inputs.input_ids[0].tolist(),
            output_ids=output, raw=raw, text=visible.strip(), input_tokens=n, output_tokens=len(output),
            stop_reason=reason, started_at=started, seconds=round(time.monotonic()-tick, 3), metadata=metadata)
        target.write_text(json.dumps(result, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
        return result
    finally:
        gate.release()


if __name__ == '__main__':
    import torch
    import transformers
    import uvicorn
    from transformers import AutoTokenizer, AutoModelForCausalLM, StoppingCriteria, StoppingCriteriaList
    ap = argparse.ArgumentParser()
    ap.add_argument('--root', type=Path, required=True)
    args = ap.parse_args()
    receipt = json.loads((args.root/'download-verified.json').read_text())
    assert receipt['status']=='complete' and receipt['revision']==REVISION and len(receipt['files'])==38
    for item in receipt['files']:
        assert (args.root/'model'/item['file']).stat().st_size==item['bytes']
    torch.set_num_threads(8)
    tokenizer = AutoTokenizer.from_pretrained(args.root/'model', local_files_only=True, trust_remote_code=False)
    model = AutoModelForCausalLM.from_pretrained(args.root/'model', torch_dtype=torch.bfloat16,
        device_map={'':0}, attn_implementation='sdpa', local_files_only=True, trust_remote_code=False)
    model.eval()
    assert all(p.dtype == torch.bfloat16 for p in model.parameters())
    params = sum(p.numel() for p in model.parameters())
    assert params == 70553706496
    metadata = dict(model='cosmicoptima/computer-10', revision=REVISION, precision='bfloat16',
        parameters=params, torch=torch.__version__, transformers=transformers.__version__,
        gpu=torch.cuda.get_device_name(), temperature=1., top_p=.98, top_k=0, max_new_tokens=512,
        context_limit=8192, attention='sdpa', frame='Model C full frame', system_prompt=None)
    (args.root/'records').mkdir(exist_ok=True)
    (args.root/'records'/'runtime.json').write_text(json.dumps(metadata, indent=2)+'\n')
    print('TALKING_CURE_READY', flush=True)
    uvicorn.run(app, host='127.0.0.1', port=8767, access_log=False)
