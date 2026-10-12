# Infinity Skin 209 — ZIP Preview and Corrective Polish RC1

Parent: exact locked 1.0.5.208 ZIP SHA-256 `a6d496f6bd576676d060a31b572e3930c7ac6a3625b8eaf5dcdd04433f172408`. Parent source/lock commit: `38d916bb885fe434f923bb951e605e65ff1fb34f`.

Test candidate only. No lock, production promotion, profile migration, add-on deletion, or installation is performed. Pair with the separately signed native-preview APK 2103375. APK 2103374 and skins 208/207 remain rollback artifacts.

## Scope and reproduction

This recipe produces 59 modified and 27 new payload files from the complete, hash-verified 208 package. `parent-files.json` records every parent payload. `change-inventory.json` records every candidate delta hash and retired/guarded route. Derived XML is generated in ignored `delta/`; the three Python modules and master dialog XML are maintained as source here. Every unrelated compressed ZIP entry is retained.

1. Extract the exact 208 ZIP into an isolated staging directory. Do not use an installed profile export as the parent.
2. Run `python repairs/skin-209-preview-polish/generate.py --parent <staging>/skin.infinity.diggz`.
3. Run `python -m unittest discover -s repairs/skin-209-preview-polish/tests -v` (35 targeted cases).
4. Run `python repairs/skin-209-preview-polish/package_candidate.py --parent <exact-208.zip> --out <output>`.
5. Run `python repairs/skin-209-preview-polish/validate_candidate.py --parent <exact-208.zip> --candidate <output>/skin.infinity.diggz-1.0.5.209-File-Preview-Polish-RC1.zip --out <evidence>` (8 candidate gates).
6. Run the unchanged inherited `repairs/skin-207-verified-cleanup/validate_candidate.py` against its .204 base and the exact .208 parent. Its 11 checks protect the inherited .207/.208 repairs; candidate byte/semantic checks then establish preservation of those interfaces. Do not claim this parent run executed .209.

## Preview boundary

Only Kodi's shares-based Install from ZIP picker opts in. Native code supplies the selected path through the exact dialog instance ID and transient properties; filenames never enter a built-in command. Long press, context action and Preview open an on-demand Python dialog. Single tap uses the original native path. Cancel/Back restores list 450; only explicit Install, successful reinspection and matching native nonce/selection can re-enter the original installer. Unknown Sources, installer confirmation and dependency checks retain their original owner.

Local/special/file ZIP metadata inspection is bounded: 65,557-byte tail, 2 MiB central directory, 8,192 entries, 256 KiB XML, 512 KiB icon, four-second inspection budget. No member extraction or execution occurs. Remote ZIPs remain info-only in this preview and can still use ordinary Kodi installation. Icons reference the bounded approved ZIP member through Kodi's texture system; normal texture-cache behavior is not disabled globally.

## Retired Live TV boundary

All 61 skin XML launch actions for `script.infinity.live` are removed. Native TVGuide retains its prior fallback role. The dedicated Power-menu group 17/button 1700 is removed with scoped neighbor repairs. Existing TV provider source-100 presets and captions remain exact: a source error does not establish retirement. All 56 active Sports Live Events widget contents retain their original provider URIs and load only in the Sports section. The optional legacy add-on dependency is removed from this skin; the add-on itself, import-time focus/Multi-View hooks, credentials, favorites, last channel, PVR, EPG, recordings, timeshift and providers are retained.

The recording's Channels / Source not found dialog requires investigating the hardcoded TV preset and unguarded background contents. The provider's installed source/version/source store is unavailable, so that precise provider failure cause is an inference. Separately installed add-ons and user-saved shortcuts have not been deleted or certified unreachable.

## Preservation and acceptance

All 2,075 candidate XML documents parse. All 58 modified non-manifest trees are semantically compared after narrowly accounting for the explicit repairs. 2,881 unrelated package entries retain their payload and compressed bytes. Existing fonts, textures, services, playback, Health, Command Center, Resume, shutdown and approved UI are preserved.

The exact manifest selects unified; `resources/infinity-native-responsive-v1.json` is absent. New preview XML is available in all 14 presentation/fallback families. Geometry tests use the native Android 1.03 aspect-mismatch threshold and uniform logical-area adaptation for the active unified browser. They cover 16 window profiles and are source checks, not physical Fold results.

The accompanying report and labelled visual projections distinguish captured before evidence from projected after layouts. Physical Samsung Fold interaction, rotation/fold/multi-window, long sessions, playback/PVR/provider operation and thermal measurements remain acceptance work. No post-change device screenshot or production certification is claimed.
