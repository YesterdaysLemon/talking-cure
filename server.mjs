import http from 'node:http';
import {readFile,stat} from 'node:fs/promises';
import path from 'node:path';
const root=path.resolve('dist');
const buildSha=(await readFile('build-sha.txt','utf8').catch(()=>'local')).trim();
const types={'.html':'text/html; charset=utf-8','.css':'text/css; charset=utf-8','.js':'text/javascript; charset=utf-8','.json':'application/json; charset=utf-8','.md':'text/plain; charset=utf-8','.txt':'text/plain; charset=utf-8','.svg':'image/svg+xml','.gz':'application/gzip'};
http.createServer(async(req,res)=>{
  res.setHeader('X-Content-Type-Options','nosniff');
  res.setHeader('Referrer-Policy','strict-origin-when-cross-origin');
  res.setHeader('Content-Security-Policy',"default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self' data:; base-uri 'none'; frame-ancestors 'none'; form-action 'none'");
  if(!['GET','HEAD'].includes(req.method)){res.writeHead(405);res.end();return;}
  try{
    const url=new URL(req.url,'http://localhost');
    if(url.pathname==='/healthz'){
      await stat(path.join(root,'index.html'));await stat(path.join(root,'data/case-001.json'));
      res.setHeader('Content-Type',types['.json']);res.setHeader('Cache-Control','no-store');
      res.end(JSON.stringify({ok:true,app:'talking-cure',sha:buildSha}));return;
    }
    const rel=decodeURIComponent(url.pathname);
    const file=path.resolve(root,'.'+(rel==='/'?'/index.html':rel));
    if(!file.startsWith(root+path.sep)){res.writeHead(403);res.end();return;}
    const buf=await readFile(file);
    res.setHeader('Content-Type',types[path.extname(file)]||'application/octet-stream');
    res.setHeader('Cache-Control','public, max-age=0, must-revalidate');
    res.setHeader('Content-Length',buf.length);
    res.end(req.method==='HEAD'?undefined:buf);
  }catch{res.writeHead(404,{'Content-Type':'text/plain; charset=utf-8'});res.end('This page is absent. Return to /');}
}).listen(Number(process.env.PORT||8790),process.env.HOST||'0.0.0.0',()=>console.log('The Talking Cure is listening'));
