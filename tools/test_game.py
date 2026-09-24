"""Black-box participant, database, image and iframe checks in real Chromium.
Uses a disposable server/database; no production participant records are touched.
Run .venv/bin/python tools/test_game.py
"""
import json, os, subprocess, sys, tempfile, time, urllib.request
from pathlib import Path
from collections import Counter
from playwright.sync_api import sync_playwright

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'artifacts/verification';OUT.mkdir(exist_ok=True)
BASE='http://127.0.0.1:8767'
REPORT={'cases':{},'errors':[]}

def snapshot(page): return page.evaluate('window.buffet.snapshot()')
def ready(page): page.wait_for_function('window.buffet && !window.buffet.snapshot().moving',timeout=90000)
def saved(page): page.wait_for_function('window.buffet.snapshot().saved',timeout=45000)
def start(page,url='/?PROLIFIC_PID=QA-desktop'):
    page.goto(BASE+url);ready(page)
    page.get_by_role('button',name='Explore the buffet').click();ready(page)
def add(page): page.locator('#add').click();ready(page);page.wait_for_timeout(480)
def next_dish(page): page.locator('#next').click();ready(page)
def shot(page,name):page.screenshot(path=str(OUT/(name+'.png')))
def exports(): return json.load(urllib.request.build_opener(urllib.request.ProxyHandler({})).open(BASE+'/api/export.json'))['sessions']
def check_errors(page):
    page.on('pageerror',lambda e:REPORT['errors'].append(str(e)))
    page.on('console',lambda m:REPORT['errors'].append(m.text) if m.type=='error' and m.text.startswith('Godot:') else None)
def click3d(page,name,index=0):
    p=page.evaluate('([n,i])=>window.buffet.point(n,i)',[name,index]);page.mouse.click(p['x'],p['y'])

