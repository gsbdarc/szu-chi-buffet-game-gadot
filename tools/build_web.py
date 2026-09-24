"""Export the actual Godot project, then prepare the browser shell.

GODOT_BIN may point to a Godot 4.7.2 executable. Export templates must be installed.
Use --pages to also build a standalone _site/ directory for GitHub Pages.
"""
import argparse
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from server.buffet_server import DEFAULT_CONFIG


def build(pages=False):
    godot = os.environ.get('GODOT_BIN') or shutil.which('godot') or str(Path.home()/'.local/share/asta-godot-tools/4.7.2/Godot.app/Contents/MacOS/Godot')
    engine = ROOT/'web/engine'
    engine.mkdir(exist_ok=True)
    for arguments in [['--editor', '--import'], ['--export-release', 'Web', str(engine/'game.html')]]:
        result = subprocess.run([godot, '--headless', '--path', str(ROOT), *arguments], capture_output=True, text=True)
        output = result.stdout + result.stderr
        print(output, end='')
        if result.returncode or 'SCRIPT ERROR:' in output or 'ERROR:' in output:
            raise SystemExit('Godot import/export failed. See errors above.')
    sizes = {f'engine/game.{extension}': (engine/f'game.{extension}').stat().st_size for extension in ['wasm', 'pck']}
    config = {'executable': 'engine/game', 'mainPack': 'engine/game.pck', 'fileSizes': sizes,
              'canvasResizePolicy': 0, 'focusCanvas': False, 'gdextensionLibs': []}
    (engine/'config.json').write_text(json.dumps(config, indent=2)+'\n')
    # The exported default HTML expects a standalone scene. The participant page
    # is the shared browser shell in web/index.html.
    (engine/'game.html').unlink()
    if pages:
        output = ROOT/'_site'
        if output.exists():
            shutil.rmtree(output)
        shutil.copytree(ROOT/'web', output, ignore=shutil.ignore_patterns('.gdignore', '*.meta', '.DS_Store'))
        conditions = json.loads((ROOT/'study/conditions.json').read_text())
        settings = {name: dict(DEFAULT_CONFIG, **values) for name, values in conditions.items()}
        for name, setting in settings.items():
            setting.update(condition=name, allowedParentOrigins=[], apiBaseUrl='', parentOrigin='')
        (output/'src/deployment.js').write_text('export const deployment = '+json.dumps({'storage': 'local', 'conditions': settings}, indent=2)+';\n')
        (output/'.nojekyll').touch()
        for name in ['THIRD_PARTY.md', 'GODOT_LICENSE.txt', 'GODOT_COPYRIGHT.txt']:
            if (ROOT/name).exists():
                shutil.copy2(ROOT/name, output/name)
        print('Standalone site:', output)
    print('Godot engine export sizes:', sizes)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--pages', action='store_true')
    build(parser.parse_args().pages)
