import {createRequire} from 'node:module';
import {execFileSync} from 'node:child_process';
import {writeFile} from 'node:fs/promises';
import assert from 'node:assert/strict';
import {fileURLToPath} from 'node:url';
const root=fileURLToPath(new URL('../',import.meta.url));process.chdir(root);
const require=createRequire(new URL('../bot-screen-plugin/package.json',import.meta.url));
const {chromium}=require('playwright');
const browser=await chromium.launch({executablePath:'C:/Program Files/Google/Chrome/Application/chrome.exe',headless:true});
const context=await browser.newContext({viewport:{width:1600,height:1000}});
await context.addInitScript(()=>{localStorage.setItem('bot-screen:language:v1','zh-Hant');const Native=window.WebSocket;window.__reviewSockets=[];window.WebSocket=new Proxy(Native,{construct(Target,args){const ws=new Target(...args);window.__reviewSockets.push(ws);return ws;}});});
const page=await context.newPage(), origin='http://127.0.0.1:9124';
const result={gates:{},layouts:[],errors:[],passed:false};
page.on('pageerror',e=>result.errors.push(e.message));
const credentials=JSON.parse(execFileSync('docker',['exec','bot-screen-integration','/opt/hermes-venv/bin/python','-c',"from pathlib import Path;print(Path('/lab/test-login.json').read_text())"],{encoding:'utf8'}));
const section=page.getByTestId('bot-screen');
let timeoutPage;
const ready=()=>page.waitForFunction(()=>document.querySelector('[data-testid=bot-screen]')?.dataset.connection==='ready');
async function watch(){await section.getByRole('button',{name:'觀看畫面',exact:true}).click();await section.getByRole('status').filter({hasText:'畫面已連線'}).waitFor({timeout:30000});await page.waitForTimeout(500);}
try{
 assert.equal((await page.request.post(origin+'/auth/password-login',{data:{...credentials,provider:'basic'}})).status(),200);
 await page.goto(origin+'/bot-screen');await ready();
 await section.getByRole('heading',{name:'你的桌面已準備好'}).waitFor();
 assert.equal(await section.getByRole('button',{name:'觀看畫面',exact:true}).count(),1);
 result.gates.guidedEmptyState=true;await page.screenshot({path:'evidence/ui-empty.png'});
 const more=section.getByRole('button',{name:'更多操作',exact:true});
 await more.focus();await page.keyboard.press('Enter');assert.equal(await more.getAttribute('aria-expanded'),'true');
 await page.keyboard.press('Tab');assert.equal(await page.evaluate(()=>document.activeElement?.id),'bs-language-select');
 await page.keyboard.press('Tab');assert.equal(await page.evaluate(()=>document.activeElement?.textContent),'重新連線');
 await page.keyboard.press('Escape');assert.equal(await more.getAttribute('aria-expanded'),'false');assert.equal(await more.evaluate(e=>document.activeElement===e),true);
 result.gates.keyboardMenuAndEscape=true;
 await watch();
 await page.screenshot({path:'evidence/ui-after.png'});
 for(const [width,height] of [[1920,1080],[1280,720],[768,1024],[390,844]]){
  await page.setViewportSize({width,height});await page.waitForTimeout(450);
  const shell=await section.boundingBox(),viewer=await section.getByTestId('screen-viewer').boundingBox();
  assert.ok(shell.x>=0&&shell.x+shell.width<=width+1);assert.ok(shell.y+shell.height<=height+1);assert.ok(viewer.height>=120);
  const overflow=await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth);assert.equal(overflow,false);
  const minimumText=await section.evaluate(e=>Math.min(...Array.from(e.querySelectorAll('p,span,strong,button')).filter(n=>getComputedStyle(n).display!=='none'&&n.getBoundingClientRect().width>0&&n.textContent.trim()).map(n=>parseFloat(getComputedStyle(n).fontSize)).filter(v=>v>0)));
  assert.ok(minimumText>=12,`Text too small: ${minimumText}`);
  result.layouts.push({width,height,viewerHeight:viewer.height,horizontalOverflow:false,minimumText});
  await page.screenshot({path:`evidence/ui-${width}.png`});
 }
 result.gates.responsiveFourSizes=true;
 await page.setViewportSize({width:1600,height:1000});await page.waitForTimeout(300);
 await section.getByRole('button',{name:'全螢幕',exact:true}).click();await page.waitForFunction(()=>!!document.fullscreenElement);
 const full=await section.boundingBox();assert.equal(full.x,0);assert.equal(full.y,0);assert.equal(full.width,1600);
 await page.screenshot({path:'evidence/ui-fullscreen.png'});
 await section.getByRole('button',{name:'離開全螢幕',exact:true}).click();await page.waitForFunction(()=>!document.fullscreenElement);result.gates.fullscreenRoundTrip=true;
 await page.evaluate(()=>{for(const s of window.__reviewSockets)if(s.readyState===1)s.close(4002,'UI recovery check');});
 await page.waitForFunction(()=>document.querySelector('[data-testid=bot-screen]')?.dataset.connection==='disconnected');
 await page.screenshot({path:'evidence/ui-disconnected.png'});
 assert.equal(await section.getByRole('button',{name:'重新連線',exact:true}).count(),1);
 await section.getByRole('button',{name:'重新連線',exact:true}).click();await ready();await watch();result.gates.clearDisconnectRecovery=true;
 const timeoutContext=await browser.newContext({viewport:{width:1280,height:800}});
 // Preserve native WebSocket prototypes: noVNC rejects Playwright's routed socket shim.
 // Only this test page drops inbound display frames to exercise the real 15 s UI deadline.
 await timeoutContext.addInitScript(()=>{localStorage.setItem('bot-screen:language:v1','zh-Hant');
  const Native=window.WebSocket;window.__displayFaultInjected=false;
  window.WebSocket=new Proxy(Native,{construct(Target,args){
   const ws=new Target(...args);
   if(String(args[0]).includes('/api/display/ws')){
    window.__displayFaultInjected=true;
    Object.defineProperty(ws,'onmessage',{enumerable:true,configurable:true,get(){return null;},set(){}});
   }
   return ws;
  }});
 });
 timeoutPage=await timeoutContext.newPage();
 await timeoutPage.request.post(origin+'/auth/password-login',{data:{...credentials,provider:'basic'}});
 await timeoutPage.goto(origin+'/bot-screen');await timeoutPage.waitForFunction(()=>document.querySelector('[data-testid=bot-screen]')?.dataset.connection==='ready');
 await timeoutPage.getByRole('button',{name:'觀看畫面',exact:true}).click();
 await timeoutPage.waitForFunction(()=>window.__displayFaultInjected===true);
 await timeoutPage.getByTestId('bot-screen').getByRole('status').filter({hasText:'畫面連線逾時'}).waitFor({timeout:22000});
 assert.equal(await timeoutPage.getByRole('button',{name:'觀看畫面',exact:true}).isEnabled(),true);
 await timeoutPage.screenshot({path:'evidence/ui-timeout.png'});result.gates.boundedFrameTimeout=true;
 await timeoutContext.close();assert.deepEqual(result.errors,[]);result.gates.noRuntimeErrors=true;result.passed=true;
}catch(error){result.errors.push(error.message);if(timeoutPage&&!timeoutPage.isClosed()){result.timeoutMessage=await timeoutPage.getByTestId('bot-screen').getByRole('status').innerText().catch(()=>null);await timeoutPage.screenshot({path:'evidence/ui-timeout-failure.png'}).catch(()=>{});}await page.screenshot({path:'evidence/ui-review-failure.png'}).catch(()=>{});process.exitCode=1;}
finally{await writeFile('evidence/ui-review.json',JSON.stringify(result,null,2));console.log(JSON.stringify(result,null,2));await browser.close();}
