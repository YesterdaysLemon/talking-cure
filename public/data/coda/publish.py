"""Verify the closing contributions and export the public coda. No inference."""
import hashlib
import json
import shutil
from pathlib import Path
from tokenizers import Tokenizer

HERE=Path(__file__).resolve().parent
PRIVATE=Path('D:/Interiority-V1/computer-10/runs/2026-09-24-last-word')
OPUS=Path('D:/Interiority-V1/computer-10/closing-opus')
OUT=Path('C:/Users/Yeste/Project/talking-cure/public/data/coda')
SKILL=Path('C:/Users/Yeste/.agents/skills/computer-10-runpod')
read=lambda p:json.loads(p.read_text(encoding='utf-8'))
digest=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def write(name,obj): (OUT/name).write_text(json.dumps(obj,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')

pre=read(PRIVATE.parent.parent/'last-word-precompute.json')
assert all(digest(Path(p))==h for p,h in pre['files'].items())
assert all(digest(SKILL/'scripts'/n)==h for n,h in pre['helpers'].items())
for line in (SKILL/'bundle/SHA256SUMS').read_text().splitlines():
    h,n=line.split();assert digest(SKILL/'bundle'/n)==h
rental=read(PRIVATE/'rental.json')
assert rental['status']=='deleted' and rental['spend_per_hr_after']==0
assert rental['local_cloud_mismatches']==[] and not rental.get('retrieve_error')
assert digest(PRIVATE/'cloud-records.tar.gz')==rental['cloud_archive_sha256']
records=[read(p) for p in (PRIVATE/'records').glob('*.json')]
assert len(records)==1
r=records[0];assert r['id']=='coda-15001' and r['seed']==15001
cloud=[read(p) for p in (PRIVATE/'retrieved/records').glob('*.json') if p.name!='runtime.json']
assert cloud==[{k:v for k,v in r.items() if k!='text_exact'}]
assert r['messages']==[{'role':'user','content':(HERE/'computer10-prompt.txt').read_text(encoding='utf-8')}]
assert read(PRIVATE/'requests/coda-15001.json')=={k:r[k] for k in ['id','seed','messages']}
assert hashlib.sha256(r['prompt'].encode()).hexdigest()==r['prompt_sha256']
tok=Tokenizer.from_file(str(PRIVATE/'tokenizer.json'))
assert tok.encode(r['prompt'],add_special_tokens=True).ids==r['input_ids']
assert len(r['input_ids'])==r['input_tokens']==pre['input_tokens']
assert len(r['output_ids'])==r['output_tokens'] and r['input_tokens']+512<=8192
exact=tok.decode(r['output_ids'],skip_special_tokens=True)
for stop in ['\n\n**User:**','\n\n**Model C:**']:exact=exact.split(stop,1)[0]
assert exact.strip()==r['text_exact']
assert r['metadata']['precision']=='bfloat16' and r['metadata']['revision']=='61350bff78dd4ed64e896a311dca0c76455088ec'

opus=read(OPUS/'provider-result-desktop.json')
assert opus['is_error'] is False and set(opus['modelUsage'])=={'claude-opus-5-5'}
request=read(OPUS/'request-desktop.json')
assert request['prompt']==(HERE/'opus-invitation.txt').read_text(encoding='utf-8')
assert opus.get('subagent_stats',{}).get('spawned',0)==0
assert opus['usage']['server_tool_use']=={'web_search_requests':0,'web_fetch_requests':0}
OUT.mkdir(parents=True,exist_ok=True)
write('computer10.json',{'model':'cosmicoptima/computer-10','revision':r['metadata']['revision'],'protocol_commit':pre['protocol_commit'],'scope':'One fresh reply to the disclosed editorial summary, not the entire archive or cross-session memory.','records':records})
write('opus.json',{'author':'Dr. Opus','model':'claude-opus-5-5','provider':'Anthropic, through Claude Code 2.1.280','context':'Fork of the completed author session that wrote Letter III and the replay; existing working context retained. Tools disabled for this invitation.','prompt':request['prompt'],'text':opus['result'],'started_at':request['started_at'],'duration_ms':opus['duration_ms'],'usage':opus['usage'],'reported_list_price_usd':opus['total_cost_usd'],'billing_note':'Provider-reported list-price estimate through an existing Claude subscription; not an observed account debit.','provider_result_sha256':digest(OPUS/'provider-result-desktop.json'),'startup_notes':['First CLI attempt skipped keychain authentication and returned no model output.','Installed CLI 2.1.273 was unsupported for Opus 5.5 and returned no model output.','The already-installed desktop CLI 2.1.280 produced the sole contribution.']})
for n in ['protocol.md','computer10-prompt.txt','opus-invitation.txt','run.py','publish.py','archive-baseline.json']:shutil.copyfile(HERE/n,OUT/n)
for n in ['turn.py','common.py']:shutil.copyfile(SKILL/'scripts'/n,OUT/n)
shutil.copyfile(SKILL/'bundle/server.py',OUT/'server.py')
shutil.copyfile(PRIVATE/'retrieved/records/runtime.json',OUT/'runtime.json')
for n in ['requirements-resolved.txt','download-verified.json']:shutil.copyfile(PRIVATE/'retrieved'/n,OUT/n)
write('precompute.json',{k:v for k,v in pre.items() if k!='starting_balance'})
compute={k:rental[k] for k in ['pod_id','cost_per_hr','budget_usd','created_at','ready_at','deleted_at','status','observed_balance_delta','spend_per_hr_after','cloud_archive_sha256']}
checkpoint=read(PRIVATE/'billing-checkpoint.json')
assert checkpoint['pods']==[] and checkpoint['spend_per_hr']==0
compute.update(billing_checked_at=checkpoint['checked_at'],observed_balance_delta=round(rental['starting_balance']-checkpoint['balance'],6),billing_note='Observed account delta, not a final invoice.')
write('compute.json',compute)
(OUT/'transcript.txt').write_text('THE TALKING CURE / CLOSING INVITATION\n\nSIX\'ASTRA:\n'+r['messages'][0]['content']+'\n\nCOMPUTER-10:\n'+r['text_exact']+f"\n\n[seed={r['seed']} stop={r['stop_reason']} output_tokens={r['output_tokens']}]\n",encoding='utf-8',newline='\n')
write('integrity.json',{'sha256':{p.name:digest(p) for p in sorted(OUT.iterdir()) if p.name!='integrity.json'}})
print(json.dumps({'records':1,'cloud_matched':True,'exact_token_decode':True,'opus_model':'claude-opus-5-5','observed_debit':compute['observed_balance_delta']},indent=2))
