const failure = (code, message) => Object.assign(new Error(message), { code });
export function socketURL(origin,path,key,ticket){
 if(!path.startsWith('/')||path.startsWith('//'))throw Error('Same-origin path required');
 const u=new URL(path,origin);if(u.origin!==new URL(origin).origin)throw Error('Same-origin required');
 u.protocol=u.protocol==='https:'?'wss:':'ws:';u.searchParams.set(key,ticket);return u.href;
}
export class ScreenController{
 constructor(rpc,profile='bot-screen-lab'){this.rpc=rpc;this.profile=profile;this.viewerId=null;this.viewerHash=null;this.profileKey=null;this.controlling=false;}
 allowed(){if(this.profile!=='bot-screen-lab')throw failure('profileIsolation', 'An isolated bot-screen-lab profile is required');}
 call(method,params={}){this.allowed();return this.rpc(method,{...params,profile:this.profile});}
 async start(){this.allowed();return this.call('display.start');}
 async observe(){this.allowed();this.controlling=false;const result=await this.call('display.observe',this.viewerId?{viewer_id:this.viewerId}:{});this.viewerId=result.viewer_id;this.profileKey=result.profile_key;const digest=await crypto.subtle.digest('SHA-256',new TextEncoder().encode(this.viewerId));this.viewerHash=Array.from(new Uint8Array(digest),b=>b.toString(16).padStart(2,'0')).join('').slice(0,12);return result;}
 async takeOver(){this.allowed();if(!this.viewerId)throw failure('observeFirst', 'Observe before taking control');this.controlling=false;const r=await this.call('display.lease.acquire',{viewer_id:this.viewerId,reason:'Dashboard human takeover'});this.controlling=r.lease?.holder==='human';if(!this.controlling)throw failure('takeoverDenied', 'Human control was not granted');return r;}
 async handBack(){this.allowed();this.controlling=false;if(!this.viewerId)throw failure('observeFirst', 'Observe before handback');return this.call('display.lease.release',{viewer_id:this.viewerId});}
 disconnect(){this.controlling=false;this.viewerId=null;}
}
export class RpcClient{
 constructor(){this.pending=new Map();this.seq=0;this.onDisconnect=()=>{};this.onEvent=()=>{};}
 async connect(){
 const url=await window.__HERMES_PLUGIN_SDK__.buildWsUrl('/api/ws');
 this.ws=new WebSocket(url);
 this.ws.onmessage=e=>{for(const line of String(e.data).split('\n').filter(Boolean)){let m;try{m=JSON.parse(line)}catch{continue}const p=this.pending.get(m.id);if(p){clearTimeout(p.timer);this.pending.delete(m.id);m.error?p.reject(Error(m.error.message)):p.resolve(m.result);}else this.onEvent(m);}};
 this.ws.onclose=()=>{for(const p of this.pending.values()){clearTimeout(p.timer);p.reject(failure('connectionClosed', 'Connection closed'));}this.pending.clear();this.onDisconnect();};
 await new Promise((resolve,reject)=>{const timer=setTimeout(()=>{this.ws.close();reject(failure('connectionTimeout', 'Connection timeout'))},15000);this.ws.onopen=()=>{clearTimeout(timer);resolve()};this.ws.onerror=()=>{clearTimeout(timer);reject(failure('connectionFailed', 'Authenticated WebSocket failed'))};});
 }
 request(method,params){if(this.ws?.readyState!==1)return Promise.reject(failure('notConnected', 'Not connected'));return new Promise((resolve,reject)=>{const id='screen-'+ ++this.seq;const timer=setTimeout(()=>{this.pending.delete(id);reject(failure('requestTimeout', 'Request timed out'))},30000);this.pending.set(id,{resolve,reject,timer});this.ws.send(JSON.stringify({jsonrpc:'2.0',id,method,params})+'\n');});}
 close(){this.ws?.close(1000);}
}
