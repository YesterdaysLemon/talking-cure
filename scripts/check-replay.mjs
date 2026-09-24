import assert from 'node:assert/strict';
import {readFile} from 'node:fs/promises';
import {createHash} from 'node:crypto';
const read=async p=>JSON.parse(await readFile(p,'utf8'));
const hash=s=>createHash('sha256').update(s).digest('hex');
const prefix=(a,b)=>{let n=0;while(n<a.length&&a[n]===b[n])n++;return n;};
export async function checkReplay(){
  const a=await read('public/data/replay/case-001-replay.json');
  const m=await read('public/data/replay/metrics.json');
  const e010=Object.fromEntries((await read('public/data/case-001.json')).records.map(r=>[r.id,r]));
  const exact=Object.fromEntries((await read('public/data/second-sitting/e010-exact-decode.json')).map(e=>[e.id,e.text_exact]));
  const c=await read('content/replay.json');
  const recs=Object.fromEntries(a.records.map(r=>[r.id,r]));
  assert.equal(a.records.length,33);assert.equal(Object.keys(recs).length,33);
  for(const r of a.records){
    assert.equal(hash(r.prompt),r.prompt_sha256);assert.equal(r.input_ids.length,r.input_tokens);assert.equal(r.output_ids.length,r.output_tokens);
    assert.equal(r.metadata.revision,a.revision);assert.equal(r.metadata.precision,'bfloat16');
    assert.equal(r.text.replace(/\s/g,''),r.text_exact.replace(/\s/g,''));
    assert.equal(r.seed,e010[r.source_id].seed,`Replay must use the original seed: ${r.id}`);
  }
  let identical=0;
  for(let t=1;t<=16;t++){
    const nn=String(t).padStart(2,'0'),o=e010[`session-${nn}`],r=recs[`replay-${nn}-recorded`];
    assert.deepEqual(r.messages,o.messages,`Recorded replay must send the recorded messages: ${nn}`);
    const same=r.output_ids.join()===o.output_ids.join();identical+=same;assert.equal(m.turns[t-1].recorded_identical,same);
    if(t===1)continue;
    const s=recs[`replay-${nn}-restored`];
    const restored=o.messages.map((msg,j)=>msg.role==='assistant'?{role:'assistant',content:exact[`session-${String(Math.floor(j/2)+1).padStart(2,'0')}`]}:msg);
    assert.deepEqual(s.messages,restored,`Restored replay may change only the spaces in earlier replies: ${nn}`);
    const fork=s.output_ids.join()===o.output_ids.join()?null:prefix(s.output_ids,o.output_ids);
    assert.equal(m.turns[t-1].restored_fork_token,fork,`Fork index mismatch: ${nn}`);
  }
  assert.equal(identical,m.replayability.recorded_identical);
  for(const n of ['04','12'])assert.deepEqual(recs[`replay-${n}-fresh`].messages,[e010[`session-${n}`].messages.at(-1)]);
  assert.equal(recs['replay-12-fresh'].text_exact.includes('43'),m.content_codes.codes['replay-12-fresh'].result);
  for(const b of c.blocks.filter(b=>b.type==='quote'))assert(recs[b.id]?.text_exact.includes(b.text),`Replay quote mismatch: ${b.id}`);
  const receipt=await read('public/data/replay/integrity.json');
  for(const [file,sha] of Object.entries(receipt.sha256))assert.equal(hash(await readFile(`public/data/replay/${file}`)),sha,file);
  const compute=await read('public/data/replay/compute.json');assert.equal(compute.status,'deleted');assert.equal(compute.spend_per_hr_after,0);
  console.log(`PASS: replay records, original seeds, recorded and restored messages, ${identical}/16 identical replays, fork indices, file hashes and teardown receipt`);
}
