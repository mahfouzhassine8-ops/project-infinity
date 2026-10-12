# Skin 1.0.5.210 critical correction candidate

Continue the exact failed skin 209 package SHA-256
`544279a735b2e2a4a7d1d77ac94a101dfd112f5f538deca1968f341d0ab6bb08`.
Accepted rollback 1.0.5.208 remains unchanged. Pair with APK 2103376.

## Root-cause evidence and scope

The bundled Home and legacy shortcut presets requested Playlist Browser source 100.
The pinned newer provider registry has no 100. Its real `channels_by_group` handler
produces exactly `Channels / Source not found.` for that route. Hidden TV widgets
could request this path while TV Shows was selected. Sports-only guards in 209 did
not cover that path. The provider registry is installed separately from the APK.

The correction reads the installed provider's registry locally. Known, portable AST
contracts identify the reviewed sequential and stable-ID allocators without importing
or executing provider code. A valid existing 100 route is preserved. Otherwise, an
unambiguous provider-defined TV or sports widget alias supplies the current ID. Unknown,
missing or ambiguous registries retain explicit provider browsing and make no background
request to a guessed source. TV/Sports widgets are gated to their own sections.
Compact mode retains its existing View All control when a TV/Sports route needs
explicit browsing, even while its normal widget-ready gate is false.

There are no provider/profile writes, provider replacements, network fetches, new
services or edits to playback/PVR/user favorites. The current device's provider version
was not captured; the runtime check resolves this on the device or uses the browse
fallback. User-generated custom shortcut files outside this package remain untouched.

File Browser's old masked SetProperty onload remains only for the 375 compatibility
path. APK 376 sets opt-in on the exact instance. Python startup and callback failures
cancel and close the modal, release the native request, and record a stage without
logging user paths. ZIP parsing, install confirmation, textures, themes, layout geometry
and the fourteen preview XML files are unchanged from 209.

## Reproduce

Supply the exact parent ZIP, then run:

```
python3 repairs/skin-210-critical-correction/generate.py --parent /path/to/skin209.zip
python3 repairs/skin-210-critical-correction/run_tests.py --parent /path/to/skin209.zip --out /path/to/evidence
python3 repairs/skin-210-critical-correction/package_candidate.py --parent /path/to/skin209.zip --out /path/to/evidence
python3 repairs/skin-210-critical-correction/validate_candidate.py --parent /path/to/skin209.zip --candidate /path/to/evidence/skin.infinity.diggz-1.0.5.210-Critical-Correction-RC1.zip --out /path/to/evidence
```

Use Python 3.9+ and lxml for build/test tooling. Shipped scripts use Kodi's existing
Python dependency. `provider-provenance.json` pins upstream evidence. Routing fixtures
are exact function excerpts for offline tests and are not included in the skin ZIP.

Tests execute actual provider registry, router, group handler and alias-filter bodies;
the old URL must reproduce the exact error. The original metadata suite and controller
behavior cases remain unchanged. New lifecycle fault tests cover imports, missing
controls and modal exceptions. Package gates compare all unrelated XML semantics and
all unrelated payload/compressed entries. These host checks do not validate Kodi GUI
rendering, installed user keymaps or Samsung touch dispatch. Fold acceptance is pending.

No lock, promotion or acceptance is performed by this recipe.
