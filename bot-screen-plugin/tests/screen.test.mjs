import {test} from 'node:test';
import assert from 'node:assert/strict';
import {ScreenController, socketURL} from '../src/screen.mjs';

test('socket URL keeps origin and carries only one-use display ticket',()=>{
 assert.equal(socketURL('http://127.0.0.1:9119','/api/display/ws','display_ticket','abc'),'ws://127.0.0.1:9119/api/display/ws?display_ticket=abc');
 assert.throws(()=>socketURL('http://127.0.0.1:9119','https://evil.test/ws','ticket','abc'));
});
test('protected profiles cannot receive screen mutations',async()=>{
 const c=new ScreenController(async()=>{throw Error('must not dispatch')},'default');
 await assert.rejects(c.start(),/isolated/);
});
test('viewer starts read-only and takeover uses minted id',async()=>{
 const calls=[]; const c=new ScreenController(async(m,p)=>{calls.push([m,p]); return m==='display.observe'?{viewer_id:'minted',ticket:'once',path:'/api/display/ws'}:{lease:{holder:'human'}};});
 await c.observe(); assert.equal(c.controlling,false); await c.takeOver();
 assert.equal(c.controlling,true); assert.equal(calls[1][1].viewer_id,'minted');
 assert.equal(calls[1][1].profile,'bot-screen-lab');
});
test('takeover is refused before observe',async()=>{
 const c=new ScreenController(async()=>{}); await assert.rejects(c.takeOver(),/Observe/);
});
test('failed acquisition never enables input',async()=>{
 const c=new ScreenController(async m=>{if(m==='display.observe')return {viewer_id:'v'};throw Error('refused')});
 await c.observe();await assert.rejects(c.takeOver());assert.equal(c.controlling,false);
});
test('handback disables input before awaiting server',async()=>{
 let c; c=new ScreenController(async m=>{if(m==='display.observe')return {viewer_id:'v'};if(m==='display.lease.acquire')return {lease:{holder:'human'}};if(m==='display.lease.release')assert.equal(c.controlling,false);return {lease:{holder:'agent'}}});
 await c.observe();await c.takeOver();await c.handBack();assert.equal(c.controlling,false);
});
test('disconnect fails closed without silently releasing lease',()=>{
 const c=new ScreenController(()=>{throw Error('no dispatch')});c.controlling=true;c.disconnect();assert.equal(c.controlling,false);assert.equal(c.viewerId,null);
});
test('protected profiles cannot observe a screen',async()=>{
 const c=new ScreenController(()=>{throw Error('must not dispatch')},'meta-ops');await assert.rejects(c.observe(),/isolated/);
});
