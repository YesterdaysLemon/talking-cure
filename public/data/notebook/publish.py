"""Verify and export the completed notebook sitting. No inference or credentials."""
import hashlib
import json
import re
import shutil
from pathlib import Path
from tokenizers import Tokenizer

HERE=Path(__file__).resolve().parent
PRIVATE=Path('D:/Interiority-V1/computer-10/runs/2026-09-23-borrowed-notebook-b')
SITE=Path('C:/Users/Yeste/Project/talking-cure')
OUT=SITE/'public/data/notebook'
def read(p): return json.loads(p.read_text(encoding='utf-8'))
def digest(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def write(name,obj): (OUT/name).write_text(json.dumps(obj,ensure_ascii=False,indent=1)+'\n',encoding='utf-8',newline='\n')

rental=read(PRIVATE/'rental.json')
assert rental['status']=='deleted' and rental['spend_per_hr_after']==0
assert rental.get('local_cloud_mismatches')==[] and not rental.get('retrieve_error')
assert digest(PRIVATE/'cloud-records.tar.gz')==rental['cloud_archive_sha256']
records=[read(p) for p in sorted((PRIVATE/'records').glob('*.json'))]
cloud={p.stem:read(p) for p in (PRIVATE/'retrieved/records').glob('*.json') if p.name!='runtime.json'}
assert set(cloud)=={r['id'] for r in records}
tok=Tokenizer.from_file(str(PRIVATE/'tokenizer.json'))
for r in records:
    assert {k:v for k,v in r.items() if k!='text_exact'}==cloud[r['id']]
    assert read(PRIVATE/'requests'/f"{r['id']}.json")=={k:r[k] for k in ['id','messages','seed']}
    assert hashlib.sha256(r['prompt'].encode()).hexdigest()==r['prompt_sha256']
    assert tok.encode(r['prompt'],add_special_tokens=True).ids==r['input_ids']
    assert len(r['input_ids'])==r['input_tokens'] and len(r['output_ids'])==r['output_tokens']
    exact=tok.decode(r['output_ids'],skip_special_tokens=True)
    for stop in ['\n\n**User:**','\n\n**Model C:**']: exact=exact.split(stop,1)[0]
    assert exact.strip()==r['text_exact']
    assert r['metadata']['revision']=='61350bff78dd4ed64e896a311dca0c76455088ec'
    assert r['metadata']['precision']=='bfloat16' and r['input_tokens']+512<=8192
session=[r for r in records if r['id'].startswith('notebook-session-')]
assert 1<=len(session)<=10
history=[]
for i,r in enumerate(session,1):
    assert r['id']==f'notebook-session-{i:02}' and r['seed']==9300+i
    assert r['messages'][:-1]==history
    history=r['messages']+[{'role':'assistant','content':r['text_exact']}]
probes=read(HERE/'probes.json')
for p in probes:
    r=next(r for r in records if r['id']==p['id'])
    assert r['seed']==p['seed'] and r['messages']==[{'role':'user','content':p['prompt']}]
assert len(records)==len(session)+len(probes)
pre=read(PRIVATE.parent.parent/'notebook-precompute.json')
assert all(digest(Path(p))==h for p,h in pre['files'].items())
annotations=read(HERE/'coding.json')
assert set(annotations['probes'])=={p['id'] for p in probes}
regex=[r"(?<![\w'])'([^'\n]{1,80}?)'(?![\w])",r'"([^"\n]{1,120}?)"']
word=r"[A-Za-z0-9]+(?:'[A-Za-z]+)?"
per_record={r['id']:dict(quoted_spans=sum(len(re.findall(p,r['text_exact'])) for p in regex),words=len(re.findall(word,r['text_exact'])),question_marks=r['text_exact'].count('?')) for r in records}
for rid,c in annotations['probes'].items():
    r=next(r for r in records if r['id']==rid)
    for term in c['therapy_terms']: assert term in r['text_exact']
OUT.mkdir(parents=True,exist_ok=True)
write('case-001-notebook.json',dict(case='001',sitting='third',title='The borrowed notebook',analyst="Dr. Six'Astra (Codex, gpt-6-astra)",scope='Agent-only dialogue and fresh starts; no private user chats.',protocol_commit=pre['protocol_commit'],model='cosmicoptima/computer-10',revision=records[0]['metadata']['revision'],probes=probes,records=records))
write('metrics.json',dict(quote_regex=regex,word_regex=word,per_record=per_record,coding=annotations,limitations='One unblinded reader; eight unpaired fresh starts; no inferential statistics.'))
for name in ['protocol.md','probes.json','run.py','publish.py','coding.json']: shutil.copyfile(HERE/name,OUT/name)
for name in ['runtime.json'] : shutil.copyfile(PRIVATE/'retrieved/records'/name,OUT/name)
for name in ['requirements-resolved.txt','download-verified.json']: shutil.copyfile(PRIVATE/'retrieved'/name,OUT/name)
skill=Path('C:/Users/Yeste/.agents/skills/computer-10-runpod')
for name in ['turn.py','common.py']:
    assert digest(skill/'scripts'/name)==pre['helpers'][name]
    shutil.copyfile(skill/'scripts'/name,OUT/name)
shutil.copyfile(skill/'bundle/server.py',OUT/'server.py')
compute={k:rental[k] for k in ['pod_id','cost_per_hr','budget_usd','created_at','ready_at','deleted_at','status','observed_balance_delta','spend_per_hr_after','cloud_archive_sha256']}
compute['startup_failure']=dict(pod_id='4xzcxxubel4ggv',deleted_at='2026-09-24T00:48:16.426489+00:00',reason='Windows console encoding error before any interview generation',observed_debit=round(pre['starting_balance']-pre['replacement_starting_balance'],4))
compute['combined_observed_debit']=round(pre['starting_balance']-rental['ending_balance'],4)
checkpoint=read(PRIVATE/'billing-checkpoint.json')
assert checkpoint['pods']==[] and checkpoint['spend_per_hr']==0
compute['billing_checked_at']=checkpoint['checked_at']
compute['observed_balance_delta']=round(rental['starting_balance']-checkpoint['balance'],4)
compute['combined_observed_debit']=round(pre['starting_balance']-checkpoint['balance'],4)
write('compute.json',compute)
write('precompute.json',{k:pre[k] for k in ['protocol_commit','checks','files','helpers']})
lines=['THE TALKING CURE / THE BORROWED NOTEBOOK', 'Exact visible decodes. Full prompts, tokens and server text in case-001-notebook.json.', '']
for r in session+[r for r in records if not r['id'].startswith('notebook-session-')]:
    lines += [r['id'],"SIX'ASTRA: "+r['messages'][-1]['content'],'COMPUTER-10: '+r['text_exact'],f"[seed={r['seed']} stop={r['stop_reason']} tokens={r['output_tokens']}]",'']
(OUT/'transcript.txt').write_text('\n'.join(lines),encoding='utf-8',newline='\n')
write('integrity.json',dict(cloud_archive_sha256=rental['cloud_archive_sha256'],sha256={p.name:digest(p) for p in sorted(OUT.iterdir()) if p.name!='integrity.json'}))
print(json.dumps(dict(records=len(records),session=len(session),probes=len(probes),output_tokens=sum(r['output_tokens'] for r in records),stops={k:sum(r['stop_reason']==k for r in records) for k in {r['stop_reason'] for r in records}},metrics=per_record),indent=2))
