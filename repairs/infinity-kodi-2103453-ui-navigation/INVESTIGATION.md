# Kodi UI/navigation source investigation — 2026-11-04

## Authority and boundary

User-authorized source-only investigation, targeted implementation and focused
verification of Kodi browsing, View Options, drawer organization and local media
access. No APK build, signing, installation, release, promotion or lock.

The user's subsequent evidence handoff requires actual inspection of
`Infinity-Kodi-UI-Original-Evidence.zip` before visual implementation continues.
That archive is **not accessible in this executor**. Its name is present in the
conversation, but no local path, downloadable attachment identifier or authorized
private download URL was supplied to the tools. Local file searches and connected
Page searches did not expose it. The available Pages contain older Cobra
references, which are not substitutes. No screenshots, video frames or full video
from this archive have been inspected. Do not report media verification as passed.

Production implementation is paused at this evidence gate. No production source
has been changed. No application tests or builds have been run for this task.

## Preserved starting point

- Source/evidence parent: `b6a85a74b3f11c44282986c6a391a84f5ad64c9d`.
- Signed 2103453 source: `cb7c6214807b79661e397cccb0740fc91fab3e24`.
- Signed APK SHA-256:
  `08ca19e9ff01e3830253980028dbcdbfb36056fd71b06a18cbfb922158ceaac8`.
- Native engine SHA-256:
  `d0b6f115e839fbe39e764e2fecad47418c501ab1ece853294578652cd0b80b98`.
- Isolated branch:
  `work/infinity-kodi-2103453-ui-navigation-source-20261104`.

Read-only extraction used actual XML/Python text members of the delivered signed
2103453 APK, not an older staging tree. Its skin manifest names version
`1.0.5.251` and uses only the `unified` folder with a 1080 × 2400 reference canvas.
The other packaged resolution directories are not automatically active layouts.

## Concrete signed-source observations

All following paths are APK member paths under
`assets/addons/skin.infinity.diggz/` unless stated otherwise.

1. **View registration mismatch.** `unified/custom_1130_Views.xml` offers
   `Container.SetViewMode(54)`, and `unified/View_54_ShowCase.xml` defines controls
   with ID 54. However, `unified/MyVideoNav.xml` omits 54 from its explicit `views`
   list and includes 592 instead. This is a concrete inconsistent registration;
   it is not proof that it caused the reported List pagination reversion.

2. **Nested selector sizing/close geometry.** In
   `unified/custom_1130_Views.xml`, the selector title and list use
   `20.833333%` width. Close button 8999 has top `-11`, dimensions 64 × 48,
   and is conditional on `system.getbool(input.enablemouse)`. In
   `unified/custom_1131_ViewSettings.xml`, the title uses the same narrow width,
   the list has a fixed width of 400, and close button 8999 is 64 × 48 at
   left `19.0104%`. These are source dimensions, not measured device touch bounds.

3. **Main versus nested menu ownership.** `unified/Includes.xml` defines
   `SideBladeLeft`, including header close 8999 and collapse control 9002.
   Both clear `MediaMenu` and restore the parameterized return control. The
   nested 1130/1131 dialogs close their own window. The main panel remains a
   separate legitimate layer. Any repair must distinguish the two layers and
   retain Back/focus behavior; deleting every second close control is not a
   justified fix. The Videos panel in `MyVideoNav.xml` is fixed at width 480,
   and several rows reserve 300 units of text width. No rendered clipping or
   tap failure has yet been reproduced in this task.

4. **Native persistence is path-specific.** The preserved native source
   `xbmc/view/GUIViewState.cpp` loads and saves through `CViewDatabase`.
   `xbmc/view/ViewDatabase.cpp` keys views by window, full path and skin (with
   the existing empty-skin read fallback). Different plugin pagination URLs
   can therefore be different keys. This establishes the storage mechanism,
   not the cause of this user's Red Light failure. The actual current
   `Red Light → In Theaters` URL sequence, provider view override behavior,
   and saved view rows have not been observed. Do not normalize arbitrary
   provider URLs, write Kodi's view database directly, or force a global view.

5. **Drawer routes already present.**
   `unified/Custom_1198_InfinityNav.xml` currently routes Home to Home,
   Movies to `plugin://script.infinity.commandcenter/?action=movies`, TV Shows
   to `...?action=tv`, Library to the generic Videos window, Add-ons to
   AddonBrowser, and Favourites to `favouritesbrowser`. The Library label
   currently does not distinguish the requested indexed-library and file
   destinations. Existing Movies/TV routes must be retained. A verified Sports
   route, Android-authorized Downloads access, and safe source-browser routing
   still need to be established; do not substitute an unrelated destination.

## Affected source candidates, not an implementation allowlist yet

- `unified/MyVideoNav.xml`: registered views and Videos-only panel geometry.
- `unified/custom_1130_Views.xml`: existing view selector and dismissal.
- `unified/custom_1131_ViewSettings.xml`: per-view settings panel.
- `unified/Includes.xml` / `unified/Includes_ViewSettings.xml`: scoped menu
  includes, with unrelated consumers protected.
- Existing `unified/View_*.xml`: only individually reproduced geometry defects;
  preserve view-specific designs, artwork and supplied metadata.
- `unified/Custom_1198_InfinityNav.xml`: existing drawer organization/routes.

No provider, background service, database, native engine, Android permission,
Preview, Cobra, chooser, shutdown or release-control change is authorized by
these observations. If safe persistence or local storage access requires a
protected component change, report that particular dependency before editing it.

## Selected verification and pending evidence

Before implementing, obtain and inspect the already supplied original archive:
verify ZIP integrity, enumerate files, inspect the two View Options screenshots
and drawer screenshot, and review the recording with its actual timestamps.
Distinguish static-frame review from full-video playback. No new diagnostic
export or duplicate upload is required; the existing archive needs a supported
private reference or executor-local path.

Selected read-only source check before execution:
`python repairs/infinity-kodi-2103453-ui-navigation/source_probe.py --apk <signed453.apk>`.
It checks authoritative skin folder, view registration, explicit selector
dimensions and original navigation actions. It does not execute Kodi, providers,
playback or shutdown and cannot establish physical usability or persistence.

After evidence access, record exact corrective tests before executing them:

- Existing Red Light category: List/Posters/InfoWall/TriPanel and relevant views
  across next/back/refresh/reopen, with actual path/content/view identity.
- Main and nested View Options: close, Back, touch bounds, remote/keyboard/mouse
  navigation, retained focus/selection and scroll position.
- Retained Home/Movies/TV/Add-ons/System routes; verified Sports and existing
  native Favorites; indexed movie/TV libraries, authorized local file navigation,
  Downloads access failures and source-return after Kodi playback.
- Actual full-skin rendering for cover/inner dimensions and both orientations,
  preserving details, proportions and existing responsive corrections.
- Exact source/member allowlist comparison against signed 2103453; no APK build.

Compatible Android/Fold execution and current provider state are not available
here. Linux/host/fixture results, if obtained, must remain explicitly separate
from Android or physical Galaxy Fold acceptance. No completed device test,
functional repair, or release readiness is claimed by this checkpoint.
