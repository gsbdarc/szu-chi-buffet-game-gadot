/* Paste into this question's Qualtrics JavaScript editor. Replace BUFFET_ORIGIN.
   Define the listed Embedded Data fields BEFORE this question in Survey Flow.
   Classic JFE SurveyEngine API; verify with your institution's survey layout. */
Qualtrics.SurveyEngine.addOnReady(function () {
  'use strict';
  var question = this;
  var BUFFET_ORIGIN = 'https://buffet.example.edu';
  var container = question.getQuestionContainer();
  var host = container.querySelector('#buffet-frame-host');
  var status = container.querySelector('#buffet-survey-status');
  var frame = document.createElement('iframe');
  var url = new URL('/', BUFFET_ORIGIN);
  var incoming = new URLSearchParams(window.location.search);
  function embedded(name) {
    return String(Qualtrics.SurveyEngine.getEmbeddedData(name) || incoming.get(name) || '');
  }
  ['PROLIFIC_PID', 'STUDY_ID', 'SESSION_ID'].forEach(function (key) {
    var value = embedded(key);
    if (value) url.searchParams.set(key, value);
  });
  url.searchParams.set('condition', embedded('buffet_condition') || 'default');
  url.searchParams.set('parentOrigin', window.location.origin);
  frame.src = url.toString();
  frame.title = 'Interactive dining hall buffet';
  frame.allow = 'fullscreen';
  frame.style.cssText = 'width:100%;height:min(82vh,900px);min-height:460px;border:1px solid #d8dace;border-radius:8px;';
  question.disableNextButton();
  var acceptedSession = '';
  function receive(event) {
    if (event.origin !== BUFFET_ORIGIN || event.source !== frame.contentWindow) return;
    var message = event.data;
    if (!message || message.type !== 'buffet:complete' || message.schemaVersion !== 1) return;
    var s = message.session;
    if (!s || s.completed !== true || typeof s.sessionId !== 'string' || !/^[A-Za-z0-9_-]{1,128}$/.test(s.sessionId)
        || !Number.isInteger(s.revision) || s.revision < 1 || !Array.isArray(s.portions) || s.portions.length > 200
        || typeof s.elapsedSeconds !== 'number' || !Number.isFinite(s.elapsedSeconds) || s.elapsedSeconds < 0) return;
    if (acceptedSession && acceptedSession !== s.sessionId) return;
    if (embedded('PROLIFIC_PID') && s.participantId !== embedded('PROLIFIC_PID')) return;
    if (embedded('SESSION_ID') && s.sourceSessionId !== embedded('SESSION_ID')) return;
    var counts = Object.create(null), plateCounts = Object.create(null), seen = Object.create(null);
    for (var index = 0; index < s.portions.length; index++) {
      var portion = s.portions[index];
      if (!portion || !/^[A-Za-z0-9_-]{1,128}$/.test(portion.foodId) || !/^[A-Za-z0-9_-]{1,128}$/.test(portion.plateId)
          || !/^[A-Za-z0-9_-]{1,128}$/.test(portion.portionId) || seen[portion.portionId]) return;
      seen[portion.portionId] = true;
      counts[portion.foodId] = (counts[portion.foodId] || 0) + 1;
      var key = portion.plateId + ':' + portion.foodId;
      plateCounts[key] = (plateCounts[key] || 0) + 1;
    }
    var compact = {schemaVersion:1,sessionId:s.sessionId,revision:s.revision,condition:s.condition,participantId:s.participantId,
      studyId:s.studyId,sourceSessionId:s.sourceSessionId,elapsedSeconds:s.elapsedSeconds,startedAt:s.startedAt,completedAt:s.completedAt,portions:s.portions};
    var fields = {
      buffet_session_id: s.sessionId, buffet_revision: String(s.revision), buffet_condition: s.condition,
      buffet_completed: '1', buffet_elapsed_seconds: s.elapsedSeconds.toFixed(3), buffet_total_portions: String(s.portions.length),
      buffet_counts_json: JSON.stringify(counts), buffet_plate_counts_json: JSON.stringify(plateCounts),
      buffet_payload_json: JSON.stringify(compact), buffet_screenshot_count: String((s.events || []).filter(function(e){ return e.eventType === 'screenshot_saved' || e.eventType === 'screenshot_recovered'; }).map(function(e){ return e.portionId; }).filter(function(id,i,a){return a.indexOf(id) === i;}).length),
      buffet_received_at: new Date().toISOString(), PROLIFIC_PID: s.participantId || '', STUDY_ID: s.studyId || '', SESSION_ID: s.sourceSessionId || ''
    };
    ["chicken_parmesan", "pizza", "burger", "salmon", "beef_skewer", "rice", "pasta", "broccoli", "roasted_carrots", "mashed_potatoes", "kale_salad", "bread_roll", "fruit_salad", "chocolate_cake", "cookie"].forEach(function(id) { fields["buffet_count_" + id] = String(counts[id] || 0); });
    try {
      Object.keys(fields).forEach(function (name) { Qualtrics.SurveyEngine.setEmbeddedData(name, fields[name]); });
      acceptedSession = s.sessionId;
      status.textContent = 'Your choices have been received. Select Next to save this survey page and continue.';
      question.enableNextButton();
      frame.contentWindow.postMessage({ type: 'buffet:ack', sessionId: s.sessionId, revision: s.revision }, BUFFET_ORIGIN);
    } catch (_) { status.textContent = 'The survey could not receive your data yet. Keep this page open and contact the researcher if the problem continues.'; }
  }
  window.addEventListener('message', receive);
  host.appendChild(frame);
  Qualtrics.SurveyEngine.addOnUnload(function () { window.removeEventListener('message', receive); });
});
