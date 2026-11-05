# Bounded Info presentation and preserved behavioral failures

Exact signed 2103458 member: assets/addons/skin.infinity.diggz/unified/DialogVideoInfo.xml. Before SHA256 39bb6ad5c0b7c5a75da697e139b5c8b20622d94a63de17f041150d207d2650fb.

## Source correction

- Header Back button and its existing loading frame: width 4.791614% → 17.5%; MEDIA DETAILS left 8.2292% → 22%. The old 1080-wide layout left 7.75 logical pixels after its 44-pixel label offset.
- Existing poster and two cast image templates: aspectratio scale → keep. No new artwork source, metadata or control.
- Existing action group: width 54.6875% → 72%, height 58 → 72; its four button widths → 22.8% of the group. On a 1080-wide canvas this supplies 177.29 logical pixels per button with all four plus existing gaps fitting the group. No label/font/action changes.

All other bytes are compared to the signed member, including control IDs, onclick actions, loading notifications, theme variables, enablement and visibility. Five final focused source checks pass. Earlier before and intermediate evidence remains retained, including three initial failed expectations and the later action-width failure. These tests do not establish physical visual acceptance.

## Actual isolated Linux observations

The finite harness runs upstream Linux Kodi 21.2, original full skin assets and synthetic local metadata, with explicit responsive-coordinate projection because this is not the Android Infinity engine. It opens the actual native Info dialog, captures existing Dark/Light theme changes, and tests native Back/selection restoration. It does not invoke playback or application shutdown. Only its disposable processes/profile are used.

Initial attempts failed at fixture startup: the restored fixture's Disabled add-ons modal prevented directory activation. Subsequent harness handling acknowledges only that specific known notice, at most three times; any different notice fails. Those failed results remain committed, not converted into passes.

A further real failure occurred when selecting the skin's original Back control ID10: it opened DialogSelect instead of restoring the browser. The following separate native Action(Back) tests pass and do not waive the button failure.

## New behavior boundary: existing reserved control collisions

Frozen `xbmc/video/dialogs/GUIDialogVideoInfo.cpp` defines control10 as CONTROL_BTN_GET_THUMB; its OnMessage branch invokes OnGetArt. The signed skin uses ID10 for the visually labelled “‹ MOVIES” button with PreviousMenu. The Linux click reproduced the conflicting native artwork-selector action. Both the ID and native branch predate this correction. A visual-width change cannot correct native click ownership.

The same source inspection finds skin ID15 labelled TRAILER, while native ID15 is CONTROL_BTN_MANAGE_VIDEO_EXTRAS; native Trailer is ID11. No Trailer click/playback test was run here, so its actual Android outcome is unverified.

These are behavior changes outside the current strictly visual group5. No ID, native mapping or action was altered. A separately approved minimal skin-only control-contract repair would need to assign a nonreserved Back ID and update its loading/focus references, then reconcile Trailer/native IDs while retaining all existing conditional Stop and metadata actions. This is a boundary report, not an implemented patch. Native code need not be changed merely to conceal a skin/native ID conflict.

## Remaining visual limits

The cover portrait render still shows long-title truncation, oversized empty cast area when synthetic cast is absent and a tall original poster frame. The narrow action-label clipping was addressed by the second bounded geometry edit. Cast/season/episode/all-view rendering and physical Fold transitions remain pending. No claim of universal polish completion, exact approved-reference match or Android acceptance is made.
