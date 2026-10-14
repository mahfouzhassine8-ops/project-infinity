# Infinity Custom Add-on Rails RC3 — 1.0.5.219 TEST

Versions .217 and .218 already have separate RC3 candidates; this build uses the next available .219 version and helper 0.2.1. Those candidates and their branches are preserved.

Status: host-verified test candidate. **Not locked. No live Kodi or physical Fold testing was performed.**

Complete skin package: `skin.infinity.diggz-1.0.5.219-Custom-Rails-RC3-TEST.zip`.
Required companion: `script.infinity.rails-0.2.1-Custom-Rails-RC3-TEST.zip`.

Install the companion through Install from ZIP first, upgrading the existing helper without uninstalling it. Then install the complete skin ZIP through Install from ZIP and accept the skin reload. There is no Program add-on resource-patching step. The helper is not published in a repository from which Kodi can automatically fetch it; the separate ZIP is required.

The source input is the exact 1.0.5.215 package, SHA-256 `486aa86c8f8dcda31d80c6d058f4b96154dcb2b3f1a18cfa464c65e280ec7e70`. Its repository provenance record is commit `85b1305ef7a220dd23aaeb40c7d38150b8da4a92`; the actual complete skin source is that hash-pinned ZIP. RC2 helper input SHA-256 is `b0d0b293cc66d937cb82dd6c8ac9e97956e67f88efec10e764d4631540f7a9da`. Branch parent/provenance record: `faae58d7594b8be1e423e119ddd1e1c9839767fd`.

## Owned correction

RC2 published rail actions to Kodi's native context menu. That loads the inherited `DialogContextMenu.xml`. Kodi clones template button 1000 into group 996 and adjusts background 999, then positions the window using that background's dimensions. The inherited profiles include percentage geometry and nested controls that are unsuitable for this externally resized popup. The screenshot and this command path identify the inherited context window as the problem owner. The exact active profile and calculated dimensions on the physical Fold have not been captured, so the complete device-side causal chain is not claimed verified.

RC3 uses a narrowly scoped onload bridge in that context window for Home rail items only. It closes the inherited shell and opens `InfinityRailsOptions.xml` through an on-demand `WindowXMLDialog`. It selects a bounded, content-sized XML shape using Kodi's actual window coordinate dimensions before initialization. Numeric child geometry stays inside a centered responsive group, so Infinity's existing in-place XML reflow cannot overwrite Python-assigned dimensions. The original context-menu controls remain semantically preserved in a conditional include for other items. No native touch recognizer, keymap, gesture threshold, global menu, or unrelated dialog is redesigned.

Single tap keeps the original directory launch paths. Context action/intentional long-press opens Open Add-on, Move / Reorder, custom-only removal from the current rail, supported Add-on Settings, and Cancel. X and Back dismiss. Removed shortcuts do not uninstall add-ons. Original defaults cannot be removed. Each placement is managed independently. Reordering uses the original built-in tokens and custom tokens. Unavailable custom preferences are retained.

Normal uses 9200, Compact 8820, Two-Pane 8720, and Cinema its existing More menus row 19600. All fourteen XML profiles have the same integration and original home geometry/actions preserved. No separate Custom Add-ons section is introduced.

`store.py`, `catalog.py`, and `defaults.xml` are byte-identical to RC2 and to the existing 0.2.0 helper. Saved `special://profile/addon_data/script.infinity.rails/rails.json` remains schema 1. Atomic replace, fsync, bounded locking, corruption protection, duplicate prevention and closing/abort checks are retained. No migration or configuration deletion runs during installation. Revision changes invalidate only the affected rail URI; Kodi's existing directory-container logic preserves selection by path and keeps the neighboring index after removal. This focus behavior still needs runtime confirmation.

## Verification

