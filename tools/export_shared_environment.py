"""Transfer the comparison scene once; Babylon is not used by the Godot game.

Run with the comparison project's Playwright Python environment. Requires the
matching 9.11.0 Babylon serializers bundle in artifacts/. Outputs editable GLBs.
"""
import base64
import functools
import shutil
import tempfile
import threading
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT.parent / 'Asta_Babylon/web'


class QuietHandler(SimpleHTTPRequestHandler):
    def log_message(self, *args):
        pass


with tempfile.TemporaryDirectory(prefix='buffet-environment-') as temporary:
    folder = Path(temporary)
    for name, source in [('world.js', SOURCE/'src/world.js'),
                         ('babylon.js', SOURCE/'vendor/babylon.js'),
                         ('serializers.js', ROOT/'artifacts/babylonjs.serializers.min.js'),
                         ('menu.json', SOURCE/'assets/menu.json')]:
        shutil.copy2(source, folder/name)
    (folder/'index.html').write_text('<canvas id="scene" width="1024" height="768"></canvas><script src="babylon.js"></script><script src="serializers.js"></script>')
    server = ThreadingHTTPServer(('127.0.0.1', 0), functools.partial(QuietHandler, directory=temporary))
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        with sync_playwright() as pw:
            browser = pw.chromium.launch(channel='chrome', headless=True, args=['--no-proxy-server'])
            page = browser.new_page()
            page.goto(f'http://127.0.0.1:{server.server_port}')
            assets = page.evaluate('''async () => {
                const B=BABYLON, {buildHall,makePlate,stationX}=await import('./world.js');
                const engine=new B.Engine(document.querySelector('canvas'),true);
                const encode=async(scene,name)=>{
                    const output=await B.GLTF2Export.GLBAsync(scene,name,{exportWithoutWaitingForScene:true});
                    const bytes=new Uint8Array(await output.glTFFiles[name+'.glb'].arrayBuffer());
                    let binary='';for(let i=0;i<bytes.length;i+=16384)binary+=String.fromCharCode(...bytes.subarray(i,i+16384));
                    return btoa(binary);
                };
                const hall=new B.Scene(engine);hall.useRightHandedSystem=true;
                const {label}=buildHall(hall);
                const {foods}=await(await fetch('menu.json')).json();
                const hallData=await encode(hall,'hall');hall.dispose();
                const plate=new B.Scene(engine);plate.useRightHandedSystem=true;makePlate(plate);
                const plateData=await encode(plate,'plate');plate.dispose();engine.dispose();
                return {hall:hallData,plate:plateData};
            }''')
            for name, data in assets.items():
                output = ROOT/'assets/environment'/f'{name}.glb'
                output.write_bytes(base64.b64decode(data))
                print(f'Exported {output.name}: {output.stat().st_size} bytes')
            browser.close()
    finally:
        server.shutdown()
        server.server_close()
        thread.join()
