const {chromium}=require('playwright');const fs=require('fs');
(async()=>{const [mode,a,b,out]=process.argv.slice(2);
const br=await chromium.launch();const p=await br.newPage({viewport:{width:1080,height:1920}});
await p.goto('file://'+__dirname+'/composition.html');
if(mode==='bg'){await p.evaluate(()=>{document.querySelectorAll('body>*:not(#bg):not(script)').forEach(e=>e.style.visibility='hidden')});await p.screenshot({path:out});await br.close();return;}
await p.evaluate(()=>document.body.classList.add('fg'));
fs.mkdirSync(out,{recursive:true});
const fps=25;const times=mode==='at'?a.split(',').map(Number):null;
const list=times||Array.from({length:Math.round((+b - +a)*fps)},(_,i)=>+a+i/fps);
for(let i=0;i<list.length;i++){await p.evaluate(t=>seek(t),list[i]);
 const name=times?`t${list[i]}.png`:`f${String(Math.round(list[i]*fps)).padStart(5,'0')}.png`;
 await p.screenshot({path:out+'/'+name,omitBackground:true});}
await br.close();})();
