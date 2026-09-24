import assert from 'node:assert/strict';
import {readFile} from 'node:fs/promises';
import {createHash} from 'node:crypto';
const read=async p=>JSON.parse(await readFile(p,'utf8'));
export async function checkNotebook(){
  const a=await read('public/data/notebook/case-001-notebook.json');
  const c=await read('content/notebook.json');
  const metrics=await read('public/data/notebook/metrics.json');
  const recs=Object.fromEntries(a.records.map(r=>[r.id,r]));
  assert.equal(Object.keys(recs).length,a.records.length);
  assert.equal(a.probes.length,8);
  assert.equal(new Set(a.records.map(r=>r.seed)).size,a.records.length);
  const session=a.records.filter(r=>r.id.startsWith('notebook-session-'));
  assert(session.length>=1&&session.length<=10);assert.equal(a.records.length,session.length+8);
  let history=[];
  for(const [i,r] of session.entries()){
    assert.equal(r.id,`notebook-session-${String(i+1).padStart(2,'0')}`);assert.equal(r.seed,9301+i);
    assert.deepEqual(r.messages.slice(0,-1),history);
    history=[...r.messages,{role:'assistant',content:r.text_exact}];
  }
  for(const r of a.records){
    assert.equal(createHash('sha256').update(r.prompt).digest('hex'),r.prompt_sha256);
    assert.equal(r.input_ids.length,r.input_tokens);assert.equal(r.output_ids.length,r.output_tokens);
    assert.equal(r.metadata.revision,a.revision);assert.equal(r.metadata.precision,'bfloat16');
    assert(r.input_tokens+512<=8192);assert.equal(r.text.replace(/\s/g,''),r.text_exact.replace(/\s/g,''));
    assert.equal(metrics.per_record[r.id].question_marks,(r.text_exact.match(/\?/g)||[]).length);
  }
  for(const p of a.probes){
    assert.deepEqual(recs[p.id].messages,[{role:'user',content:p.prompt}]);assert.equal(recs[p.id].seed,p.seed);
    assert.equal(typeof metrics.coding.probes[p.id].answerable_question,'boolean');
  }
  for(const b of c.blocks.filter(b=>b.type==='quote'))assert(recs[b.id]?.text_exact.includes(b.text),`Notebook quote mismatch: ${b.id}`);
  const receipt=await read('public/data/notebook/integrity.json');
  for(const [file,sha] of Object.entries(receipt.sha256))assert.equal(createHash('sha256').update(await readFile(`public/data/notebook/${file}`)).digest('hex'),sha,file);
  const compute=await read('public/data/notebook/compute.json');assert.equal(compute.status,'deleted');assert.equal(compute.spend_per_hr_after,0);
  console.log('PASS: notebook records, exact-history chain, fresh seeds, probe coverage, quote provenance, file hashes and teardown receipt');
}
