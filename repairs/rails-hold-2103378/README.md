# Infinity Rails hold correction — test only

The user separately authorized the scoped native correction and isolated test APK on 2026-10-14, after the captured Super Favourites routing failure was reported. This authorization does not promote or lock a build.

## Confirmed failure and correction

The device's global longpress mapping invokes Super Favourites' capture launcher. Its provider-owned dialog (captured instance 13000, `script-super-favourites-contextmenu.xml`) fails in `menus.py:76`: a float is passed to `setPosition` before list population. Rails never receives that context request. RC3–RC5 changes downstream of this interception could not correct it.

The native patch checks one-pointer `ACTION_TOUCH_LONGPRESS` before keymap translation, only in Infinity Home with no modal. It asks the actually focused supported rail container to hit-test the original screen coordinates using its cached rendered transform, checks visible/enabled ancestors and dynamic-item opt-in, selects the actual hit row without launching it, then posts a fixed Rails command with a validated section/key/add-on identity. Other input keeps its existing route. The existing ZIP-picker hold branch remains intact.

Helper 0.2.4 opts its generated items into that contract and resolves the received shortcut key. It verifies the expected add-on and current Home section, then displays Rail Options using Kodi's existing DialogSelect. Open, Move/Reorder, custom shortcut removal and available settings reuse the established operations. Back/Cancel performs no card action. The previous inspector correction is included.

No skin layout correction is needed for this failure. The complete 1.0.5.221 skin ZIP stays byte-identical. This retains all its themes, view modes, responsive profiles and Command Center integration; no approved skin file is replaced with an older baseline. The existing helper Store, catalog, defaults, artwork and data schema also remain byte-identical. No third-party add-on, keymap, service or startup patch is introduced.

## Verification and status

- 101 Python tests pass locally: the preserved 94-case suite (including the no-dialog sentinel correction) plus seven new exact-card menu cases.
- The added production C++ method compiles and passes controlled-peer cases for changed/unchanged selection, four rail IDs, transformed coordinates, hidden/disabled parents, inactive controls, active pan, outside hits, legacy items and unsafe commands. These peers are not real Android touch injection.
- The complete matched Android Kodi engine is reconstructed from RC5, with a ledger requiring exactly three changed native source files. Its full compilation is a separate CI gate.
- A separate real Kodi process exercises callback, populated DialogSelect, Back and plugin launch in a disposable fixture Home skin. This does not establish full Infinity theme rendering or Android gesture acceptance.
- Packaging requires green native and real-Kodi receipts, the original parent package hash, original permanent signer, unchanged native exports/dependencies, and byte-identical parent payload except the native library and manifest version label.
- Physical Fold acceptance remains required. Never infer it from these checks.

The native working directory/branch uses task number 2103378. The test APK deliberately retains Android versionCode 2103377 with a distinct `1.0.9-Rails-Hold-Correction-RC01` versionName: the exact original signed 2103377 APK can therefore be reinstalled for rollback without a downgrade/uninstall or data loss. Original baseline files are not overwritten.

## Installation after all packaging gates pass

1. Keep the original signed 2103377 RC5 APK, helper 0.2.3 ZIP and complete skin 1.0.5.221 ZIP. Keep the protected 1.0.5.215 archive separately.
2. Close Infinity normally. Install the signed Rails-Hold test APK as an update to the existing application; never uninstall or clear data.
3. Install helper 0.2.4 through Install from ZIP, over the existing helper. The existing full skin 1.0.5.221 is compatible and does not need repatching. If reinstalling the skin, use the unchanged complete ZIP.
4. Reopen Infinity normally to load the new helper-generated items. Keep all rail preferences and add-on settings.
5. On the Fold, hold both a selected card and a different card once in each of Normal, Cinema, Compact and Two-Pane. Verify the exact add-on title and menu entries, tap launch, normal swipe, reorder persistence after reopening, custom shortcut-only removal, supported settings and clean Back/X dismissal. Check Light, Dark and OLED, folded/unfolded layouts, Command Center labels and Resume Hub.

## Rollback

Close Infinity normally and reinstall the preserved original signed 2103377 APK as an in-place update. Reinstall helper 0.2.3 from its ZIP. The skin has not changed. Do not uninstall, delete profiles, reset settings or remove add-ons. Helper storage format is unchanged, so saved shortcut ordering remains usable. Keep the actual candidate and original package hashes with the test report.
