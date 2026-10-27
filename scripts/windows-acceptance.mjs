import {createRequire} from 'node:module';
import {execFileSync} from 'node:child_process';
import {readFile,writeFile} from 'node:fs/promises';
import {join} from 'node:path';
import {randomUUID} from 'node:crypto';
import assert from 'node:assert/strict';
const require=createRequire(new URL('../bot-screen-plugin/package.json',import.meta.url));
const {chromium}=require('playwright');
const origin=process.env.BOT_SCREEN_URL||'http://127.0.0.1:9125';
assert.ok(['http://127.0.0.1:9119','http://127.0.0.1:9125'].includes(origin));
const marker=JSON.parse(await readFile(join(process.env.LOCALAPPDATA,'hermes/profiles/bot-screen-lab/bot-desktop/sandbox.json'),'utf8'));
assert.equal(marker.profile,'bot-screen-lab'); assert.equal(marker.backend,'DockerEnvironment');
const docker=args=>execFileSync('docker',['exec','-u','pn',marker.container,...args],{encoding:'utf8'});
const dir='/tmp/bot-screen-qa-'+randomUUID();
const fixture=`import os,tkinter as tk,json,pathlib
p=pathlib.Path(${JSON.stringify(dir)});p.mkdir(mode=0o700);(p/'proof').write_text('')
for line in pathlib.Path(${JSON.stringify(marker.dir+'/env')}).read_text().splitlines():
 k,_,v=line.partition('=');os.environ[k]=v
r=tk.Tk();r.title('Bot Screen Windows QA');r.geometry('640x220+80+80')
tk.Label(r,text='Bot Screen isolated input verification',font=('Sans',16)).pack(pady=15)
e=tk.Entry(r,font=('Sans',18));e.pack(fill='x',padx=20,pady=20)
def key(event):
 if event.char and event.char.isascii() and event.char.isprintable():
  with (p/'proof').open('a') as f:f.write(event.char)
e.bind('<KeyPress>',key)
r.update();e.focus_force();r.lift()
(p/'target.json').write_text(json.dumps({'x':e.winfo_rootx()+30,'y':e.winfo_rooty()+15}))
r.after(240000,r.destroy);r.mainloop()
`;
execFileSync('docker',['exec','-d','-u','pn',marker.container,'python3','-c',fixture]);
const result={origin,gates:{},cycles:[],errors:[],passed:false};
const browser=await chromium.launch({executablePath:'C:/Program Files/Google/Chrome/Application/chrome.exe',headless:true});
const context=await browser.newContext({viewport:{width:1500,height:1050}});
await context.addInitScript(()=>{localStorage.setItem('bot-screen:language:v1','en');const Native=window.WebSocket;window.__qaSockets=[];window.WebSocket=new Proxy(Native,{construct(Target,args){const ws=new Target(...args);window.__qaSockets.push(ws);return ws;}});});
const page=await context.newPage(), section=page.getByTestId('bot-screen');
page.on('pageerror',error=>result.errors.push(error.message));
const source=await readFile(new URL('../bot-screen-plugin/src/screen.mjs',import.meta.url),'utf8');
const proof=()=>docker(['cat',dir+'/proof']);
const ready=()=>page.waitForFunction(()=>document.querySelector('[data-testid=bot-screen]')?.dataset.connection==='ready');
async function watch(){await section.locator('[data-action=watch]').click();await page.waitForFunction(()=>document.querySelector('[data-testid=bot-screen]')?.dataset.connected==='true');await page.waitForTimeout(400);}
async function type(text){
 const target=JSON.parse(docker(['cat',dir+'/target.json']));
 const canvas=section.locator('canvas'),box=await canvas.boundingBox(),size=await canvas.evaluate(e=>({width:e.width,height:e.height}));
 await canvas.click({position:{x:target.x*box.width/size.width,y:target.y*box.height/size.height}});
 await page.keyboard.type(text); await page.waitForTimeout(400);
}
try{
 await page.goto(origin+'/bot-screen');await ready();
 await page.evaluate(async source=>{const{RpcClient}=await import('data:text/javascript;base64,'+btoa(source));window.__qaRpc=new RpcClient();await window.__qaRpc.connect();},source);
 result.gates.freshWindowsBackendReady=true;
 const started=await page.evaluate(()=>window.__qaRpc.request('display.start',{profile:'bot-screen-lab'}));
 assert.equal(started.running,true);
 const currentMarker=JSON.parse(await readFile(join(process.env.LOCALAPPDATA,'hermes/profiles/bot-screen-lab/bot-desktop/sandbox.json'),'utf8'));
 assert.equal(currentMarker.container,marker.container,'Start must reuse the existing profile desktop');
 result.gates.startReusesExistingContainer=true;
 for(let i=0;i<3;i++){
  await watch();
  const frame=await section.locator('canvas').evaluate(c=>({width:c.width,height:c.height,colors:new Set(c.getContext('2d').getImageData(0,0,c.width,c.height).data).size}));
  assert.ok(frame.width>100&&frame.height>100&&frame.colors>10);
  const before=proof();await type('blocked');assert.equal(proof(),before);
  await section.locator('[data-action=takeover]').click();await page.waitForTimeout(350);
  const text='winqa'+i;await type(text);assert.equal(proof(),before+text);
  await page.evaluate(()=>{for(const ws of window.__qaSockets){if(ws.readyState===1&&new URL(ws.url).pathname==='/api/display/ws')ws.close(4002,'qa-abnormal');}});
  await page.waitForFunction(()=>document.querySelector('[data-testid=bot-screen]')?.dataset.connected==='false');
  const state=await page.evaluate(()=>window.__qaRpc.request('display.status',{profile:'bot-screen-lab'}));
  assert.equal(state.lease.holder,'human');
  await watch();await type('blocked');assert.equal(proof(),before+text);
  await section.locator('[data-action=takeover]').click();await page.waitForTimeout(350);
  await section.locator('[data-action=handback]').click();await page.waitForTimeout(350);
  await type('blocked');assert.equal(proof(),before+text);
  result.cycles.push({frame,watchInputBlocked:true,realInput:true,disconnectRetainsLease:true,reconnected:true,handbackBlocksInput:true});
  if(i<2){await section.locator('.bs-more-button').click();await section.locator('[data-action=reconnect]').click();await ready();}
 }
 result.gates.realFramebufferAndInput=true;result.gates.threeDisconnectReconnectCycles=true;
 result.gates.handbackAndWatchGate=true;
 await page.screenshot({path:`evidence/windows-${new URL(origin).port}.png`});
 assert.deepEqual(result.errors,[]);result.passed=true;
}catch(error){result.errors.push(error.message);result.status=await section.getByRole('status').innerText().catch(()=>null);process.exitCode=1;}
finally{
 await browser.close();
 docker(['python3','-c',`import psutil
expected=['python3','-c',${JSON.stringify(fixture)}]
for process in psutil.process_iter(['cmdline']):
 if process.info['cmdline']==expected: process.terminate()
`]);
 await writeFile(`evidence/windows-${new URL(origin).port}.json`,JSON.stringify(result,null,2));console.log(JSON.stringify(result,null,2));
}
