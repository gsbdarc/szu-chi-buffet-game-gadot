# Provenance and notices

- The 15 food GLBs are byte-for-byte copies of the Babylon comparison's models,
  converted from the supplied Asta_test Unity project's food assets. No food was
  replaced or generated for this port. Menu text, preview pictures, and fonts come
  from the same supplied project. Font licenses are beside the font files.
- The cafeteria and plate GLBs are transferred from Asta_Babylon's code-authored
  geometry using `tools/export_shared_environment.py`. Their physical dimensions
  are preserved. Godot renders them using its own materials, lights, and shadows.
- The browser interface, persistence layer, Python research server and survey
  integration are adapted from Asta_Babylon. The engine identifier and browser
  storage namespace are distinct. The Godot runtime does not load Babylon.js.
- Godot Engine **4.7.2**, MIT License: `GODOT_LICENSE.txt`.
  https://github.com/godotengine/godot . Editor and export templates are official
  release binaries verified against the release's SHA-512 checksums.
- Godot's bundled third-party components and their notices are listed in
  `GODOT_COPYRIGHT.txt` from the same release.
- Babylon.js **9.11.0** and its serializers are used only by the optional geometry
  transfer tool, not the distributed runtime. Apache License 2.0:
  https://github.com/BabylonJS/Babylon.js/blob/master/license.md .

No external asset host or CDN is required at runtime. The game is served from
its own origin. Research mode also uses the API on that same origin.
