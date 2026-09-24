"""Verify participant actions cannot race a pending plate capture."""
from pathlib import Path
import json,time
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1]
with sync_playwright() as pw:
    browser=pw.chromium.launch(channel='chrome',headless=True,args=['--no-proxy-server'])
    page=browser.new_page(viewport={'width':1280,'height':800})
    page.goto('http://127.0.0.1:8770/?SESSION_ID=QA-capture-'+str(time.time_ns()))
    page.wait_for_function('window.buffet',timeout=90000)
    page.get_by_role('button',name='Explore the buffet').click();page.wait_for_function('!window.buffet.snapshot().moving')
    page.locator('#add').click();page.wait_for_timeout(500)
    pending=[]
    page.route('**/api/screenshots/**',lambda route:pending.append(route))
    page.locator('#photo').click()
    for _ in range(30):
        if pending:break
        page.wait_for_timeout(100)
    assert pending,'Capture did not reach the image API'
    for selector in ('#review','#add','#view','#next','#undo'):assert page.locator(selector).is_disabled(),selector
    assert len(page.evaluate('window.buffet.snapshot().portions'))==1
    pending[0].continue_()
    page.unroute('**/api/screenshots/**')
    page.get_by_role('heading',name='Your plate photograph').wait_for(timeout=30000)
    page.get_by_role('button',name='Back',exact=True).click()
    page.locator('#review').click();page.get_by_role('button',name='Finish meal',exact=True).click()
    page.wait_for_function('window.buffet.snapshot().finished && window.buffet.snapshot().saved',timeout=60000)
    result={'inputFrozenDuringCapture':True,'completionSaved':True,'portions':1}
    (ROOT/'docs/evidence/capture-guard.json').write_text(json.dumps(result,indent=2))
    browser.close();print('PASS capture guard and completion')
