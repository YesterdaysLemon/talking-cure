import assert from 'node:assert/strict';
import {readFile} from 'node:fs/promises';
import {createHash} from 'node:crypto';
const c=JSON.parse(await readFile('content/case-001.json','utf8'));
const a=JSON.parse(await readFile('public/data/case-001.json','utf8'));
const hash=s=>createHash('sha256').update(s).digest('hex');
assert.equal(new Set(a.records.map(r=>r.id)).size,a.records.length);
const session=a.records.filter(r=>r.id.startsWith('session-'));
assert(session.length>=1&&session.length<=16);
assert.equal(a.records.length-session.length,18);
let history=[];
for(const [i,r] of session.entries()){
  assert.equal(r.id,`session-${String(i+1).padStart(2,'0')}`);
  assert.deepEqual(r.messages.slice(0,-1),history);
  history=[...r.messages,{role:'assistant',content:r.text}];
}
for(const r of a.records){
  assert.equal(hash(r.prompt),r.prompt_sha256);
  assert.equal(r.input_ids.length,r.input_tokens);assert.equal(r.output_ids.length,r.output_tokens);
  assert.equal(r.metadata.revision,'61350bff78dd4ed64e896a311dca0c76455088ec');
  assert.equal(r.metadata.precision,'bfloat16');assert(r.input_tokens+512<=8192);
}
for(const p of a.probes)for(const seed of [101,202,303]){
  const r=a.records.find(r=>r.id===`${p.id}-${seed}`);
  assert.equal(r.seed,seed);assert.deepEqual(r.messages,[{role:'user',content:p.prompt}]);
}
for(const b of c.blocks.filter(b=>b.type==='quote')){
  assert(a.records.find(r=>r.id===b.id)?.text.includes(b.text),`Quote mismatch: ${b.id}`);
}
const receipt=JSON.parse(await readFile('public/data/integrity.json','utf8'));
for(const [file,expected]of Object.entries(receipt.sha256)) assert.equal(hash(await readFile(`public/data/${file}`)),expected,file);
const html=await readFile('dist/index.html','utf8');
const ids=[...html.matchAll(/\sid="([^"]+)"/g)].map(m=>m[1]);assert.equal(ids.length,new Set(ids).size);
for(const m of html.matchAll(/href="#([^"]+)"/g))assert(ids.includes(m[1]),`Broken evidence anchor ${m[1]}`);
assert(!html.includes('undefined'));assert(!html.includes('TODO'));
console.log('PASS: complete records, chain of context, probe coverage, hashes, quotation provenance, and evidence links');
