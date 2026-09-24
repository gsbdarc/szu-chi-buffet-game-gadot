"""Test standalone gameplay on a project URL, including durable local downloads."""
import argparse
import functools
import json
import tempfile
import threading
import uuid
from contextlib import contextmanager
from datetime import datetime, timezone
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlsplit

from playwright.sync_api import sync_playwright
import shutil

def build(output):
    shutil.copytree(ROOT / '_site', output)
    return output

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'artifacts/pages'
OUT.mkdir(parents=True, exist_ok=True)


class QuietHandler(SimpleHTTPRequestHandler):
    def log_message(self, *args):
        pass


@contextmanager
def site(url):
    if url:
        yield url.rstrip('/') + '/'
        return
    with tempfile.TemporaryDirectory(prefix='buffet-pages-') as temporary:
        build(Path(temporary) / 'szu-chi-buffet-game-gadot')
        handler = functools.partial(QuietHandler, directory=temporary)
        server = ThreadingHTTPServer(('127.0.0.1', 0), handler)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            yield f'http://127.0.0.1:{server.server_port}/szu-chi-buffet-game-gadot/'
        finally:
            server.shutdown()
            server.server_close()
            thread.join()


def ready(page):
    page.wait_for_function('window.buffet && !window.buffet.snapshot().moving', timeout=120000)


def saved(page):
    page.wait_for_function('window.buffet.snapshot().saved', timeout=30000)
    assert page.locator('#save-state').inner_text() == 'Saved on this device'


def snapshot(page):
    return page.evaluate('window.buffet.snapshot()')


def check(base):
    errors, api_calls, failed, models = [], [], [], set()
    report = {'testedAt': datetime.now(timezone.utc).isoformat(), 'url': base}
    with sync_playwright() as pw:
        browser = pw.chromium.launch(channel='chrome', headless=True, args=['--no-proxy-server'])
        context = browser.new_context(viewport={'width': 1440, 'height': 1000}, accept_downloads=True)

        def observe(page):
            page.on('pageerror', lambda error: errors.append(str(error)))
            page.on('request', lambda request: api_calls.append(request.url) if '/api/' in request.url else None)
            page.on('response', lambda response: failed.append([response.status, response.url]) if response.status >= 400 else None)
            page.on('response', lambda response: models.add(urlsplit(response.url).path) if response.url.endswith(('.wasm','.pck')) and response.ok else None)

        page = context.new_page()
        observe(page)
        page.goto(base + '?SESSION_ID=pages-test-' + uuid.uuid4().hex)
        ready(page)
        assert 'saved only in this browser' in page.locator('#dialog-body').inner_text()
        assert len(models) == 2, f'Expected Godot WASM and PCK, loaded {models}'
        assert snapshot(page)['models'] == 15
        assert snapshot(page)['engine'].startswith('Godot 4.7.2')
        assert page.evaluate("typeof BABYLON") == 'undefined'
        assert snapshot(page)['session']['storageMode'] == 'local'
        page.get_by_role('button', name='Explore the buffet').click()
        ready(page)
        page.locator('#add').click()
        page.wait_for_timeout(500)
        page.locator('#next').click()
        ready(page)
        page.locator('#add').click()
        page.wait_for_timeout(500)
        saved(page)
        before = snapshot(page)['session']
        assert len(before['portions']) == 2
        page.reload()
        ready(page)
        page.get_by_role('button', name='Continue your plate').click()
        ready(page)
        after = snapshot(page)['session']
        assert after['sessionId'] == before['sessionId']
        assert after['portions'] == before['portions']
        page.locator('#view').click()
        ready(page)
        page.screenshot(path=str(OUT / 'plate.png'))
        page.locator('#photo').click()
        page.get_by_role('heading', name='Your plate photograph').wait_for(timeout=60000)
        with page.expect_download() as downloaded:
            page.get_by_role('button', name='Download PNG').click()
        downloaded.value.save_as(str(OUT / 'photograph.png'))
        assert (OUT / 'photograph.png').read_bytes().startswith(b'\x89PNG\r\n\x1a\n')
        page.get_by_role('button', name='Back', exact=True).click()
        page.locator('#review').click()
        page.get_by_role('button', name='Finish meal', exact=True).click()
        page.get_by_role('heading', name='Thank you for choosing a meal').wait_for(timeout=60000)
        saved(page)
        assert snapshot(page)['session']['completed']
        assert 'has not been sent to a researcher' in page.locator('#dialog-body').inner_text()
        completed = snapshot(page)['session']
        page.reload()
        ready(page)
        saved(page)
        assert snapshot(page)['session'] == completed
        with page.expect_download() as downloaded:
            page.get_by_role('button', name='Download meal and photographs').click()
        downloaded.value.save_as(str(OUT / 'meal.json'))
        recovery = json.loads((OUT / 'meal.json').read_text())
        assert recovery['session'] == completed
        assert len(recovery['savedImages']) == 2
        assert all(item['data'].startswith('data:image/png;base64,') for item in recovery['savedImages'])
        with page.expect_download() as downloaded:
            page.get_by_role('button', name='Download your choices', exact=True).click()
        downloaded.value.save_as(str(OUT / 'choices.json'))
        assert json.loads((OUT / 'choices.json').read_text()) == completed
        page.screenshot(path=str(OUT / 'complete.png'))
        page.get_by_role('button', name='Start a new meal').click()
        page.wait_for_url(lambda url: 'pages-test-' not in urlsplit(url).query)
        ready(page)
        assert not snapshot(page)['session']['completed']
        assert snapshot(page)['session']['sessionId'] != completed['sessionId']
        assert not snapshot(page)['portions']
        report.update(foodsLoaded=15, godotRuntimeLoaded=True, portionsRestored=2, screenshotsRestored=2,
                      completionRestored=True, downloads=True, newMeal=True)

        mobile_context = browser.new_context(viewport={'width': 390, 'height': 844}, is_mobile=True, has_touch=True)
        mobile = mobile_context.new_page()
        observe(mobile)
        mobile.goto(base + '?condition=no_screenshot&SESSION_ID=pages-mobile-' + uuid.uuid4().hex)
        ready(mobile)
        mobile.get_by_role('button', name='Explore the buffet').tap()
        ready(mobile)
        assert mobile.locator('#photo').is_hidden()
        mobile.locator('#add').tap()
        mobile.wait_for_timeout(500)
        saved(mobile)
        assert len(snapshot(mobile)['portions']) == 1
        mobile.screenshot(path=str(OUT / 'mobile.png'))
        mobile.locator('#review').tap()
        mobile.get_by_role('button', name='Finish meal', exact=True).tap()
        mobile.get_by_role('heading', name='Thank you for choosing a meal').wait_for(timeout=30000)
        saved(mobile)
        report.update(mobile=True, noScreenshotCondition=True)
        browser.close()
    assert not api_calls, api_calls
    assert not failed, failed
    assert not errors, errors
    report.update(apiCalls=api_calls, failedRequests=failed, errors=errors)
    (OUT / 'report.json').write_text(json.dumps(report, indent=2))
    print('PASS standalone Pages: 15 models, local meals/images, downloads, refresh, replay, mobile; no API calls.')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--url', help='Test a deployed site instead of a temporary static server')
    args = parser.parse_args()
    with site(args.url) as base:
        check(base)
