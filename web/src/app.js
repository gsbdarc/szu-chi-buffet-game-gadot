import {ResearchSession,download} from './research.js';
const $=id=>document.getElementById(id);
const escapeHTML=s=>String(s).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const wait=ms=>new Promise(resolve=>setTimeout(resolve,ms));
let game;

// Godot owns the 3D scene and all placement/picking calculations. This shell
// retains the comparison game's interface and browser/research persistence.
class GodotClient {
  constructor(onState){
    this.onState=onState;this.pending=new Map();this.nextId=0;
    this.ready=new Promise(resolve=>this.resolveReady=resolve);
    window.godotBridge={
      register:(callback,info)=>{this.callback=callback;this.info=JSON.parse(info);this.resolveReady();},
      resolve:(id,json)=>{const result=JSON.parse(json),pending=this.pending.get(id);if(!pending)return;clearTimeout(pending.timer);this.pending.delete(id);if(result.state)this.onState(result.state);pending.resolve(result);},
      state:json=>this.onState(JSON.parse(json))
    };
  }
  async start(canvas){
    const response=await fetch('engine/config.json');if(!response.ok)throw new Error('The Godot web export is missing. Build it before starting the server.');
    const config=await response.json();
    this.engine=new Engine({...config,canvas,canvasResizePolicy:0,focusCanvas:false});
    const resize=()=>{const rect=canvas.getBoundingClientRect(),ratio=Math.min(devicePixelRatio||1,1.5);canvas.width=Math.max(1,Math.round(rect.width*ratio));canvas.height=Math.max(1,Math.round(rect.height*ratio));};
    resize();this.resizeObserver=new ResizeObserver(resize);this.resizeObserver.observe(canvas);
    await this.engine.startGame({onProgress:(current,total)=>{$('loading-text').textContent=total?`Loading the dining hall · ${Math.round(current/total*100)}%`:'Loading the dining hall…';},onPrintError:message=>console.error('Godot:',message)});
    await Promise.race([this.ready,new Promise((_,reject)=>setTimeout(()=>reject(new Error('Godot could not start the scene.')),90000))]);
  }
  call(action,payload={}){
    return new Promise((resolve,reject)=>{const id=++this.nextId,timer=setTimeout(()=>{this.pending.delete(id);reject(new Error('The game took too long to respond. Reload to restore your meal.'));},90000);this.pending.set(id,{resolve,reject,timer});this.callback(JSON.stringify({id,action,payload}));});
  }
}

