# The Common Table — Godot

The same cafeteria buffet game implemented with **Godot 4.7.2**, for comparison
with the [Babylon.js version](https://gsbdarc.github.io/Szu-Chi-game-babylon.js/).

## Play online

Source repository: [gsbdarc/szu-chi-buffet-game-gadot](https://github.com/gsbdarc/szu-chi-buffet-game-gadot).

GitHub Pages deployment is pending. The project is in its own `Asta_Godot`
folder; its current `localhost` link is a local preview.

The GitHub Pages preview saves meals and photographs in the player's browser.
Download your choices or a meal with photographs to keep a copy. It does not send
participant data to a researcher. Refresh restores a meal; **Start a new meal**
opens a fresh session after completion.

- Click/tap a dish, use **Add one portion**, press Space, or drag onto the plate.
- Use arrows or the menu to browse the same 15 foods.
- **View plate** lets you select and move each portion; remove or undo when allowed.
- **Photograph** creates a 1024 × 1024 PNG.
- **Review meal → Finish meal** completes and saves the meal.

Once deployed, the site runs on GitHub's servers and stays available when the
developer's computer is off. It requires WebAssembly and WebGL 2 support.

## What uses Godot

`project.godot`, `scenes/main.tscn`, and `scripts/` are the editable Godot project.
Godot renders every 3D object and implements cameras, triangle picking, per-portion
placement and movement, shadows, animation, and plate photographs. Its actual
engine is exported to WebAssembly with the Compatibility renderer and threads off.

The HTML interface and browser persistence layer are shared in design with the
Babylon version, communicating through Godot's JavaScriptBridge. This keeps the
participant task, controls, wording, fonts, and data format consistent. The full
participant interface runs in the web export; the editor's native scene preview
shows the 3D environment. No Babylon renderer is used at runtime.

See [comparison notes](docs/COMPARISON.md), [research setup](docs/RESEARCH.md), and
[verification](docs/VERIFICATION.md).

## Build and run

Using Python 3.11 or newer, install the pinned editor and its web export templates:

```sh
python3 tools/install_godot.py
```

On macOS the build finds this installation automatically. Elsewhere, set
`GODOT_BIN` to the executable path printed by the installer.

```sh
python3 tools/build_web.py --pages
python3 -m http.server 8772 --bind 127.0.0.1 --directory _site
```

Open http://127.0.0.1:8772 for a local preview. The `localhost`/`127.0.0.1` address
requires that local server. After deployment, share the GitHub Pages URL instead.

For the research version, after exporting:

```sh
python3 server/buffet_server.py
```

Open http://127.0.0.1:8770. The included server stores sessions, events, and PNGs in
SQLite and provides CSV/JSON exports and survey handoff. It needs a separate host
for a participant study; GitHub Pages cannot run it.

## Tests and deployment

```sh
python3 -m unittest discover -s server -p 'test_server.py'
python3 -m venv .venv
.venv/bin/pip install -r tools/test-requirements.txt
.venv/bin/python tools/test_game.py
.venv/bin/python tools/test_pages.py
```

The browser tests use installed Chrome, isolated profiles, and synthetic sessions.
Additional WebKit/Firefox and capacity/touch checks are in `tools/`.

GitHub Actions installs verified Godot binaries, imports the project, exports it,
and deploys `_site/` on pushes to `main`. Exported engine files, local databases,
test artifacts, and credentials are excluded from the source repository.

Asset provenance and licenses: [THIRD_PARTY.md](THIRD_PARTY.md).
