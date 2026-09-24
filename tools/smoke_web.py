from pathlib import Path
import json,time
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1]
with sync_playwright() as pw:
    browser=pw.chromium.launch(channel='chrome',headless=True,args=['--no-proxy-server'])
    page=browser.new_page(viewport={'width':1440,'height':1000})
    logs=[]
    page.on('console',lambda message: logs.append([message.type,message.text]) if message.type in ['error','warning'] else None)
    page.on('pageerror',lambda error: logs.append(['pageerror',str(error)]))
    try:
        page.goto('http://127.0.0.1:8772/?SESSION_ID=smoke-'+str(time.time()))
        page.wait_for_function('window.buffet',timeout=120000)
        print(json.dumps(page.evaluate('window.buffet.snapshot()'),indent=2),flush=True)
        page.screenshot(path=str(ROOT/'artifacts/welcome.png'))
        page.get_by_role('button',name='Explore the buffet').click()
        page.wait_for_function('!window.buffet.snapshot().moving',timeout=30000)
        page.screenshot(path=str(ROOT/'artifacts/station.png'))
        start=time.monotonic();page.locator('#add').click()
        page.wait_for_function('window.buffet.snapshot().portions.length===1 && !window.buffet.snapshot().moving',timeout=30000)
        print('Serve seconds:',time.monotonic()-start,flush=True)
        page.wait_for_timeout(700)
        page.locator('#view').click();page.wait_for_function('!window.buffet.snapshot().moving')
        page.screenshot(path=str(ROOT/'artifacts/plate.png'))
        print('Final state:',json.dumps(page.evaluate('window.buffet.snapshot()'),indent=2),flush=True)
        page.locator('#photo').click();page.get_by_role('heading',name='Your plate photograph').wait_for(timeout=60000)
        with page.expect_download() as download: page.get_by_role('button',name='Download PNG').click()
        download.value.save_as(str(ROOT/'artifacts/photograph.png'))
    finally:
        (ROOT/'artifacts/browser-errors.json').write_text(json.dumps(logs,indent=2))
        page.screenshot(path=str(ROOT/'artifacts/last.png'))
        print('Browser diagnostics:',json.dumps(logs),flush=True)
        browser.close()
