import {createRequire} from 'node:module';
import {writeFile} from 'node:fs/promises';
import assert from 'node:assert/strict';
const require=createRequire(new URL('../bot-screen-plugin/package.json',import.meta.url));
const {chromium}=require('playwright');
const origin=process.argv[2];
assert.equal(origin,'http://127.0.0.1:9127');
const browser=await chromium.launch({executablePath:'C:/Program Files/Google/Chrome/Application/chrome.exe',headless:true});
const context=await browser.newContext({viewport:{width:1440,height:1000}});
const page=await context.newPage();
const result={passed:false,gates:{},errors:[]};
page.on('pageerror',error=>result.errors.push(error.message));
try{
 await page.goto(origin+'/bot-screen');
 await page.waitForFunction(()=>document.querySelector('[data-testid=bot-screen]')?.dataset.connection==='ready',{},{timeout:45000});
 const profiles=await page.evaluate(async()=> (await window.__HERMES_PLUGIN_SDK__.api.getStatus()).profiles);
 assert.ok(profiles.includes('bot-screen-lab'));result.gates.newIsolatedProfileDiscovered=true;
 const section=page.getByTestId('bot-screen');
 await section.locator('[data-action=watch]').click();
 await page.waitForFunction(()=>document.querySelector('[data-testid=bot-screen]')?.dataset.connected==='true');
 const frame=await section.locator('canvas').evaluate(c=>({width:c.width,height:c.height}));
 assert.ok(frame.width>100&&frame.height>100);result.gates.actualCanvasFromInstalledPlugin=true;
 for(const locale of ['zh-Hant','zh-Hans','en']){
  await section.locator('.bs-more-button').click();await section.getByTestId('language-select').selectOption(locale);
  assert.equal(await section.getAttribute('data-locale'),locale);
 }
 result.gates.threeLanguagesSwitch=true;
 await page.screenshot({path:'evidence/one-click-installed-windows.png'});
 assert.deepEqual(result.errors,[]);result.passed=true;
}finally{await browser.close();await writeFile('evidence/installer-browser.json',JSON.stringify(result,null,2));}
console.log(JSON.stringify(result,null,2));
