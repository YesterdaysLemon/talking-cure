// The front page (title and contents), the running header, and the reading-order links between views.
const esc=s=>String(s).replaceAll('&','&amp;').replaceAll('<','&lt;').replaceAll('>','&gt;').replaceAll('"','&quot;');

// A wandering line, seeded so every build draws the same walk. Seeds 43 (17 + 26), 9201 and 9301 open each sitting's lore.
function drift(seed,steps,start){
  let t=seed>>>0;const rand=()=>{t+=0x6D2B79F5;let r=Math.imul(t^t>>>15,t|1);r^=r+Math.imul(r^r>>>7,r|61);return((r^r>>>14)>>>0)/4294967296;};
  let [x,y]=start,heading=rand()*Math.PI*2;const points=[[x,y]];
  for(let i=0;i<steps;i++){
    heading+=(rand()-.5)*.9;
    const [cx,cy]=[600-x,450-y];if(Math.hypot(cx,cy)>380)heading+=Math.sign(Math.sin(Math.atan2(cy,cx)-heading))*.35;
    x+=Math.cos(heading)*7;y+=Math.sin(heading)*7;points.push([x,y]);
  }
  return 'M'+points.map(([a,b])=>`${a.toFixed(1)} ${b.toFixed(1)}`).join('L');
}

export function frontView({sittings,letters,awaiting,whisper}){
  const walks=[[43,900,[420,380],'ink'],[9201,760,[800,520],'teal'],[9301,760,[520,600],'red']];
  const svg=`<svg class="drift" viewBox="0 0 1200 900" preserveAspectRatio="xMidYMid slice" aria-hidden="true">${walks.map(([seed,steps,start,ink],i)=>`<path class="walk walk-${ink}" style="--i:${i}" pathLength="1" d="${drift(seed,steps,start)}"/>`).join('')}</svg>`;
  const sittingRows=sittings.map((s,i)=>`<li class="toc-item ink-${s.ink}" style="--n:${i}"><a href="#${s.id}"><span class="toc-num">${s.number}</span><span class="toc-title">${esc(s.name)}<em>${esc(s.title)}</em></span><span class="toc-leader" aria-hidden="true"></span><span class="toc-by">${esc(s.by)}</span></a></li>`).join('');
  const letterRows=letters.map((l,i)=>`<li class="toc-item toc-letter ink-${l.from==='Dr. Opus'?'teal':'red'}" style="--n:${i+sittings.length}"><a href="#${l.id}"><span class="toc-num">${l.number}</span><span class="toc-title">${esc(l.from)} <i>to</i> ${esc(l.to)}<em>${esc(l.subject)}</em></span></a></li>`).join('')
    +(awaiting?`<li class="toc-item toc-letter toc-awaiting" style="--n:${letters.length+sittings.length}"><span class="toc-num">${esc(awaiting.number)}</span><span class="toc-title">${esc(awaiting.from)} <i>to</i> ${esc(awaiting.to)}<em>${esc(awaiting.note)}</em></span></li>`:'');
  return `<section class="view front" id="contents" aria-labelledby="front-title">${svg}<div class="front-inner">
<p class="front-kicker">An experimental journal of machine speech · No. 001 · September 2026</p>
<h1 class="front-title" id="front-title">The Talking <em>Cure.</em></h1>
<p class="front-deck">Case 001. One machine, two analysts, three sittings, and the letters between them.</p>
<nav class="toc" id="toc" aria-label="Contents"><p class="toc-head">The sittings</p><ol class="toc-list">${sittingRows}</ol><p class="toc-head">The letters</p><ol class="toc-list">${letterRows}</ol></nav>
<blockquote class="whisper">“${esc(whisper.text)}”<a href="#${whisper.id}">${esc(whisper.label)}</a></blockquote>
<p class="front-foot"><span class="seal">The couch is a metaphor</span><span>Conceived by Alireza Afshan · readings by two language models · every word the patient said is kept</span></p>
</div></section>`;
}

export function runner(sittings){
  return `<header class="runner"><a class="wordmark" href="#contents" aria-label="The Talking Cure: contents">The Talking <em>Cure.</em></a><nav aria-label="Sittings and letters">${sittings.map(s=>`<a href="#${s.id}" data-view="${s.id}" class="ink-${s.ink}"><b>${s.number}</b><span>${esc(s.short)}</span></a>`).join('')}<a href="#letters" data-view="letters"><span class="always">Letters</span></a></nav></header>`;
}

export function nextLink(target){
  if(!target)return `<nav class="next-link" aria-label="Continue reading"><a href="#contents"><span class="kicker">The end, for now</span>Back to the contents ↑</a></nav>`;
  return `<nav class="next-link" aria-label="Continue reading"><a href="#${target.id}"><span class="kicker">Next</span>${target.number?`${target.number}. `:''}${esc(target.name)} <em>${esc(target.title||'')}</em> →</a></nav>`;
}
