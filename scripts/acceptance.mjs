import {createRequire} from 'node:module';
import {readFile,writeFile,mkdir} from 'node:fs/promises';
import {execFileSync} from 'node:child_process';
import {fileURLToPath} from 'node:url';
import assert from 'node:assert/strict';
const require=createRequire(new URL('../bot-screen-plugin/package.json',import.meta.url));
const {chromium}=require('playwright');
const root=fileURLToPath(new URL('../',import.meta.url));
process.chdir(root);
const origin='http://127.0.0.1:9124', container='bot-screen-integration';
const docker=args=>execFileSync('docker',['exec',container,...args],{encoding:'utf8'});
const py=source=>docker(['/opt/hermes-venv/bin/python','-c',source]);
const input=()=>py("from pathlib import Path;p=Path('/lab/input-proof.txt'); print(p.read_text() if p.exists() else '',end='')");
const identity=()=>JSON.parse(py("import pathlib,json; p=pathlib.Path('/lab/profiles/bot-screen-lab/bot-desktop/launcher.pid'); record=p.read_text(); pid=int(record.split()[0]); print(json.dumps({'record':record,'ticks':pathlib.Path(f'/proc/{pid}/stat').read_text().rsplit(')',1)[1].split()[19]}))"));
await mkdir('evidence',{recursive:true});
const result={startedAt:new Date().toISOString(),origin,container,profile:'bot-screen-lab',gates:{},cycles:[],errors:[],consoleErrors:[],passed:false};
const browser=await chromium.launch({executablePath:'C:/Program Files/Google/Chrome/Application/chrome.exe',headless:!process.env.BOT_SCREEN_HEADED});
const context=await browser.newContext({viewport:{width:1600,height:1150}});
await context.addInitScript(()=>{localStorage.setItem('bot-screen:language:v1','zh-Hant');
 const Native=window.WebSocket;window.__testSockets=[];
 window.WebSocket=new Proxy(Native,{construct(Target,args){const socket=new Target(...args);window.__testSockets.push(socket);return socket;}});
});
const page=await context.newPage();
page.on('pageerror',e=>result.consoleErrors.push(e.message));
const moduleSource=await readFile('bot-screen-plugin/src/screen.mjs','utf8');
async function probe(){
 await page.evaluate(async source=>{
  window.testRpc?.close();
  const {RpcClient}=await import('data:text/javascript;base64,'+btoa(source));
  window.testRpc=new RpcClient();await window.testRpc.connect();
 },moduleSource);
}
const status=()=>page.evaluate(()=>window.testRpc.request('display.status',{profile:'bot-screen-lab'}));
const section=page.getByTestId('bot-screen');
const button=name=>section.getByRole('button',{name,exact:true});
async function watch(){
 await button('觀看畫面').click();
 await section.getByRole('status').filter({hasText:'畫面已連線'}).waitFor({timeout:30000});
 await page.waitForTimeout(700);
 const frame=await section.locator('canvas').evaluate(c=>({width:c.width,height:c.height,colors:new Set(c.getContext('2d').getImageData(0,0,c.width,c.height).data).size}));
 assert.ok(frame.width>100&&frame.height>100&&frame.colors>10);
 return frame;
}
async function type(text){
 const canvas=section.locator('canvas');
 const dimensions=await canvas.evaluate(c=>({width:c.width,height:c.height}));
 const box=await canvas.boundingBox();
 const target=JSON.parse(py("from pathlib import Path;print(Path('/lab/input-target.json').read_text())"));
 await canvas.click({position:{x:target.x*box.width/dimensions.width,y:target.y*box.height/dimensions.height}});
 await page.keyboard.press('End');
 await page.keyboard.type(text);
 await page.waitForTimeout(400);
}
async function takeOver(){
 await button('接管操作').click();
 await section.getByTestId('control-state').filter({hasText:'人工操作中'}).waitFor();
 // The official RFB bridge refreshes cross-process leases at most every 250 ms.
 await page.waitForTimeout(350);
}
async function handBack(){await button('交回控制權').click();await section.getByRole('status').filter({hasText:'已交回'}).waitFor();}
async function reconnect(){
 if(!await button('重新連線').count())await section.getByRole('button',{name:'更多操作',exact:true}).click();
 await button('重新連線').click();
 await page.waitForFunction(()=>document.querySelector('[data-testid=bot-screen]')?.dataset.connection==='ready');
}
try{
 let available=false;
 for(let attempt=0;attempt<30;attempt++){
  try{if((await page.request.get(origin+'/login',{timeout:2000})).status()===200){available=true;break;}}catch{}
  await new Promise(resolve=>setTimeout(resolve,500));
 }
 assert.ok(available,'Dashboard readiness timed out');
 const mounts=JSON.parse(execFileSync('docker',['inspect',container,'--format','{{json .Mounts}}'],{encoding:'utf8'}));
 assert.ok(mounts.every(m=>m.Type==='bind'&&m.RW===false&&m.Source.toLowerCase().replaceAll('\\','/').includes('/projects/bot-screen/')));
 result.gates.isolatedReadOnlySourceMounts=true;
 const credentials=JSON.parse(py("from pathlib import Path;print(Path('/lab/test-login.json').read_text())"));
 assert.equal((await page.request.post(origin+'/auth/password-login',{data:{...credentials,provider:'basic'}})).status(),200);
 await page.goto(origin+'/bot-screen');
 await section.waitFor({state:'visible'});
 await page.waitForFunction(()=>document.querySelector('[data-testid=bot-screen]')?.dataset.connection==='ready');
 const plugins=await page.evaluate(()=>window.__HERMES_PLUGIN_SDK__.fetchJSON('/api/dashboard/plugins'));
 assert.ok(plugins.some(p=>p.name==='bot-screen-lab'));result.gates.pluginDiscovered=true;
 await probe();
 let s=await status();
 if(!s.running){await button('啟動並觀看').click();await section.getByRole('status').filter({hasText:'畫面已連線'}).waitFor({timeout:45000});}
 s=await status();assert.equal(s.running,true);result.gates.desktopStarted=true;
 docker(['env','PYTHONPATH=/opt/hermes','/opt/hermes-venv/bin/python','/integration/fixture.py']);
 await page.waitForTimeout(800);
 result.framebuffer=await watch();result.gates.realFramebuffer=true;
 const before=input();await type('WATCH-BLOCKED');assert.equal(input(),before);result.gates.watchInputBlocked=true;
 await takeOver();await type('BOT-SCREEN-HUMAN');
 assert.equal(input(),before+'BOT-SCREEN-HUMAN');assert.equal((await status()).lease.holder,'human');result.gates.realHumanInput=true;
 await page.screenshot({path:'evidence/takeover.png'});
 await handBack();const after=input();await type('HANDBACK-BLOCKED');assert.equal(input(),after);assert.equal((await status()).lease.holder,'agent');result.gates.handbackInputBlocked=true;
 await page.screenshot({path:'evidence/handback.png'});
 result.beforeIdentity=identity();
 // All sockets undergo abnormal close, the same backend exclusion branch as a dropped link.
 await takeOver();
 await page.evaluate(()=>{for(const s of window.__testSockets)if(s.readyState===1)s.close(4002,'integration abnormal disconnect');});
 await section.getByRole('status').filter({hasText:'連線中斷'}).waitFor();
 await probe();assert.equal((await status()).lease.holder,'human');result.gates.abnormalDisconnectRetainsHumanLease=true;
 for(let i=0;i<3;i++){
  await reconnect();
  const frame=await watch();assert.equal(await section.getByTestId('control-state').innerText(),'觀看模式');
  const prior=input();await type('RECONNECT-BLOCKED');assert.equal(input(),prior);
  await takeOver();await page.keyboard.press('End');await type('-CYCLE-'+i);assert.equal(input(),prior+'-CYCLE-'+i);
  await handBack();const stable=input();await type('POST-RECONNECT-BLOCKED');assert.equal(input(),stable);
  assert.equal((await status()).lease.holder,'agent');assert.deepEqual(identity(),result.beforeIdentity);
  result.cycles.push({index:i,framebuffer:frame,watchBlocked:true,inputDelivered:true,handbackBlocked:true,sameDesktop:true});
  if(i<2){await page.evaluate(()=>{for(const s of window.__testSockets)if(s.readyState===1)s.close(4002,'integration reconnect cycle');});await page.waitForTimeout(300);await probe();}
 }
 result.gates.reconnectThreeCycles=true;
 const tickets=await page.evaluate(async()=>{
  const o=await window.testRpc.request('display.observe',{profile:'bot-screen-lab'});
  const u=new URL(o.path,location.origin);u.protocol='ws:';u.searchParams.set('display_ticket',o.ticket);
  const attempt=()=>new Promise(resolve=>{const s=new WebSocket(u);s.binaryType='arraybuffer';const timer=setTimeout(()=>{s.close();resolve({timeout:true})},5000);s.onmessage=e=>{clearTimeout(timer);s.close(1000);resolve({bytes:e.data.byteLength})};s.onclose=e=>{clearTimeout(timer);resolve({code:e.code})};});
  return {first:await attempt(),replay:await attempt()};
 });
 assert.ok(tickets.first.bytes>0);assert.equal(tickets.replay.code,4401);result.ticketChecks=tickets;result.gates.singleUseTicketEnforced=true;
 const unauth=await browser.newContext();const p=await unauth.newPage();await p.goto(origin+'/login');
 const denied=await p.request.get(origin+'/api/config',{maxRedirects:0});
 result.unauthorized={status:denied.status(),redirect:denied.headers().location};
 assert.ok([302,303,401,403].includes(denied.status()));
 if([302,303].includes(denied.status()))assert.ok(denied.headers().location.includes('/login'));
 result.unauthorized.sockets=await p.evaluate(async()=>{
  const out={};for(const path of ['/api/ws','/api/display/ws'])out[path]=await new Promise(resolve=>{
   const s=new WebSocket(location.origin.replace('http:','ws:')+path);
   const timer=setTimeout(()=>{s.close();resolve({timeout:true})},5000);
   s.onmessage=()=>{clearTimeout(timer);s.close();resolve({unexpectedData:true})};
   s.onclose=e=>{clearTimeout(timer);resolve({code:e.code})};
  });return out;
 });
 for(const r of Object.values(result.unauthorized.sockets)){assert.ok([1006,4401,4403,1008].includes(r.code));assert.ok(!r.unexpectedData);}
 await unauth.close();result.gates.unauthorizedRejected=true;
 await page.screenshot({path:'evidence/reconnected.png'});
 assert.equal(result.consoleErrors.length,0);result.gates.noBrowserRuntimeErrors=true;result.passed=true;
}catch(e){result.errors.push(e.message);result.pageStatus=await section.getByRole('status').innerText().catch(()=>null);await page.screenshot({path:'evidence/failure.png'}).catch(()=>{});process.exitCode=1;}
finally{
 result.finishedAt=new Date().toISOString();
 // Keep exact kernel identities only in memory for assertions, not in shared evidence.
 if(result.beforeIdentity)result.beforeIdentity.record='<PROCESS_IDENTITY_REDACTED>';
 await writeFile('evidence/acceptance.json',JSON.stringify(result,null,2));
 console.log(JSON.stringify(result,null,2));await browser.close();
}
