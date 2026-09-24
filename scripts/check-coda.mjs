import assert from 'node:assert/strict';
import {readFile} from 'node:fs/promises';
import {createHash} from 'node:crypto';
const read=async p=>JSON.parse(await readFile(p,'utf8'));
const hash=b=>createHash('sha256').update(b).digest('hex');
export async function checkCoda(){
  const a=await read('public/data/coda/computer10.json'),r=a.records[0];
  assert.equal(a.records.length,1);assert.equal(r.id,'coda-15001');assert.equal(r.seed,15001);
  assert.deepEqual(r.messages,[{role:'user',content:await readFile('public/data/coda/computer10-prompt.txt','utf8')}]);
  assert.equal(hash(r.prompt),r.prompt_sha256);assert.equal(r.input_ids.length,r.input_tokens);assert.equal(r.output_ids.length,r.output_tokens);
  assert(r.input_tokens+512<=8192);assert.equal(r.metadata.revision,a.revision);assert.equal(r.metadata.precision,'bfloat16');
  assert.equal(r.text.replace(/\s/g,''),r.text_exact.replace(/\s/g,''));
  const files=['public/data/case-001.json','public/data/second-sitting/case-001-second-sitting.json','public/data/notebook/case-001-notebook.json','public/data/replay/case-001-replay.json'];
  let total=1;for(const f of files){const b=await read(f);assert(b.records.every(x=>x.seed!==15001));total+=b.records.length;}assert.equal(total,117);
  const opus=await read('public/data/coda/opus.json');assert.equal(opus.model,'claude-opus-5-5');assert(opus.text.length>100);
  assert.equal(opus.prompt,await readFile('public/data/coda/opus-invitation.txt','utf8'));
  const receipt=await read('public/data/coda/integrity.json');for(const [file,sha] of Object.entries(receipt.sha256))assert.equal(hash(await readFile(`public/data/coda/${file}`)),sha,file);
  const compute=await read('public/data/coda/compute.json');assert.equal(compute.status,'deleted');assert.equal(compute.spend_per_hr_after,0);
  const c=await read('content/framing.json');assert(c.closing.lastWord.length>=2);
  for(const p of c.closing.lastWord)for(const q of p.matchAll(/<q data-record="([^"]+)">([^<]+)<\/q>/g)){assert.equal(q[1],r.id);assert(r.text_exact.includes(q[2]));assert(p.includes(`href="#${r.id}"`));}
  const letters=await read('content/correspondence.json');assert.equal(letters.letters.at(-1).id,'letter-4');assert(!letters.awaiting);
  const baseline=await read('public/data/coda/archive-baseline.json');
  for(const [file,sha] of Object.entries(baseline.files_sha256))assert.equal(hash(await readFile(file)),sha,`Earlier archive changed: ${file}`);
  for(const [id,sha] of Object.entries(baseline.letters_json_sha256))assert.equal(hash(JSON.stringify(letters.letters.find(l=>l.id===id))),sha,`Published letter changed: ${id}`);
  console.log('PASS: coda exact request, new seed, 117 total records, closing quotation, Opus provenance, evidence hashes and teardown');
}
