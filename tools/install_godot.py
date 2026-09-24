"""Install the pinned official editor and web templates, checking SHA-512.

The editor stays in a project-specific user cache. Other Godot installations
are unaffected. Supports macOS and Linux x86_64 (including GitHub Actions).
"""
import hashlib
import os
import platform
import shutil
import subprocess
import urllib.request
import zipfile
from pathlib import Path

VERSION = '4.7.2'
CACHE = Path.home()/'.local/share/asta-godot-tools'/VERSION
BASE = f'https://github.com/godotengine/godot/releases/download/{VERSION}-stable/'


def download(name):
    target = CACHE/name
    if not target.exists():
        temporary = target.with_suffix(target.suffix+'.partial')
        request = urllib.request.Request(BASE+name, headers={'User-Agent': 'CommonTable-build'})
        with urllib.request.urlopen(request, timeout=120) as response, temporary.open('wb') as output:
            shutil.copyfileobj(response, output)
        temporary.replace(target)
    return target


def install():
    CACHE.mkdir(parents=True, exist_ok=True)
    sums = {line.split()[-1].lstrip('*'): line.split()[0] for line in download('SHA512-SUMS.txt').read_text().splitlines() if line.strip()}
    mac = platform.system() == 'Darwin'
    if not mac and (platform.system() != 'Linux' or platform.machine() != 'x86_64'):
        raise SystemExit('Install Godot 4.7.2 and its web export templates manually on this platform.')
    editor = f'Godot_v{VERSION}-stable_'+('macos.universal.zip' if mac else 'linux.x86_64.zip')
    templates = f'Godot_v{VERSION}-stable_export_templates.tpz'
    for name in [editor, templates]:
        archive = download(name)
        with archive.open('rb') as stream:
            digest = hashlib.file_digest(stream, 'sha512').hexdigest()
        if digest != sums[name]:
            raise SystemExit(f'Checksum mismatch: {archive}. Delete the download and try again.')
        print('Verified:', name)
    if mac:
        subprocess.run(['/usr/bin/ditto', '-x', '-k', str(CACHE/editor), str(CACHE)], check=True)
        binary = CACHE/'Godot.app/Contents/MacOS/Godot'
        template_root = Path.home()/'Library/Application Support/Godot/export_templates'
    else:
        with zipfile.ZipFile(CACHE/editor) as archive:
            archive.extractall(CACHE)
        binary = CACHE/f'Godot_v{VERSION}-stable_linux.x86_64'
        binary.chmod(0o755)
        template_root = Path.home()/'.local/share/godot/export_templates'
    destination = template_root/f'{VERSION}.stable'
    destination.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(CACHE/templates) as archive:
        for name in archive.namelist():
            basename = Path(name).name
            if basename in ['web_nothreads_release.zip', 'web_nothreads_debug.zip', 'version.txt']:
                (destination/basename).write_bytes(archive.read(name))
    if os.environ.get('GITHUB_ENV'):
        with open(os.environ['GITHUB_ENV'], 'a') as output:
            output.write(f'GODOT_BIN={binary}\n')
    print('GODOT_BIN='+str(binary))


if __name__ == '__main__':
    install()
