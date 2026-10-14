# Infinity Add-on Rails — Mocha UI / Focus-independent Hold (staged)

**Status: code/source preserved; menu package host-tested; native signed APK not built; no production lock.**

## Protected inputs
- Exact complete skin parent: **1.0.5.221**, SHA256 `58bd3862493c6967865f82cd6d0555b450e8557d0f80f136306cf587efb9d4b3` (previous RC5 receipt; validate source ZIP locally).
- Protected approved skin lineage **1.0.5.215**. **Never use 1.0.5.211 as parent.**
- Existing helper **0.2.4**, preserve `rails.json` schema and all user data.
- Existing signed RC01 APK remains test-only; locked original code 2103377 unchanged.

## Fixed input route (GitHub branch)
`repairs/rails-hold-2103378/patch_native.py` now probes the **four visible Home rail controls by actual touch coordinates**, not `home->GetFocusedControl()`. Native C++ dispatch regression harness: `repairs/rails-hold-2103378/test_focus_dispatch.py`; invoked by `native_ci.py`. All unrelated input falls through normally.

**Native CI is not green on this new branch; an APK labelled Rails Hold RC02 does not yet exist.** A newly added branch-scoped native workflow is saved under `.github/workflows/infinity-2103379-rails-native.yml`, but no Actions run was registered from the connector commit as of check. Do not substitute the older RC01 APK.

## New Mocha design package (delivered as chat artifacts)
- Skin `skin.infinity.diggz-1.0.5.222-Mocha-Rails-RC2-TEST.zip`
  SHA256: `f44ba08b3838b3dd56bc04403b8a7c470e881c001d03f5c4d378a3a2b81f35d1`
- Helper `script.infinity.rails-0.2.5-Mocha-Rails-RC2-TEST.zip`
  SHA256: `5219ca62141c4b570765c405dbac5f5f026da7ccd56c2c9bd3ac96329f31403b`
- Source archive: `Infinity-Rails-Mocha-RC2-Source-and-Verification.zip`
  SHA256 `2a2d1178af5f8b20321aae909f28fb67a1af5cc6133846d3f68d41962753e4a8`; supplied in this conversation for audit/build continuation (contains only new XML, icons, helper changes, tests, source and approved screenshot; no standalone fonts).

**UI contract:** The exact user-approved `Infinity_Rail_Options_Mockup.png` is the visual target. Popup is anchored conceptually to the selected Movie/TV Show rail card, with a pearl glass panel, cyan-blue outline and highlighted Move, add-on artwork/name, red shortcut-only Remove, Settings where supported, Cancel/X, blue accents, responsive Light/Dark/OLED. Menu appears only upon intentional rail long-press; single tap launches and swipe scrolls. WindowXMLDialog fallback is disabled when .222 XML is unavailable; Kodi's own readable Dialog.select remains fallback.

New 14 responsive XML profile files and 7 new small icon/pointer textures; the ONLY changed existing skin ZIP file is `addon.xml`. **3,009 existing files byte-identical**, zero deletions. Helper modifies only version/description and menu callback, adds `mocha.py`; saved storage, default catalog and add-on data unchanged.

## Host verification
- 59 original storage/catalog tests: PASS, unchanged.
- 21 legacy runtime API tests: PASS after updating obsolete **test stubs only** for newer inspector's add-on id, current-window APIs and JSON output.
- 12 new menu/visual XML/preservation tests: PASS.
- All packaged skin XML parses; ZIP CRC checks passed.
- Pixel fidelity, Kodi Android modal interaction, Fold touch and ANR behavior **NOT** device-verified.

## Release gates
1. Native CI with focus-independent hold implementation; signed update-over-install package using original signer/code and unchanged non-Rails native subsystems.
2. Real Kodi GUI smoke of `WindowXMLDialog('InfinityRailsOptions.xml', ...)` with installed .222 skin and .2.5 helper, add/move/remove/Back, selected add-on identity.
3. Physical Fold first hold (other Home control initially focused), Light/Dark/OLED and all four view modes, ANR/perf, saved state and normal Close.
4. User explicit approval before lock. Maintain rollback to exact .221/.215 skin and original locked APK.

**Do not instruct user to install the .222/.2.5 pair as a completed long-press fix until matching native RC02 is built and verified.**
