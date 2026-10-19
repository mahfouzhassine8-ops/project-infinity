# INFINITY GROUP #2 — COMPLETE SOURCE-LEVEL CORRECTIVE STAGE (NOT FOLD-APPROVED)

**Date:** 2026-10-19. **Current user direction:** "Okay back to 2 finish it so we can check... see now we are going backwards instead of forwards." Work Group #2 is active again. Preserve saved unfinished Group #1 and source-staged Group #3; no work on them. Cobra and shutdown off limits.

## Protected signed source

- **Immutable developmental base:** versionCode **2103390**, APK SHA-256 `778b84a5f0d8712f250c538bacfa3c01e1352a936e0b7b9aa79cbaada9b22dbb`.
- **7,430 original APK entries**; no signed APK rewritten, repacked or installed in this checkpoint.
- Previous Group #2 skin-only stage `4b18d89c7fb69ec554887257c07b87ff6aebf400`, tests `2b97f4ecb8aa835e9d39ae0c26776df946d0c345` remain intact.
- Only **42/7,430** original signed APK skin members are permitted to differ in that **virtual skin** stage, 7,388 unchanged. These are `AddonBrowser.xml`, `Includes_InfinityBrowser223.xml`, `FileBrowser.xml` across the exact 14 approved Infinity layouts. No art assets deleted; actual Kodi search, ZIP and repository handlers unchanged.

## NEW: Native interaction source overlay for remaining original tasks #06–#08

**Committed patcher:** `repairs/2103390-bugfixes/group2/native_addonbrowser_patch.py`, commit **`a58918b2a62b71898bf4e075964b9566567c05f8`**, Git blob `a361eb1c326c671fa3b481a18ab4a8c9d676da62`. This is a **fail-closed SOURCE-STAGING tool**, NOT a compiled native library or a new APK.

It changes no source outside these **four** Kodi native paths:
1. `xbmc/addons/gui/GUIWindowAddonBrowser.h` — ephemeral in-memory browser-only hidden add-on IDs and last touched item fingerprint; overrides context actions only on Add-on Browser.
2. `xbmc/addons/gui/GUIWindowAddonBrowser.cpp` — first tap selects, second tap on same path/index intentionally opens; right-click remains original native context; Hide from this browser action for valid installed-user-addon items; Show hidden add-ons restoration when items are filtered, including empty-list recovery; clearing hide state on leaving the browser. The original Kodi root may omit Available updates and Recently updated when no updates exist, so only the Infinity Add-on Browser root adds **real** native `addons://outdated/` and `addons://recently_updated/` links when otherwise absent. These are existing native Kodi paths, not fake installers/searches, and all six root capabilities remain reachable.
3. `xbmc/addons/gui/GUIDialogAddonInfo.cpp` — after Kodi's existing essential-dependency lock, adds a confirm/cancel for actual Disable only while Addon Browser is the active parent and **Infinity skin** is active. Cancel returns before `DisableAddon`; original enable/settings/update/install buttons and non-browser behavior are untouched.
4. `xbmc/addons/ContextMenus.cpp` — separately confirms actual Disable from native context menus under the same window+skin guard (that path previously bypassed the AddonInfo safeguard). Other windows, Cobra and other context actions use the original path.

No persistent Hide database, no call to Kodi's `DisableAddon` or `UnInstall` from the Hide code, no disabled add-ons on staging, no new global keymap, no native `GUIBaseContainer` or `InputManager` change. Native patch applies only to source checkout passing caller-provided SHA-256 preimages on **all four files**, creates a different staging folder, and refuses other files.

**Original exact upstream Kodi Omega source-anchor validation executed with connected GitHub:** 4 original files inspected, **13/13 exact unique source replacement anchors passed**, each reverse transform restores the unchanged upstream file exactly. Original Omega Git blob anchors:
- `GUIWindowAddonBrowser.h`: `7f605eefe32b00e303b037f5283e8968741f797f`
- `GUIWindowAddonBrowser.cpp`: `16ac3858ccce99ab2e4299ca076cd83dd47722da`
- `GUIDialogAddonInfo.cpp`: `671e55dcf4479f3df2fcf908a70914a5a48121ef`
- `ContextMenus.cpp`: `23f50365d40d6a592a0a4473fd9849a37678ef6e`

**Important limitation:** Omega source anchors are not a proved SHA-equivalent checkout of the custom **2103390 compiled libkodi.so**. Applying this overlay to an actual 2103390 native build checkout, Android compilation/signing, and a true byte/member-level compiled APK regression still remain **NOT RUN**. The source script fails closed if any original SHA/anchor does not match.

## Tests and source verification

- Native patch test source saved: `repairs/2103390-bugfixes/group2/test_native_addonbrowser_patch.py`, commit **`3444bef95ec6678ddc46f8c0112b7ddc1f1d24b3`**. Has 9 synthetic/pure-source checks and a 10th real-source test that is **intentionally skipped when the exact native source checkout is unavailable**; do not count the skip as a pass.
- An independent local equivalent native source-stage suite executed **10/10** checks green (mocked native source fixtures/guards), and the original signed skin source suite re-ran **10/10** green: **20/20 local host assertions in separate suites**, but **NOT** integrated Android/native compilation or real Fold behavior.
- Read-only review of current Kodi Omega original native routing confirmed: root `addons://user/`, `outdated/`, `recently_updated/`, `repos/`, `install/`, `search/`; original keyboard Search, search database result population, native `CGUIDialogFileBrowser::ShowAndGetFile` ZIP picker, original `CAddonInstaller::InstallFromZip`, repository browsing, original Addon Info actions and standard Kodi global/plugin context action behavior all present. The new branch preserves those native handlers and only adds the scoped presentation guard. Actual add-on/provider state unmodified.

## Remaining acceptance required before marking Group #2 checked

1. Read the exact native source used to compile the **signed 2103390 parent**, verify all four source preimages, apply overlay in isolated build checkout. Native Android C++ compile/link must go green; audit that only intended app native binary+42 scoped skin XML members (plus necessary signing metadata) differ from the signed base, and compile did not change Cobra/shutdown semantics.
2. Test physical Galaxy Fold: first tap selects and does NOT launch, second same item opens it; long-hold selects the actual touched item and opens its correct existing context menu; verify Back and focus recovery, scroll, provider actions and update states.
3. Test Hide in My add-ons: hidden item disappears from browser **without changing enabled/install/user data**; the Show hidden add-ons item restores it; hide reset on browser exit. Test an empty hidden list and actual add-on dependencies.
4. Test Disable through **both native entry points** with Cancel then Confirm and dependency-blocking; no accidental disabling. Confirm no change to native Enable, repository update, installer actions.
5. Test six exact root native routes, empty/nonempty Available updates / Recently updated, repository categories/selection, real native Install from ZIP + existing compact ZIP Preview, real Search keyboard and results, D-pad/touch/Back, both Fold screens and Light/Dark/OLED themes, no other windows affected.
6. Obtain user physical acceptance after signed install-over APK; **do not check Group #2 complete or final lock based on host proofs alone**.

**Current state:** Original tasks 05/06 visually staged, 07/08 scoped native behavior source-staged and native repository/ZIP/Search routes audited. **Group #2 is SOURCE-STAGED, NOT ANDROID/FOLD-COMPLETE.** No signed APK generated. **Group #1/#3 remain saved unfinished; Cobra/shutdown untouched.**
