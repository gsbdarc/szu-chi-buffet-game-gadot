"""Focused WebKit and Firefox checks of the actual game and plate capture."""
from pathlib import Path
import json, time
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'artifacts/browsers';OUT.mkdir(exist_ok=True)
report={}
with sync_playwright() as pw:
    for engine in ('webkit','firefox'):
        browser=getattr(pw,engine).launch(headless=True)
        page=browser.new_page(viewport={'width':1280,'height':800})
        errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
        page.goto('http://127.0.0.1:8770/?SESSION_ID=QA-'+engine+'-'+str(time.time_ns()))
        page.wait_for_function('window.buffet',timeout=90000)
        page.get_by_role('button',name='Explore the buffet').click()
        page.wait_for_function('!window.buffet.snapshot().moving',timeout=20000)
        page.locator('#add').click();page.wait_for_timeout(600)
        page.locator('#next').click();page.wait_for_function('!window.buffet.snapshot().moving')
        page.locator('#add').click();page.wait_for_timeout(600)
        page.locator('#view').click();page.wait_for_function('!window.buffet.snapshot().moving')
        page.screenshot(path=str(OUT/(engine+'-plate.png')))
        page.locator('#photo').click();page.get_by_role('heading',name='Your plate photograph').wait_for(timeout=60000)
        image=page.locator('.screenshot-preview');assert image.evaluate('(i)=>i.naturalWidth')==1024
        page.get_by_role('button',name='Back',exact=True).click()
        page.locator('#review').click();page.get_by_role('button',name='Finish meal',exact=True).click()
        page.get_by_role('heading',name='Thank you for choosing a meal').wait_for(timeout=60000)
        page.wait_for_function('window.buffet.snapshot().saved',timeout=30000)
        state=page.evaluate('window.buffet.snapshot()');assert state['finished'] and len(state['portions'])==2 and not errors
        report[engine]={'completed':True,'portions':2,'screenshot':[1024,1024],'fps':state['fps'],'errors':errors}
        page.reload();page.wait_for_function('window.buffet',timeout=90000);assert page.evaluate('window.buffet.snapshot().finished')
        report[engine]['completedRefreshPreserved']=True
        browser.close();print('PASS',engine,flush=True)
        (OUT/'report.json').write_text(json.dumps(report,indent=2))
