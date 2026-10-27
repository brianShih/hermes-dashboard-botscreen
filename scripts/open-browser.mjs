import {createRequire} from 'node:module';
import {execFileSync} from 'node:child_process';
const require=createRequire(new URL('../bot-screen-plugin/package.json',import.meta.url));
const {chromium}=require('playwright');
const origin='http://127.0.0.1:9124';
const credentials=JSON.parse(execFileSync('docker',['exec','bot-screen-integration',
 '/opt/hermes-venv/bin/python','-c',"from pathlib import Path;print(Path('/lab/test-login.json').read_text())"],{encoding:'utf8'}));
const browser=await chromium.launch({executablePath:'C:/Program Files/Google/Chrome/Application/chrome.exe',headless:false,args:['--start-maximized']});
const page=await browser.newPage({viewport:null});
try{
 if((await page.request.post(origin+'/auth/password-login',{data:{...credentials,provider:'basic'}})).status()!==200)throw Error('Isolated dashboard login failed');
 await page.goto(origin+'/bot-screen');
 await page.waitForFunction(()=>document.querySelector('[data-testid=bot-screen]')?.dataset.connection==='ready');
 if(await page.getByTestId('bot-screen').getAttribute('data-running')==='true'){
  await page.locator('[data-action=watch]').click();
  await page.waitForFunction(()=>document.querySelector('[data-testid=bot-screen]')?.dataset.connected==='true');
 }

 console.log('Dedicated authenticated Bot Screen browser opened. Close this window to finish.');
 await new Promise(resolve=>browser.on('disconnected',resolve));
}catch(e){await browser.close();throw e;}