with tempfile.TemporaryDirectory(prefix='buffet-godot-test-') as tmp:
    temp=Path(tmp);conditions=json.loads((ROOT/'study/conditions.json').read_text())
    for config in conditions.values():config['introSeconds']=0
    conditions['restricted']=dict(conditions['default'],allowRemoval=False,maxPortions=2,foodOrder=['burger','rice'],screenshotsEnabled=False)
    (temp/'conditions.json').write_text(json.dumps(conditions))
    log=(OUT/'server.log').open('w')
    server=subprocess.Popen([sys.executable,str(ROOT/'server/buffet_server.py'),'--port','8767','--db',str(temp/'test.sqlite'),'--conditions',str(temp/'conditions.json')],stdout=log,stderr=log)
    try:
        time.sleep(.6)
        with sync_playwright() as pw:
            browser=pw.chromium.launch(channel='chrome',headless=True,args=['--no-proxy-server'])
            context=browser.new_context(viewport={'width':1440,'height':1000},accept_downloads=True)
            page=context.new_page();check_errors(page)
            start(page);shot(page,'desktop-station')
            # Single click and drag from the current serving tray, with one event per portion.
            click3d(page,'dish');page.wait_for_timeout(500)
            assert len(snapshot(page)['portions'])==1,'Tray click did not add exactly one portion'
            a=page.evaluate("window.buffet.point('dish')");b=page.evaluate("window.buffet.point('plate')")
            page.mouse.move(a['x'],a['y']);page.mouse.down();page.mouse.move(b['x'],b['y'],steps=12);page.mouse.up();page.wait_for_timeout(500)
            assert len(snapshot(page)['portions'])==2,'Drag serving failed'
            # Dropping outside the plate is cancelled.
            page.mouse.move(a['x'],a['y']);page.mouse.down();page.mouse.move(700,110,steps=8);page.mouse.up()
            assert len(snapshot(page)['portions'])==2
            for i in range(1,15):
                next_dish(page);add(page)
                assert snapshot(page)['station']==i
            state=snapshot(page);assert len(state['portions'])==16
            assert len({p['food'] for p in state['portions']})==15
            assert max(p['extent'] for p in state['portions'])<=.14301
            assert len({p['id'] for p in state['portions']})==16
            shot(page,'all-foods-served')
            page.locator('#view').click();ready(page);shot(page,'desktop-plate')
            # Select and move a visible top portion, then remove it independently.
            click3d(page,'portion',15)
            page.wait_for_function('window.buffet.snapshot().selected',timeout=5000)
            state=snapshot(page);assert state['selected'],'Could not select an individual portion'
            assert state['selected']==state['portions'][15]['id'],'Picking selected a different portion from the visible cookie'
            selected=state['selected'];p=page.evaluate("window.buffet.point('portion',15)");q=page.evaluate("window.buffet.point('plate')")
            page.mouse.move(p['x'],p['y']);page.mouse.down();page.mouse.move(q['x']+35,q['y']+25,steps=10);page.mouse.up()
            page.wait_for_function("window.buffet.snapshot().session.events.some(e=>e.eventType==='portion_moved')")
            assert any(e['eventType']=='portion_moved' for e in snapshot(page)['session']['events'])
            page.locator('#remove').click();ready(page);assert len(snapshot(page)['portions'])==15
            assert selected not in [p['id'] for p in snapshot(page)['portions']]
            # Refresh recovery preserves IDs, counts and positions, with no duplicate additions.
            saved(page);before=snapshot(page)['session'];page.reload();ready(page)
            page.get_by_role('button',name='Continue your plate').click();ready(page)
            after=snapshot(page)['session'];assert after['sessionId']==before['sessionId'];assert after['portions']==before['portions']
            # Menu navigation revisits a previously selected dish.
            page.locator('#menu').click();page.locator('[data-station="4"]').click();ready(page);add(page)
            assert snapshot(page)['session']['portions'][-1]['foodId']=='beef_skewer'
            page.locator('#details').click();assert 'Beef, bell pepper' in page.locator('#dialog-body').inner_text();page.get_by_role('button',name='Back to dish').click()
            # Photograph saved into SQLite and a PNG download is available.
            page.locator('#photo').click();page.get_by_role('heading',name='Your plate photograph').wait_for(timeout=60000);shot(page,'photograph-dialog')
            with page.expect_download() as dl:page.get_by_role('button',name='Download PNG').click()
            dl.value.save_as(str(OUT/'plate.png'));page.get_by_role('button',name='Back',exact=True).click();saved(page)
            page.locator('#review').click();page.get_by_role('button',name='Finish meal',exact=True).click()
            page.get_by_role('heading',name='Thank you for choosing a meal').wait_for(timeout=60000);saved(page)
            final=snapshot(page)['session'];record=next(r for r in exports() if r['sessionId']==final['sessionId']);assert record['completed'];assert record['portions']==final['portions'];assert record['revision']==final['revision'];assert len(record['screenshots'])>=1
            shot(page,'desktop-complete');REPORT['cases']['desktop']={'foods':15,'selected':len(final['portions']),'screenshots':len(record['screenshots']),'refreshPreserved':True,'counts':dict(Counter(p['foodId'] for p in final['portions'])),'fps':snapshot(page)['fps']}
            print('PASS desktop',flush=True)
            # Conditions prevent forbidden actions and enforce configured order/limits.
            restricted=browser.new_page(viewport={'width':1280,'height':800});check_errors(restricted);start(restricted,'/?condition=restricted&PROLIFIC_PID=QA-restricted')
            assert restricted.locator('#undo').is_hidden();assert restricted.locator('#photo').is_hidden();assert restricted.locator('#food-name').inner_text()=='Beef burger'
            add(restricted);add(restricted);add(restricted);assert len(snapshot(restricted)['portions'])==2
            next_dish(restricted);assert restricted.locator('#food-name').inner_text()=='Steamed rice';assert restricted.locator('#next').is_disabled()
            REPORT['cases']['conditions']={'order':['burger','rice'],'limit':2,'removalDisabled':True,'screenshotsDisabled':True};print('PASS conditions',flush=True)
            # Portrait touch and landscape rotation preserve the same session and usable controls.
            mobile_context=browser.new_context(viewport={'width':390,'height':844},is_mobile=True,has_touch=True,device_scale_factor=2)
            mobile=mobile_context.new_page();check_errors(mobile);start(mobile,'/?PROLIFIC_PID=QA-mobile');mobile.locator('#add').tap();mobile.wait_for_timeout(500);shot(mobile,'mobile-portrait')
            before=snapshot(mobile)['session']['sessionId'];mobile.set_viewport_size({'width':844,'height':390});mobile.wait_for_timeout(700);shot(mobile,'mobile-landscape');assert snapshot(mobile)['session']['sessionId']==before
            mobile.locator('#next').tap();ready(mobile);mobile.locator('#add').tap();mobile.wait_for_timeout(500);assert len(snapshot(mobile)['portions'])==2
            mobile.locator('#help').tap();assert mobile.locator('#dialog-title').inner_text()=='Make yourself a plate';mobile.get_by_role('button',name='Back to the buffet').tap()
            mobile.set_viewport_size({'width':390,'height':844});mobile.locator('#view').tap();ready(mobile);shot(mobile,'mobile-plate');REPORT['cases']['mobile']={'portrait':[390,844],'landscape':[844,390],'touch':True,'rotationPreserved':True};print('PASS mobile',flush=True)
            # Completion while offline stays local until all images and the final revision save.
            offline_context=browser.new_context(viewport={'width':1200,'height':800});offline=offline_context.new_page();check_errors(offline);start(offline,'/?PROLIFIC_PID=QA-offline');add(offline);saved(offline)
            offline_context.set_offline(True);next_dish(offline);add(offline);offline.locator('#review').click();offline.get_by_role('button',name='Finish meal',exact=True).click();offline.get_by_role('heading',name='Thank you for choosing a meal').wait_for(timeout=60000)
            assert not snapshot(offline)['saved'];shot(offline,'offline-complete-pending');offline_context.set_offline(False);saved(offline);record=next(r for r in exports() if r['sessionId']==snapshot(offline)['session']['sessionId']);assert record['completed'] and len(record['portions'])==2 and len(record['screenshots'])==1
            REPORT['cases']['offline']={'queuedImageRecovered':True,'completedPortions':2};print('PASS offline',flush=True)
            # Local survey exercises the same origin-checked protocol and participant IDs.
            survey=browser.new_page(viewport={'width':1440,'height':1100});check_errors(survey);survey.goto(BASE+'/study/embed-sandbox.html?PROLIFIC_PID=QA-iframe&SESSION_ID=QA-source&condition=no_screenshot')
            frame=survey.frames[1];ready(frame);frame.get_by_role('button',name='Explore the buffet').click();ready(frame);add(frame);frame.locator('#review').click();frame.get_by_role('button',name='Finish meal',exact=True).click();survey.locator('#continue:not([disabled])').wait_for(timeout=45000)
            payload=json.loads(survey.locator('#output').inner_text());assert payload['participantId']=='QA-iframe';assert payload['sourceSessionId']=='QA-source';assert len(payload['portions'])==1;assert 'survey received' in frame.locator('#save-state').inner_text();shot(survey,'survey-handoff')
            REPORT['cases']['iframe']={'acknowledged':True,'participant':'QA-iframe','sourceSession':'QA-source'};print('PASS iframe',flush=True)
            assert not REPORT['errors'],REPORT['errors']
            (OUT/'export.json').write_text(json.dumps(exports(),indent=2));browser.close()
    finally:
        (OUT/'report.json').write_text(json.dumps(REPORT,indent=2));server.terminate();server.wait(timeout=10);log.close()
print(json.dumps(REPORT,indent=2))