class BuffetGame {
  constructor(research,foods){this.research=research;this.foods=foods;this.portions=[];this.station=0;this.started=false;this.moving=false;this.mutating=false;this.plateView=false;this.finishing=false;this.finished=research.data.completed;this.selected=null;this.soundOn=research.config.soundEnabled;this.dialog=$('dialog');this.state={portions:[],points:{portions:[]}};}
  async init(){
    this.canvas=$('scene');this.native=new GodotClient(state=>this.accept(state));await this.native.start(this.canvas);
    await this.native.call('configure',{foods:this.foods,config:this.research.config,portions:this.research.data.portions,completed:this.finished});
    this.bind();$('loading').hidden=true;
    if(this.finished){this.started=true;await this.native.call('begin',{animate:false});await this.moveView(true,false);this.showCompletion();}else this.welcome();this.refresh();
    Object.defineProperty(window,'buffet',{value:{snapshot:()=>({station:this.station,started:this.started,moving:this.moving||this.mutating,plateView:this.plateView,finished:this.finished,selected:this.selected?.portionId,session:structuredClone(this.research.data),saved:this.research.saved,saveError:this.research.error,engine:this.state.engine,models:this.state.models,fps:this.state.fps,lastActionMs:this.state.lastActionMs,portions:this.portions.map(p=>({id:p.portionId,food:p.foodId,x:p.x,y:p.y,z:p.z,extent:p.extent}))}),point:(name,index=0)=>this.project(name,index)}});
  }
  accept(state){this.state=state;this.portions=state.portions;if(this.selected)this.selected=this.portions.find(p=>p.portionId===this.selected.portionId)||null;}
  project(name,index){const p=name==='portion'?this.state.points.portions[index]:this.state.points[name],r=this.canvas.getBoundingClientRect();return {x:r.left+p.x/this.canvas.width*r.width,y:r.top+p.y/this.canvas.height*r.height};}
  point(event){const r=this.canvas.getBoundingClientRect();return {x:(event.clientX-r.left)*this.canvas.width/r.width,y:(event.clientY-r.top)*this.canvas.height/r.height};}
  get current(){return this.foods[this.station];}
  get busy(){return this.moving||this.mutating||this.finished||this.finishing||this.capturing||!this.started||this.dialog.open;}
  async begin(){if(this.started)return;this.close();this.started=true;this.moving=true;this.overview=true;this.refresh();this.initAudio();this.research.record('begin');await wait(this.research.config.introSeconds*1000);this.overview=false;await this.native.call('begin',{station:this.station,animate:true});this.moving=false;this.research.record('station_view',this.current.id);this.refresh();}
  async moveView(plate=false,animate=true){if(this.moving)return;this.moving=true;this.plateView=plate;if(plate){clearTimeout(this.toastTimer);$('toast').classList.remove('visible');}this.refresh();try{await this.native.call('view',{station:this.station,plate,animate});}finally{this.moving=false;this.refresh();}}
  async navigate(index){if(this.busy||index<0||index>=this.foods.length)return;this.selected=null;this.station=index;this.research.record('station_view',this.current.id);this.tone(510,.055);await this.moveView(false);}
  async add(){if(this.busy)return;if(this.portions.length>=this.research.config.maxPortions){this.toast('This plate has reached the study’s portion limit.');return;}this.mutating=true;this.refresh();try{const record={portionId:crypto.randomUUID().replaceAll('-',''),foodId:this.current.id,addedAt:this.research.elapsed};await this.native.call('add',record);if(!this.portions.some(p=>p.portionId===record.portionId))throw new Error('This portion could not be placed.');this.research.setPortions(this.portions);this.research.record('portion_added',record.foodId,record.portionId);this.tone(920,.13);this.toast(this.current.name+' added · '+this.count(this.current.id)+' on your plate');}finally{this.mutating=false;this.refresh();}}
  count(id){return this.portions.filter(p=>p.foodId===id).length;}
  async remove(portion){if(this.busy||!this.research.config.allowRemoval||!portion)return;this.mutating=true;this.refresh();try{await this.native.call('remove',{portionId:portion.portionId});this.selected=null;this.research.setPortions(this.portions);this.research.record('portion_removed',portion.foodId,portion.portionId);}finally{this.mutating=false;this.refresh();}}
  async togglePlate(){if(this.busy)return;this.selected=null;this.research.record(this.plateView?'dish_view':'plate_view',this.current.id);await this.moveView(!this.plateView);}
  toast(text){$('toast').textContent=text;$('toast').classList.add('visible');clearTimeout(this.toastTimer);this.toastTimer=setTimeout(()=>$('toast').classList.remove('visible'),2700);}
  refresh(){
    const active=this.started&&!this.finished&&!this.overview;for(const id of ['dish','plate-summary'])$(id).hidden=!active;
    $('food-name').textContent=this.current.name;$('category').textContent=`${this.current.category} / ${String(this.station+1).padStart(2,'0')}`;$('description').textContent=this.current.description;$('portion').textContent=this.current.portionLabel+' per selection';$('dish-count').textContent=this.count(this.current.id)+' of this dish on your plate';
    $('total').textContent=this.portions.length+' portion'+(this.portions.length===1?'':'s');$('view').textContent=this.plateView?'Return to dish':'View plate';$('sound').textContent=this.soundOn?'Sound on':'Sound off';$('sound').disabled=!this.research.config.soundEnabled;
    $('previous').textContent=this.station?`‹ ${this.foods[this.station-1].name}`:'Start of the buffet';$('next').textContent=this.station<this.foods.length-1?`${this.foods[this.station+1].name} ›`:'End of the buffet';
    $('previous').disabled=this.busy||this.station===0;$('next').disabled=this.busy||this.station===this.foods.length-1;$('add').disabled=this.busy||this.plateView;$('view').disabled=this.moving||this.finishing||this.capturing;$('review').disabled=this.moving||this.finishing||this.capturing;
    $('undo').hidden=!this.research.config.allowRemoval;$('undo').disabled=this.busy||!this.portions.length;$('photo').hidden=!this.research.config.screenshotsEnabled;$('photo').disabled=this.busy||this.capturing;
    $('plate-tools').hidden=!this.plateView||this.finished||this.finishing;$('remove').hidden=!this.selected||!this.research.config.allowRemoval;$('selected-name').textContent=this.selected?this.foods.find(f=>f.id===this.selected.foodId).name:'Select a portion to move or remove it.';
    $('progress-label').textContent=this.started?`${String(this.station+1).padStart(2,'0')} / ${this.foods.length} · CHOOSE AT YOUR OWN PACE`:'';$('progress').firstElementChild.style.width=this.started?`${(this.station+1)/this.foods.length*100}%`:'0';
  }
  modal(title,body,actions,locked=false){this.previousFocus=document.activeElement;$('dialog-title').textContent=title;$('dialog-body').innerHTML=body;$('dialog-actions').replaceChildren();$('close-dialog').hidden=locked;this.locked=locked;for(const [text,fn,primary] of actions){const b=document.createElement('button');b.textContent=text;if(primary)b.className='primary';b.onclick=fn;$('dialog-actions').append(b);}if(!this.dialog.open)this.dialog.showModal();this.refresh();}
  close(){this.dialog.close();this.refresh();this.previousFocus?.focus();}
  welcome(){this.modal(this.research.config.studyTitle,`<p>Build a plate as you would in a cafeteria.<br>Take your time and choose what you would like.</p><div class="steps"><div><b>01 &nbsp; Browse</b><p>Move left or right along the buffet.</p></div><div><b>02 &nbsp; Serve</b><p>Tap a dish or drag it onto your plate.</p></div><div><b>03 &nbsp; Review</b><p>Check your plate, then finish your meal.</p></div></div><p class="study-instructions">${escapeHTML(this.research.config.instructions)}</p>${this.research.localOnly?'<p>Your meal and photographs are saved only in this browser. Download a copy to keep them.</p>':''}`,[[this.portions.length?'Continue your plate →':'Explore the buffet →',()=>this.begin(),true]],true);}
  help(){if(this.moving||this.finishing)return;this.modal('Make yourself a plate',`<p>Use the arrows to explore the dishes. Click the current dish or <b>Add one portion</b> to serve it. You can also drag from its tray onto your plate.</p><p>Open <b>View plate</b> to select and rearrange individual portions.${this.research.config.allowRemoval?' Use Undo last or select a portion to remove it.':''}</p><p>When you are ready, choose <b>Review meal</b> and confirm. ${this.research.config.screenshotsEnabled?'Photograph saves an image of your plate.':''}</p><p>Keyboard: ← / → to browse · Space to serve · P to view your plate.</p>`,[['Back to the buffet',()=>this.close(),true]]);}
  menu(){if(this.moving||this.finishing)return;this.modal('Today’s buffet',`<div class="menu-grid">${this.foods.map((f,i)=>`<button data-station="${i}"><img loading="lazy" src="assets/previews/${f.id}.png" alt="${escapeHTML(f.name)}">${escapeHTML(f.name)}<br><small>${this.count(f.id)} on your plate</small></button>`).join('')}</div>`,[['Back',()=>this.close()]]);for(const button of $('dialog-body').querySelectorAll('button'))button.onclick=()=>{if(!this.started||this.finished){this.close();return;}const i=Number(button.dataset.station);this.close();this.navigate(i);};}
  details(){if(this.moving)return;this.research.record('dish_information',this.current.id);this.modal(this.current.name,`<p>${escapeHTML(this.current.description)}</p><p><b>One selection:</b> ${escapeHTML(this.current.portionLabel)}</p><p>${escapeHTML(this.current.ingredients)}</p>`,[['Back to dish',()=>this.close(),true]]);}
  mealHTML(){return this.portions.length?this.foods.filter(f=>this.count(f.id)).map(f=>`<div class="meal-row"><span>${escapeHTML(f.name)}</span><span>${this.count(f.id)}</span></div>`).join(''):'<p>Your plate is empty. You can return to the buffet or finish without selecting any food.</p>';}
  async review(){if(this.busy)return;if(!this.plateView)await this.moveView(true);this.research.record('review');this.modal('Your meal, your choice',this.mealHTML()+`<p>${this.portions.length} portions selected. Ready to finish?</p>`,[['Keep exploring',()=>this.close()],['Finish meal',()=>this.finish(),true]]);}
  async capture(show=true){if(this.capturing||!this.research.config.screenshotsEnabled)return;this.capturing=true;this.refresh();try{const {data}=await this.native.call('capture');await this.research.queueScreenshot(data);if(show)this.modal('Your plate photograph',`<img class="screenshot-preview" alt="Photograph of your selected meal" src="${data}"><p>The image is linked to this session.</p>`,[['Back',()=>this.close()],['Download PNG',async()=>download(await(await fetch(data)).blob(),'my-buffet-plate.png'),true]]);return data;}finally{this.capturing=false;this.refresh();}}
  async finish(){if(this.finishing||this.finished||this.moving)return;this.finishing=true;this.close();this.refresh();this.modal('Saving your meal','<p>Please keep this page open while your plate is saved.</p>',[],true);try{await wait(450);if(this.research.config.screenshotsEnabled)await this.capture(false);this.research.setPortions(this.portions);await this.native.call('complete');this.research.complete();this.finished=true;this.finishing=false;this.showCompletion();}catch(error){this.finishing=false;this.modal('Your meal is still here',`<p>We could not finish saving the plate photograph. ${escapeHTML(error.message)}</p>`,[['Return to review',()=>{this.close();this.review();}],['Try again',()=>this.finish(),true]]);}}
  showCompletion(){const actions=[['Download your choices',()=>download(JSON.stringify(this.research.data,null,2),`buffet-${this.research.data.sessionId}.json`)]];if(this.research.localOnly){actions.push(['Download meal and photographs',()=>this.research.recovery()],['Start a new meal',()=>{const url=new URL(location.href);url.searchParams.delete('sessionId');url.searchParams.set('SESSION_ID',crypto.randomUUID());location.assign(url.href);},true]);}else actions.push(['Retry saving',()=>this.research.flush()]);this.modal('Thank you for choosing a meal',this.mealHTML()+`<p id="completion-state">${escapeHTML($('save-state').textContent)}</p><p>${this.research.localOnly?'Your meal is saved only in this browser. Download it to keep a copy; it has not been sent to a researcher.':this.research.parentOrigin?'Once your survey receives your choices, use its Next button to continue.':'Your choices are recorded for this dining session.'}</p><small>Session ${escapeHTML(this.research.data.sessionId)}</small>`,actions,true);}
  initAudio(){if(!this.research.config.soundEnabled||this.audio)return;this.audio=new AudioContext();this.gain=this.audio.createGain();this.gain.gain.value=this.soundOn?.12:0;this.gain.connect(this.audio.destination);const n=this.audio.sampleRate*6,buffer=this.audio.createBuffer(1,n,this.audio.sampleRate),data=buffer.getChannelData(0);let last=0;for(let i=0;i<n;i++){last+=(Math.random()*2-1-last)*.025;data[i]=last*.045;}const source=this.audio.createBufferSource();source.buffer=buffer;source.loop=true;source.connect(this.gain);source.start();}
  tone(freq,seconds){if(!this.audio||!this.soundOn)return;this.audio.resume();const o=this.audio.createOscillator(),g=this.audio.createGain(),now=this.audio.currentTime;o.frequency.value=freq;g.gain.setValueAtTime(.3,now);g.gain.exponentialRampToValueAtTime(.001,now+seconds);o.connect(g);g.connect(this.gain);o.start();o.stop(now+seconds);}
  bind(){
    $('previous').onclick=()=>this.navigate(this.station-1);$('next').onclick=()=>this.navigate(this.station+1);$('add').onclick=()=>this.add();$('view').onclick=()=>this.togglePlate();$('undo').onclick=()=>this.remove(this.portions.at(-1));$('remove').onclick=()=>this.remove(this.selected);$('photo').onclick=()=>this.capture().catch(e=>this.toast(e.message));$('review').onclick=()=>this.review();$('menu').onclick=()=>this.menu();$('help').onclick=()=>this.help();$('details').onclick=()=>this.details();$('recovery').onclick=()=>this.research.recovery();$('close-dialog').onclick=()=>this.close();
    this.dialog.addEventListener('cancel',event=>{if(this.locked)event.preventDefault();});this.dialog.addEventListener('close',()=>this.refresh());
    $('sound').onclick=()=>{if(!this.research.config.soundEnabled)return;this.initAudio();this.soundOn=!this.soundOn;this.gain.gain.value=this.soundOn?.12:0;this.research.record(this.soundOn?'sound_unmuted':'sound_muted');this.refresh();};
    $('fullscreen').onclick=async()=>{try{if(document.fullscreenElement)await document.exitFullscreen();else await document.documentElement.requestFullscreen();}catch{this.toast('Full screen is not available in this browser.');}};
    window.addEventListener('keydown',e=>{if(this.busy||e.repeat||e.altKey||e.ctrlKey||e.metaKey||e.target.matches('input,textarea,select')||(e.key===' '&&e.target.closest('button')))return;switch(e.key){case'ArrowLeft':e.preventDefault();this.navigate(this.station-1);break;case'ArrowRight':e.preventDefault();this.navigate(this.station+1);break;case' ':e.preventDefault();if(!this.plateView)this.add();break;case'p':case'P':this.togglePlate();break;}},true);
    this.canvas.addEventListener('pointerdown',event=>{
      if(this.busy||event.button!==0)return;const press={id:event.pointerId,x:event.clientX,y:event.clientY,drag:false};this.press=press;press.hit=this.native.call('pick',this.point(event)).then(async meta=>{if(this.plateView&&meta.portion){this.selected=this.portions.find(p=>p.portionId===meta.portion);await this.native.call('select',{portionId:meta.portion});this.refresh();}return meta;});this.canvas.setPointerCapture(event.pointerId);
    },true);
    this.canvas.addEventListener('pointermove',event=>{if(!this.press||this.press.id!==event.pointerId)return;if(Math.hypot(event.clientX-this.press.x,event.clientY-this.press.y)>9)this.press.drag=true;if(this.press.drag)this.canvas.style.cursor='grabbing';},true);
    this.canvas.addEventListener('pointerup',async event=>{
      const press=this.press;this.press=null;this.canvas.style.cursor='';if(!press||press.id!==event.pointerId||this.busy)return;const at=this.point(event),meta=await press.hit;if(this.busy)return;
      if(meta.station===this.station&&!this.plateView){const valid=press.drag?(await this.native.call('drop',at)).onPlate:(await this.native.call('pick',at)).station===this.station;if(valid&&!this.busy)await this.add();}
      else if(meta.portion&&this.plateView&&press.drag){this.mutating=true;this.refresh();try{const result=await this.native.call('drop',{...at,portionId:meta.portion});if(result.moved){const portion=this.portions.find(p=>p.portionId===result.moved);this.research.setPortions(this.portions);this.research.record('portion_moved',portion.foodId,portion.portionId);}}finally{this.mutating=false;this.refresh();}}
    },true);
    this.canvas.addEventListener('pointercancel',()=>{this.press=null;this.canvas.style.cursor='';},true);
  }
}

try{
  const research=await ResearchSession.open(text=>{$('save-state').textContent=text;if($('completion-state'))$('completion-state').textContent=text;});
  const {foods:all}=await(await fetch('assets/menu.json')).json();const foods=research.config.foodOrder.length?research.config.foodOrder.map(id=>all.find(f=>f.id===id)):all;if(foods.some(f=>!f)||!foods.length)throw new Error('This study menu contains an unknown food.');
  game=new BuffetGame(research,foods);await game.init();
}catch(error){console.error(error);$('loading').hidden=false;$('loading').innerHTML=`<h1>We couldn’t set the table</h1><p>${escapeHTML(error.message)}</p><button class="primary" onclick="location.reload()">Try again</button>`;}
