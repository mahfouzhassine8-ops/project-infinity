# Skin 1.0.5.211 — compact ZIP preview corrective candidate

Exact implementation parent: skin 1.0.5.210, source
`843ea76648a5efc10a611d67b24c96f710953277`, ZIP SHA-256
`8febf697772ece72c9a445d0b5b6fd2650f97889a00e1e311dc0588199596bb3`.
Pair with the UNCHANGED permanently signed APK2103376, SHA-256
`8e8e139929592daedb63e0e41040258d655f132fd025b236de7dee1e88b47649`.
The user confirmed this installed pair for the reported regression.
Protected APK2103374 and skin1.0.5.208 are untouched.

## Proven regression

APK376 `ShowAndGetFile` calls `SetHeading` -> `Initialize` -> `OnWindowLoaded`
before assigning its ZIP-install context. `OnWindowLoaded` therefore leaves
preview OptIn empty. WINDOW_INIT publishes revision2103376. Skin210 skips its
SetProperty onload exactly for that revision, removing the working209 handshake.
Native admission then rejects both long-press and Preview before Python opens.
The native lifecycle test executes pinned production method bodies and proves
209 success ->210 failure ->211 restored success, without rebuilding Kodi.

Restore the synchronous onload in all14 FileBrowser copies. Every other byte in
those files is retained. Do not modify DialogContextMenu or the native engine.
Overlapping externally-created cloned ZIP pickers retain the existing209/210
masked-builtin limitation; the ordinary Kodi Install-from-ZIP route uses10126.

## Compact design

Only the approved small bottom mockups are followed. The preview card is authored
at680x440 units then mapped to340x220dp using actual native usable view dimensions.
It centers and fits smaller windows with an outer margin. Without native dp facts,
the fallback is explicitly approximate. Kodi group transforms scale typography,
graphics and inverse pointer hit-testing together. The existing worker refreshes
geometry; no additional service or worker is introduced.

Title, add-on ID, version and size come from the selected file. The ZIP glyph is
fixed preview artwork, not executed/extracted archive artwork. Cancel is left,
Install right, close at top-right. Loading/error text uses a bounded textbox.
Successful previews have no extra metadata sections or controls. Existing theme
variables provide Light Pearl, Dark/OLED and Cinema materials. Existing texture
and font files are never edited; eight new compact-only vector-derived PNGs are
generated deterministically by system Cairo/librsvg.

## Build and verification

Python3, lxml (inherited tests), C++17 compiler, zip, Cairo/librsvg are build tools;
no new Kodi runtime dependencies are added.

```
python3 repairs/skin-211-compact-preview/generate.py --parent /path/skin210.zip --out /tmp/skin211/delta
python3 repairs/skin-211-compact-preview/run_tests.py --parent /path/skin210.zip --out /tmp/skin211/evidence
python3 repairs/skin-211-compact-preview/tests/test_native_skin_lifecycle.py --candidate-root /tmp/skin211/delta --report /tmp/skin211/evidence/native-skin-lifecycle.json
python3 repairs/skin-211-compact-preview/package_candidate.py --parent /path/skin210.zip --delta /tmp/skin211/delta --out /tmp/skin211/delivery
```

Packaging copies the exact parent ZIP and replaces only enumerated entries.
Every entry gets before/after payload and compressed-byte SHA-256s. Every unrelated
entry must match both. Home, provider routing, all services, player/PVR, settings,
themes/fonts, metadata parser and install session state remain unchanged.

The separate actual-Kodi21.3 workflow uses a disposable Linux profile and software
renderer; its fixture adapters never enter the candidate. It injects a native
preview request to exercise real XML loading, fonts, textures, callbacks and Back
cleanup. It does not claim Android gesture delivery or Samsung Fold acceptance.

No lock, merge, release promotion or physical acceptance is performed.