- Original prior RC1 suite: 182 passed, unchanged test files, after rebuilding its original fixture package.
- RC3 suite: 147 passed: 78 carried storage/catalog/legacy-installer tests, 19 carried runtime tests with the intentionally changed menu captions and chooser mocking, and 50 new RC3 package/integration/geometry/callback tests. The legacy installer tests exercise prior rollback logic as evidence; that installer is not shipped or imported by RC3.
- Skin: all 2,107 XML files parse; ZIP CRC passes. 2,937 of 2,978 original files are byte-identical. 41 original files change; 32 XML files are added; none are deleted.
- All original skin Python, fonts/textures, provider shortcut definitions, Command Center dialogs, settings-label layout repairs, Resume/Health screens and shutdown-related sources remain byte-identical. The external repaired Command Center resource files are never touched by this helper.
- The existing item-size reflow method also passed 75 compiled host-harness scenarios. This is a method-level check, not a full native engine build.
- Python 3.11 grammar and helper ZIP CRC pass. No service, polling, networking, resource patcher, full-home refresh or skin reload is shipped in helper runtime.
- Host preview uses the actual baseline Roboto font and the geometry function across Light, Dark and OLED, six representative viewport shapes. It is an illustrative Pillow preview, not a Kodi rendering test. XML theme references remain dynamic, with true-black OLED surface/field colors.
- 500 host add/move/remove cycles: median approximately 3.34 ms, p95 approximately 5.57 ms, maximum approximately 10.20 ms per complete cycle on this host. These include filesystem persistence, not GPU rendering or Python startup on Android. Raw allocation measurements include benchmark bookkeeping; they do not establish the absence of Kodi memory leaks.

Menu fade is 190 ms open / 140 ms close and respects `Infinity.OptionalMotionAllowed`. Reordering/removal uses existing rail rendering and scrolling; no new individual-neighbor movement animation is implemented. Native frame pacing, 60 FPS, live artwork flicker, actual menu-open latency, interpreter startup cost, Android lifecycle and shutdown performance remain unmeasured.

The centered XML group participates in Infinity's existing in-place reflow; its child coordinates are numeric and are not overwritten by Python. On Kodi XML reinitialization, the dialog validates the selected shape again. If coordinates change without reinitialization, the next input dismisses instead of accepting a stale selection. Long choosers show at most eight action rows and scroll within the dialog. Very small windows below 220×252 Kodi coordinate units dismiss safely. Actual Fold/unfold, split-screen, floating resize, instant reflow, modal Back behavior, long-press versus swipe, and focus return require device acceptance.

## Reproduce

Run the builder with the exact .215 input; no APK or Kodi native checkout is needed:

```bash
python3 features/infinity-rails219/tools/build_rc3.py /absolute/path/to/skin.infinity.diggz-1.0.5.215-CommandCenter-Settings-Readability-RC1-TEST.zip --output /absolute/path/to/delivery
```

Set `RAILS_BASELINE`, `RAILS_CANDIDATE`, `RAILS_HELPER`, and `RAILS_RC2` to the exact corresponding ZIP paths, then run:

```bash
python3 -m unittest discover -s features/infinity-rails219/tests -v
```

Per-file hashes, changed paths, test logs, geometry preview and host measurements are in `evidence/`; package hashes and installation details are in `DELIVERY.json`.

## Rollback and acceptance

To deliberately roll back, install the saved, hash-verified complete .215 ZIP through Install from ZIP and accept Kodi's downgrade confirmation if displayed. Do not uninstall the skin or delete profile data. Leave the helper installed; it has no background service and preserves rail choices for reinstalling .219. Do not use the retired .216 patch/restore workflow against .219. Command Center's independent label repair and the APK stay in place. Package identity and prior file restoration are host-verified; the actual Kodi downgrade/install flow is not device-tested here.

On the Fold, check startup/navigation without automatic menus; single-tap launch; hold versus horizontal swipe; add to each destination; remove/re-add without uninstalling; reorder and focus return; all four modes and three themes; fold/resize while the menu is open; repeated open/close; restart; and Normal Close with saved choices intact. Approve a lock only after physical acceptance.

Official implementation references: [Kodi context window](https://github.com/xbmc/xbmc/blob/Omega/xbmc/dialogs/GUIDialogContextMenu.cpp), [directory-container selection preservation](https://github.com/xbmc/xbmc/blob/Omega/xbmc/guilib/GUIBaseContainer.cpp), [Window coordinate API](https://github.com/xbmc/xbmc/blob/Omega/xbmc/interfaces/legacy/Window.cpp), [WindowXMLDialog callbacks](https://xbmc.github.io/docs.kodi.tv/master/kodi-base/d5/dc9/group__python__xbmcgui__window__dialog__xml.html).
