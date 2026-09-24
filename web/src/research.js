import {deployment} from './deployment.js';
const uuid = () => crypto.randomUUID().replaceAll('-','');
const copy = x => structuredClone(x);
export function download(data, name, type='application/json') {
  const url=URL.createObjectURL(data instanceof Blob?data:new Blob([data],{type}));const a=document.createElement('a');a.href=url;a.download=name;a.click();setTimeout(()=>URL.revokeObjectURL(url),10000);
}

export class ResearchSession {
  static async open(onStatus) {
    const r=new ResearchSession();r.onStatus=onStatus;r.params=new URLSearchParams(location.search);r.localOnly=deployment.storage==='local';
    r.db=await new Promise((resolve,reject)=>{const req=indexedDB.open(r.localOnly?'common-table-godot-preview':'common-table-godot',1);req.onupgradeneeded=()=>req.result.createObjectStore('sessions');req.onsuccess=()=>resolve(req.result);req.onerror=()=>reject(new Error('Browser storage is unavailable. Enable site storage and reload.'));});
    r.key=JSON.stringify(['participantId','PROLIFIC_PID','studyId','STUDY_ID','sessionId','SESSION_ID','condition'].map(k=>r.params.get(k)||''));
    if(r.localOnly)r.key=new URL('./',location.href).pathname+':'+r.key;
    let saved=await new Promise((resolve,reject)=>{const q=r.db.transaction('sessions').objectStore('sessions').get(r.key);q.onsuccess=()=>resolve(q.result);q.onerror=()=>reject(q.error);});
    if(saved){r.data=saved.data;r.token=saved.token;r.pending=saved.pending;r.acked=saved.acked||0;r.restored=true;}
    else {
      const condition=r.params.get('condition')||'default';let config;
      if(r.localOnly){
        if(!Object.hasOwn(deployment.conditions,condition))throw new Error('Unknown study condition.');
        config=copy(deployment.conditions[condition]);
      }else{
        const response=await fetch('/api/config?condition='+encodeURIComponent(condition));
        config=await response.json();if(!response.ok)throw new Error(config.error||'Could not load the study settings.');
      }
      r.data={schemaVersion:1,engine:'godot',sessionId:uuid(),participantId:r.params.get('participantId')||r.params.get('PROLIFIC_PID')||'',studyId:r.params.get('studyId')||r.params.get('STUDY_ID')||'',sourceSessionId:r.params.get('sessionId')||r.params.get('SESSION_ID')||'',condition:config.condition,config,revision:1,completed:false,startedAt:new Date().toISOString(),completedAt:'',elapsedSeconds:0,portions:[],events:[]};
      if(r.localOnly)r.data.storageMode='local';
      r.token=uuid()+uuid();r.pending=[];r.acked=0;
    }
    r.baseTime=performance.now();r.baseElapsed=r.data.elapsedSeconds;r.writeQueue=Promise.resolve();r.flushing=false;r.parentOrigin='';r.surveyAck=false;
    if(window.parent!==window){if(r.localOnly)throw new Error('Open this preview directly in a browser tab. Survey collection requires the research server.');const origin=r.params.get('parentOrigin');if(!origin||!r.data.config.allowedParentOrigins.includes(origin))throw new Error('This survey origin is not configured. Ask the researcher to add it to the server’s allowed origins.');r.parentOrigin=origin;}
    window.addEventListener('message',event=>{if(event.origin===r.parentOrigin&&event.source===window.parent&&event.data?.type==='buffet:ack'&&event.data.sessionId===r.data.sessionId&&event.data.revision===r.data.revision){r.surveyAck=true;r.status();}});
    if(!r.localOnly){
      window.addEventListener('online',()=>r.flush());
      window.addEventListener('pagehide',()=>{if(r.acked<r.data.revision)fetch('/api/sessions',{method:'POST',headers:r.headers(),body:JSON.stringify(r.data),keepalive:true}).catch(()=>{});});
      r.timer=setInterval(()=>{r.flush();r.handoff();},3000);
    }
    await r.persist();r.flush();return r;
  }
  get config(){return this.data.config;}
  get elapsed(){return this.data.completed?this.data.elapsedSeconds:this.baseElapsed+(performance.now()-this.baseTime)/1000;}
  headers(type='application/json'){return {'Content-Type':type,'X-Session-Token':this.token};}
  persist(){const snapshot=copy({data:this.data,token:this.token,pending:this.pending,acked:this.acked});this.writeQueue=this.writeQueue.then(()=>new Promise((resolve,reject)=>{const tx=this.db.transaction('sessions','readwrite');tx.objectStore('sessions').put(snapshot,this.key);tx.oncomplete=resolve;tx.onerror=()=>reject(tx.error);}));this.writeQueue.catch(()=>{this.storageFailed=true;this.onStatus('Browser storage is full — download a recovery copy');});return this.writeQueue;}
  changed(){this.data.revision++;if(!this.data.completed)this.data.elapsedSeconds=Math.round(this.elapsed*1000)/1000;this.persist();this.status();queueMicrotask(()=>this.flush());}
  record(eventType,foodId='',portionId='',detail=''){this.data.events.push({eventId:uuid(),eventType,foodId,portionId,plateId:foodId?'main':'',elapsedSeconds:Math.round(this.elapsed*1000)/1000,detail});this.changed();}
  setPortions(portions){this.data.portions=portions.map(p=>({portionId:p.portionId,foodId:p.foodId,plateId:'main',addedAt:p.addedAt,position:{x:p.x,y:p.y,z:p.z},rotation:p.angle}));}
  async queueScreenshot(data){const id=uuid();this.pending.push({id,data});this.record('screenshot_captured','',id);await this.persist();await this.flush();}
  complete(){if(this.data.completed)return;this.record('complete');this.data.completedAt=new Date().toISOString();this.data.elapsedSeconds=Math.round(this.elapsed*1000)/1000;this.data.completed=true;this.changed();}
  get saved(){return this.acked===this.data.revision&&(this.localOnly||this.pending.length===0)&&!this.storageFailed;}
  status(){this.onStatus(this.storageFailed?'Browser storage is full — download a recovery copy':this.saved?(this.localOnly?'Saved on this device':this.data.completed?(this.parentOrigin?(this.surveyAck?'Saved · survey received your choices':'Saved · sending to your survey'):'Meal saved'):'Choices saved'):(this.offline?'Saved on this device · reconnect to send':'Saving your choices…'));}
  flush(){
    if(this.flushPromise)return this.flushPromise;
    if(this.storageFailed)return Promise.resolve();
    this.flushPromise=this.doFlush().finally(()=>{this.flushPromise=null;});
    return this.flushPromise;
  }
  async doFlush(){
    this.flushing=true;
    try {
      await this.writeQueue;
      if(this.localOnly){
        // Keep screenshots with the browser snapshot so the recovery download
        // includes them. Acknowledge only revisions committed to IndexedDB.
        while(this.acked<this.data.revision){const revision=this.data.revision;await this.persist();this.acked=revision;}
        this.offline=false;this.error='';return;
      }
      while(this.acked<this.data.revision||this.pending.length){
        const snapshot=copy(this.data);
        if(this.acked<snapshot.revision){const response=await fetch('/api/sessions',{method:'POST',headers:this.headers(),body:JSON.stringify(snapshot),signal:AbortSignal.timeout(12000)});const body=await response.json();if(!response.ok)throw new Error(body.error||'Save failed');if(body.revision!==snapshot.revision)throw new Error('Save revision mismatch');this.acked=snapshot.revision;await this.persist();}
        if(this.pending.length){const item=this.pending[0],blob=await(await fetch(item.data)).blob();const response=await fetch('/api/screenshots/'+this.data.sessionId,{method:'POST',headers:this.headers('image/png'),body:blob,signal:AbortSignal.timeout(12000)});const result=await response.json();if(!response.ok)throw new Error(result.error||'Screenshot save failed');this.pending.shift();this.record('screenshot_saved','',result.imageId);await this.persist();}
      }
      this.offline=false;this.error='';this.handoff();
    }catch(error){this.offline=true;this.error=error.message;}
    finally{this.flushing=false;this.status();}
  }
  handoff(){if(!this.localOnly&&this.data.completed&&this.saved&&this.parentOrigin&&!this.surveyAck)window.parent.postMessage({type:'buffet:complete',schemaVersion:1,session:copy(this.data)},this.parentOrigin);}
  recovery(){download(JSON.stringify({schemaVersion:1,session:this.data,...(this.localOnly?{savedImages:this.pending}:{pendingImages:this.pending})},null,2),`buffet-${this.data.sessionId}.json`);}
}
