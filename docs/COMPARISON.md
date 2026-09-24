# Comparing the engine versions

The Godot port preserves the Common Table task and interface. It uses Godot for
the 3D implementation so the same task can be evaluated across engines.

| Area | Babylon.js | Godot |
| --- | --- | --- |
| Editable project | JavaScript modules | Godot 4.7.2 project and GDScript |
| Browser renderer | Babylon.js | Godot Compatibility renderer, WebAssembly and WebGL 2 |
| Food assets | 15 GLBs converted from the original Unity project | Identical GLB files, including embedded textures and dimensions |
| Cafeteria and plate | Procedural geometry | The same geometry transferred to GLB; a 29 cm plate |
| Interface | HTML/CSS, Lora and Inter | Same interface styling and controls, connected through JavaScriptBridge |
| Portion placement | Mesh-derived 3 mm height grid | Same grid spacing, plate boundary, rotation sequence and placement rules |
| Interaction | Serve, browse, select, move, remove, undo | Same participant actions; Godot performs picking and movement |
| Photograph | 1024 × 1024 plate render | 1024 × 1024 Godot SubViewport render |
| Research data | Version 1 schema, `engine: babylonjs` | Same schema, `engine: godot`; separate browser storage namespace |
| Static website | Browser saves and downloads | Browser saves and downloads |
| Central collection | Optional Python/SQLite host | Same backend, separately deployed |

## Interpreting a comparison

Use the same device, browser, viewport, food order and sequence of selections.
Compare first-load time with an empty cache separately from repeat visits. Inspect
the same meal and photograph in both versions. Record interface response, frame
rate, memory use and errors separately; a single FPS observation is not a general
engine benchmark.

Lighting and PBR shading differ between engines. The models, scale and textures
are preserved, but the output is not pixel-identical. Improving the source food
geometry, material maps or photographs would improve both versions and should be
done consistently before a controlled visual comparison.

The Godot export currently includes about 39.5 MB of WebAssembly plus 50.6 MB of
packed resources before HTTP compression. Download cost and rendering speed are
different measurements. No claim that one engine is universally faster is made.

## Scope and deployment

The full participant experience runs in the browser. Opening `project.godot` in
the editor permits scene and script editing; its native preview shows the hall.
The HTML interface is not a separate native desktop/mobile Godot interface.

The Godot source is separate from `Asta_Babylon` and `Asta_test`. The target
repository is `gsbdarc/szu-chi-buffet-game-gadot` (spelling supplied by the owner).
The Babylon version is available at
https://gsbdarc.github.io/Szu-Chi-game-babylon.js/ .

Godot's single-threaded export avoids the cross-origin isolation requirement of
threaded exports. GitHub Pages serves the static game; it cannot run the included
Python research backend. See [research setup](RESEARCH.md).

Implementation references:

- [Godot web export](https://docs.godotengine.org/en/stable/tutorials/export/exporting_for_web.html)
- [JavaScriptBridge](https://docs.godotengine.org/en/stable/tutorials/platform/web/javascript_bridge.html)
- [Custom web shell](https://docs.godotengine.org/en/stable/tutorials/platform/web/customizing_html5_shell.html)
