"""Targeted final checks: fresh previews, keyboard, touch drag, empty meals and capacity."""
import json,time
from pathlib import Path
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'artifacts/final';OUT.mkdir(exist_ok=True)
result={}
with sync_playwright() as pw:
    browser=pw.chromium.launch(channel='chrome',headless=True,args=['--no-proxy-server'])
    context=browser.new_context(viewport={'width':1440,'height':1000})
    page=context.new_page();errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
    page.goto('http://127.0.0.1:8770/researcher');page.locator('#preview-link').wait_for()
    preview=page.locator('#preview-link').get_attribute('href');assert 'SESSION_ID=preview-' in preview
    page.goto(preview);page.wait_for_function('window.buffet',timeout=90000)
    page.screenshot(path=str(OUT/'welcome.png'));page.get_by_role('button',name='Explore the buffet').click()
    assert page.evaluate('window.buffet.snapshot().moving')
    assert page.locator('#add').is_disabled()
    page.screenshot(path=str(OUT/'overview.png'));page.wait_for_function('!window.buffet.snapshot().moving')
    page.locator('#next').click();page.wait_for_function('!window.buffet.snapshot().moving')
    page.keyboard.press('ArrowRight');page.wait_for_function('!window.buffet.snapshot().moving')
    assert page.evaluate('window.buffet.snapshot().station')==2
    page.locator('#scene').focus();page.keyboard.press('Space');page.wait_for_timeout(500)
    assert len(page.evaluate('window.buffet.snapshot().portions'))==1
    for i in range(39):page.locator('#add').click()
    page.wait_for_timeout(700);state=page.evaluate('window.buffet.snapshot()');assert len(state['portions'])==40
    page.locator('#add').click();assert len(page.evaluate('window.buffet.snapshot().portions'))==40
    assert max(p['extent'] for p in state['portions'])<=.14301
    page.locator('#view').click();page.wait_for_function('!window.buffet.snapshot().moving');page.screenshot(path=str(OUT/'capacity-40.png'))
    page.locator('#photo').click();page.get_by_role('heading',name='Your plate photograph').wait_for(timeout=60000)
    with page.expect_download() as dl:page.get_by_role('button',name='Download PNG').click()
    dl.value.save_as(str(OUT/'capacity-photograph.png'));page.get_by_role('button',name='Back',exact=True).click()
    page.set_viewport_size({'width':390,'height':844});page.wait_for_timeout(500);page.screenshot(path=str(OUT/'capacity-portrait.png'))
    result['capacity']={'portions':40,'withinPlate':True};result['keyboard']=True;result['overviewInputGuard']=True;result['freshPreview']=True
    mobile=browser.new_context(viewport={'width':390,'height':844},is_mobile=True,has_touch=True,device_scale_factor=2)
    touch=mobile.new_page();touch.goto('http://127.0.0.1:8770/?SESSION_ID=QA-touch-'+str(time.time_ns()));touch.wait_for_function('window.buffet',timeout=90000)
    touch.get_by_role('button',name='Explore the buffet').tap();touch.wait_for_function('!window.buffet.snapshot().moving')
    a=touch.evaluate("window.buffet.point('dish')");b=touch.evaluate("window.buffet.point('plate')")
    assert 0 < a['x'] < 390 and 0 < b['x'] < 390, 'Projected targets must fit the mobile viewport'
    cdp=mobile.new_cdp_session(touch)
    cdp.send('Input.dispatchTouchEvent',{'type':'touchStart','touchPoints':[a]})
    for i in range(1,13):cdp.send('Input.dispatchTouchEvent',{'type':'touchMove','touchPoints':[{'x':a['x']+(b['x']-a['x'])*i/12,'y':a['y']+(b['y']-a['y'])*i/12}]})
    cdp.send('Input.dispatchTouchEvent',{'type':'touchEnd','touchPoints':[]})
    touch.wait_for_function('window.buffet.snapshot().portions.length === 1',timeout=10000)
    assert len(touch.evaluate('window.buffet.snapshot().portions'))==1
    touch.screenshot(path=str(OUT/'touch-drag.png'));result['realTouchDrag']=True
    # Render the final converted textures and verify a valid empty selection completion.
    empty=browser.new_page(viewport={'width':1200,'height':800});empty.goto('http://127.0.0.1:8770/?condition=no_screenshot&SESSION_ID=QA-empty-'+str(time.time_ns()));empty.wait_for_function('window.buffet',timeout=90000)
    empty.get_by_role('button',name='Explore the buffet').click();empty.wait_for_function('!window.buffet.snapshot().moving');empty.locator('#review').click();empty.get_by_role('heading',name='Your meal, your choice').wait_for();assert 'plate is empty' in empty.locator('#dialog-body').inner_text()
    empty.get_by_role('button',name='Finish meal',exact=True).click();empty.wait_for_function('window.buffet.snapshot().finished && window.buffet.snapshot().saved')
    result['emptyMeal']=True;result['errors']=errors;assert not errors
    browser.close()
(OUT/'report.json').write_text(json.dumps(result,indent=2));print(json.dumps(result,indent=2))
