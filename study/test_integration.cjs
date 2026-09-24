/* Run: node study/test_integration.cjs. Exercises the actual Qualtrics receiver. */
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
let ready, handler, unload, enabled = false, fields = {}, messages = [];
const contentWindow = { postMessage(message, origin) { messages.push({message, origin}); } };
const frame = { style: {}, contentWindow };
const status = {};
const context = {
  URL, URLSearchParams, Number, Date, JSON, Object, String,
  window: {location:{origin:'https://survey.example.edu',search:'?PROLIFIC_PID=test-pid&SESSION_ID=test-submission'},addEventListener(_,fn){handler=fn;},removeEventListener(_,fn){assert.equal(fn,handler);}},
  document: {createElement(){return frame;}},
  Qualtrics: {SurveyEngine:{addOnReady(fn){ready=fn;},addOnUnload(fn){unload=fn;},getEmbeddedData(name){return fields[name];},setEmbeddedData(name,value){fields[name]=value;}}}
};
vm.createContext(context);
vm.runInContext(fs.readFileSync('study/qualtrics-question.js','utf8'), context);
ready.call({getQuestionContainer(){return {querySelector(selector){return selector==='#buffet-frame-host'?{appendChild(){}}:status;}};},disableNextButton(){enabled=false;},enableNextButton(){enabled=true;}});
const session = {sessionId:'session-test',revision:3,completed:true,elapsedSeconds:21.125,condition:'default',participantId:'test-pid',sourceSessionId:'test-submission',studyId:'study',portions:[{portionId:'one',foodId:'rice',plateId:'main'},{portionId:'two',foodId:'rice',plateId:'main'},{portionId:'three',foodId:'fruit',plateId:'dessert'}],events:[{eventType:'screenshot_saved',portionId:'image1'}]};
const event = {origin:'https://buffet.example.edu',source:contentWindow,data:{type:'buffet:complete',schemaVersion:1,session}};
handler({...event,origin:'https://attacker.invalid'}); assert.equal(enabled,false);
handler({...event,source:{}}); assert.equal(enabled,false);
handler({...event,data:{...event.data,session:{...session,participantId:'someone-else'}}}); assert.equal(enabled,false);
handler({...event,data:{...event.data,session:{...session,portions:[session.portions[0],session.portions[0]]}}}); assert.equal(enabled,false);
handler(event);
assert.equal(enabled,true); assert.equal(fields.buffet_total_portions,'3');
assert.deepEqual(JSON.parse(fields.buffet_counts_json),{rice:2,fruit:1});
assert.deepEqual(JSON.parse(fields.buffet_plate_counts_json),{'main:rice':2,'dessert:fruit':1});
assert.equal(fields.buffet_elapsed_seconds,'21.125'); assert.equal(fields.buffet_screenshot_count,'1');
assert.equal(fields.SESSION_ID,'test-submission'); assert.equal(messages[0].origin,'https://buffet.example.edu');
assert.equal(messages[0].message.sessionId,session.sessionId); assert.equal(messages[0].message.revision,3);
handler(event); assert.equal(fields.buffet_total_portions,'3');
unload();
console.log('PASS: strict origin/window, participant identity, duplicate portions, counts by plate, elapsed time, screenshot count, idempotent ACK, cleanup.');
