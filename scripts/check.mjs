import assert from 'node:assert/strict';
import {readFile} from 'node:fs/promises';
import {createHash} from 'node:crypto';
const c=JSON.parse(await readFile('content/case-001.json','utf8'));
const a=JSON.parse(await readFile('public/data/case-001.json','utf8'));
const exact10=JSON.parse(await readFile('public/data/second-sitting/e010-exact-decode.json','utf8'));
const exactFirst=Object.fromEntries(exact10.map(r=>[r.id,r.text_exact]));
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
  assert(exactFirst[b.id]?.includes(b.text),`Quote mismatch: ${b.id}`);
}
const receipt=JSON.parse(await readFile('public/data/integrity.json','utf8'));
for(const [file,expected]of Object.entries(receipt.sha256)) assert.equal(hash(await readFile(`public/data/${file}`)),expected,file);
const s2=JSON.parse(await readFile('public/data/second-sitting/case-001-second-sitting.json','utf8'));
const essay2=JSON.parse(await readFile('content/second-sitting.json','utf8'));
const letters=JSON.parse(await readFile('content/correspondence.json','utf8'));
const m2=JSON.parse(await readFile('public/data/second-sitting/metrics.json','utf8'));
const bare=t=>t.replace(/\s/g,'');
assert.equal(new Set(s2.records.map(r=>r.id)).size,s2.records.length);
const s2session=s2.records.filter(r=>r.id.startsWith('opus-session-'));
assert(s2session.length>=1&&s2session.length<=16);assert.equal(s2.records.length-s2session.length,18);
let h2=[];
for(const [i,r] of s2session.entries()){
  assert.equal(r.id,`opus-session-${String(i+1).padStart(2,'0')}`);assert.equal(r.seed,9201+i);
  assert.deepEqual(r.messages.slice(0,-1),h2,`History must use text_exact: ${r.id}`);
  h2=[...r.messages,{role:'assistant',content:r.text_exact}];
  assert(s2.interventions[r.id]);
}
for(const r of s2.records){
  assert.equal(hash(r.prompt),r.prompt_sha256);
  assert.equal(r.input_ids.length,r.input_tokens);assert.equal(r.output_ids.length,r.output_tokens);
  assert.equal(r.metadata.revision,'61350bff78dd4ed64e896a311dca0c76455088ec');assert.equal(r.metadata.precision,'bfloat16');
  assert.equal(bare(r.text),bare(r.text_exact),`Exact decode may differ only in spaces: ${r.id}`);assert(r.text_exact.length>=r.text.length);
}
for(const p of s2.probes)for(const seed of [101,202,303]){
  const r=s2.records.find(r=>r.id===`opus-${p.id}-${seed}`);
  assert.equal(r.seed,seed);assert.deepEqual(r.messages,[{role:'user',content:p.prompt}]);
}
assert.deepEqual(exact10.map(r=>r.id),a.records.map(r=>r.id));
exact10.forEach((e,i)=>assert.equal(bare(e.text_exact),bare(a.records[i].text)));
assert.equal(exact10.filter((e,i)=>e.text_exact!==a.records[i].text).length,m2.decode_cleanup.records_altered);
const exact2=Object.fromEntries([...exact10.map(e=>[e.id,e.text_exact]),...s2.records.map(r=>[r.id,r.text_exact])]);
for(const b of essay2.blocks.filter(b=>b.type==='quote'))assert(exact2[b.id]?.includes(b.text),`Second-sitting quote mismatch: ${b.id}`);
for(const b of essay2.blocks.filter(b=>b.type==='stenographer')){
  assert(a.records.find(r=>r.id===b.id).text.includes(b.published));assert(exact2[b.id].includes(b.exact));
}
for(const [,,,,id] of essay2.predictions)assert(exact2[id],id);
for(const pair of essay2.coupling)for(const id of pair)assert(exact2[id],id);
assert(exact2[letters.epigraph.id].includes(letters.epigraph.text),'Epigraph mismatch');
assert.equal(new Set(letters.letters.map(l=>l.id)).size,letters.letters.length);
for(const l of letters.letters)for(const k of ['id','number','from','to','date','subject','salutation','body','closing','signature'])assert(l[k],`Letter ${l.id} lacks ${k}`);
for(const l of letters.letters){
  for(const paragraph of [...l.body,l.postscript||'']){
    for(const q of paragraph.matchAll(/<q data-record="([^"]+)">([^<]+)<\/q>/g)){
      assert(exact2[q[1]]?.includes(q[2]),`Letter quotation mismatch: ${q[1]}`);
      assert(paragraph.includes(`href="#${q[1]}"`),`Letter quotation needs its record link: ${q[1]}`);
    }
  }
}
const receipt2=JSON.parse(await readFile('public/data/second-sitting/integrity.json','utf8'));
for(const [file,expected]of Object.entries(receipt2.sha256)) assert.equal(hash(await readFile(`public/data/second-sitting/${file}`)),expected,file);
const html=await readFile('dist/index.html','utf8');
const ids=[...html.matchAll(/\sid="([^"]+)"/g)].map(m=>m[1]);assert.equal(ids.length,new Set(ids).size);
for(const m of html.matchAll(/href="#([^"]+)"/g))assert(ids.includes(m[1]),`Broken evidence anchor ${m[1]}`);
assert(!html.includes('undefined'));assert(!html.includes('TODO'));
console.log('PASS: both sittings: complete records, chain of context, probe coverage, exact decodes, hashes, quotation provenance, letters, and evidence links');
