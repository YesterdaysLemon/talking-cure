const tabs=[...document.querySelectorAll('[data-view]')];
const panels=[...document.querySelectorAll('.view')];
function route(){
  const target=location.hash.slice(1)||'essay';
  const el=document.getElementById(target);
  const panel=el?.closest('.view')||document.getElementById('essay');
  const pair=el?.closest('.probe-pair');
  if(pair){
    document.getElementById('probe-filter').value='all';
    document.querySelectorAll('.probe-pair').forEach(p=>p.hidden=false);
  }
  panels.forEach(p=>p.hidden=p!==panel);
  tabs.forEach(a=>a.setAttribute('aria-current',a.dataset.view===panel.id?'page':'false'));
  if(el&&el!==panel) requestAnimationFrame(()=>el.scrollIntoView({block:'start'}));
  else if(location.hash)window.scrollTo({top:document.querySelector('.edition-nav').offsetTop-12,behavior:'instant'});
}
window.addEventListener('hashchange',route);route();
document.querySelectorAll('[data-lens]').forEach(button=>button.addEventListener('click',()=>{
  const id=button.dataset.lens;
  document.querySelectorAll('[data-lens]').forEach(b=>b.setAttribute('aria-pressed',String(b===button)));
  document.querySelectorAll('.lens-note').forEach(p=>p.hidden=p.id!==id);
}));
document.getElementById('probe-filter')?.addEventListener('change',event=>{
  const pair=event.target.value;
  document.querySelectorAll('.probe-pair').forEach(p=>p.hidden=pair!=='all'&&p.dataset.pair!==pair);
});
document.getElementById('print')?.addEventListener('click',()=>window.print());
