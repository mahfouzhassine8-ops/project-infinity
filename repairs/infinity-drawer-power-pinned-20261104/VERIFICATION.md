# Source-only Power footer verification — 2026-11-04

## Status

**PASS: 55 focused in-memory source/structure assertions** against exact parent and the new GitHub-committed XML, using the connected GitHub repository contents. The follow-up GitHub diff check confirmed the isolated work branch changed only this SCOPE.md plus one skin XML; this verification note is an additional evidence file. No Kodi UI runtime, Android phone or playback/shutdown test was executed.

- Parent branch: `work/infinity-drawer-shortcuts-scope-20261104`
- Work branch: `work/infinity-drawer-power-fixed-source-20261104`
- Source file: `repairs/infinity-kodi-2103453-ui-navigation/overlay/assets/addons/skin.infinity.diggz/unified/Custom_1198_InfinityNav.xml`
- Original Git blob SHA: `3821a892ff54e74b29c91cccd14b147d0cbdb214` (145,416 text characters)
- Candidate Git blob SHA: `fba4228ee127437e31eea96e21ed3b0333c56754` (145,428 text characters)
- Source change commit: `c151b3663076265a1bccb50a374fadef6e80b2c1`

## Source results

- Original and candidate XML tag nesting was scanned and found balanced; the complete XML contents were re-fetched from GitHub after the commit.
- **All 182 control nodes retained**; all IDs unique, exactly one new `1198898` footer group ID.
- Original button `1198304` is beneath anchored footer `1198898`, **outside** original scrolling grouplist `1198899` and still inside original panel `1198888`.
- Original scrolling grouplist reserves bottom **104** units instead of 18: 80-unit footer + 6-unit separation + 18-unit bottom margin.
- Anchored Power group uses the original horizontal 18-unit inset, bottom 18 and height 80; the original panel 88% height, 1050 max, width, theme and animation are unchanged.
- The scrolling grouplist retains the original Home, Movies, TV, Favorites, Add-ons, Settings, UI Theme, System Hub, Library and Explore controls; Power is visually separate, so the list may scroll without scrolling Power away.
- The list's only new navigation binding is `onright=1198304` to help focus Power from remote/keyboard navigation.
- Every original button definition was compared with the candidate after normalizing indentation and found **unchanged**. This includes the original Power label, image, focus artwork, `Dialog.Close(1198)` and `ActivateWindow(shutdownmenu)` click actions.
- The **sorted multiset of every original `onclick` action was identical** between the two sources (no deleted, added, or changed action).
- All 55 checks passed; 30 compare individual button bodies and 25 cover XML structure, anchoring, other rows, preserved click actions and geometry.

## Limits and acceptance gate

This is a source candidate, not an installed fix. No release artifact was assembled or signed and no protected/accepted branch was edited. Kodi's compiled GUI focus, panel-layout scaling and real device behavior cannot be established by XML/static checks alone.

Before any separately approved APK release, the exact corrected skin must pass existing owner/module authentication, member-diff, permanent original-signature, version and forward-recovery gates. The user's physical Fold test should confirm Power stays visible at the bottom **on first open and after scrolling**, on both cover and inner displays/rotation, with all below-fold items accessible and correct Back/remote/touch behavior. Never mislabel unexecuted physical checks as PASS.

The distinct four-button direct-provider navigation correction remains a separate issue and is **not included** in this change.
