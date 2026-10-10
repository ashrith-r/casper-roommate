import http from 'node:http';
import {readFile} from 'node:fs/promises';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
const root=fileURLToPath(new URL('../site/',import.meta.url));
const types={'.html':'text/html; charset=utf-8','.js':'text/javascript; charset=utf-8','.css':'text/css; charset=utf-8','.svg':'image/svg+xml','.csv':'text/csv; charset=utf-8','.png':'image/png'};
const server=http.createServer(async(req,res)=>{
  try {
    let route=decodeURIComponent(new URL(req.url,'http://localhost').pathname);
    if(route==='/')route='/index.html';
    const file=path.resolve(root,'.'+route);
    if(!file.startsWith(root)) {res.writeHead(403).end();return;}
    const body=await readFile(file);
    res.writeHead(200,{'Content-Type':types[path.extname(file)]||'application/octet-stream','Cache-Control':'no-store','X-Content-Type-Options':'nosniff'}).end(body);
  }catch{res.writeHead(404).end('Not found');}
});
server.listen(Number(process.env.PORT)||4173,'127.0.0.1',()=>console.log('CASPER preview: http://127.0.0.1:4173'));
