# 2103223 onn. 4K Pro TV Hardening RC6

Protected rollback baseline: 2103221 — Infinity/Cobra onn. 4K Pro TV Remote UI RC4.
Immediate source parent: 2103222 TV Player / Multi-View RC5 (failed physical-device candidate).

This pass is strictly for the 32-bit armeabi-v7a TV variant. The ARM64 phone/Fold line and Kodi native engine are not modified.

## Physical-device failures

- Main TV Grid could not be traversed completely with the onn. remote.
- Player transport itself worked, but child surfaces opened by Channels, Display, Multi-View and More were effectively unusable.
- Startup / return transitions still exposed long black screens.
- UI remained visibly sluggish despite earlier focus work.

## Deep audit root causes

1. 2103222 stopped updating mCobraLastGuideWidth/mCobraLastGuideHeight. The guide-shell onLayout therefore treated every layout pass as a size change and called both cobraLayoutGuide() and cobraRenderGuideBrowser(). The latter destroys/recreates the browser and scans the channel set. Layout changes caused by those rebuilt children could feed the loop again.
2. The TV full-screen system-bar owner called requestLayout() on the decor/root/guide every time it ran. It is invoked from multiple lifecycle and player transitions, feeding the guide layout/rebuild problem.
3. Startup restored the saved channel-library JSON synchronously on the UI thread. The tested library contains about 20k channels, so parsing a potentially multi-megabyte JSON document and constructing every Channel/header map can block first presentation on ARMv7.
4. Display & Performance was hidden from TV settings, but the runtime still selected preferredDisplayModeId during player/open/close calls. That can trigger an HDMI display-mode handshake and a black frame even though this TV target is intentionally system/60-Hz owned.
5. Generic sheets/pickers had no single TV focus owner. Some opened with Close focused, some with list/search focus, and D-pad focus could escape into the player/guide behind them.
6. EPG installs from several sources independently refreshed labels, visible guide requests and full adapters. These bursts amplify UI work on the ARMv7 device.
7. Decorative list/panel motion still ran even though remote focus itself had been made immediate.

## 2103223 correction contract

- Layout passes reposition only; they never reconstruct the TV browser.
- Guide dimensions are tracked again and child LayoutParams are only replaced when bounds actually changed.
- Full-screen system bars are idempotent and never force a new layout tree.
- Saved library decode happens on Cobra's IO executor. A visible loading surface is shown immediately; cached channels are published to the UI once decoded while provider refresh continues in background.
- No preferred display-mode requests on this fixed TV target.
- All Cobra action sheets, player child menus, Multi-View picker, Display, More and Channels keep remote focus inside the open surface; Back closes exactly one layer and restores focus.
- Main TV Grid gains explicit Toolbar -> Group/Search -> EPG navigation routes.
- EPG UI refreshes are coalesced.
- Decorative child/panel animations are removed from this ARMv7 TV line; focus feedback remains immediate and visible.
- Programme/detail labels only mutate when their text/progress changed.
- Closing playback cannot trigger a full Cobra shell rebuild.
- Preserve the 2103222 player design and approved reversible Multi-View behavior.
- Preserve Live TV playback, providers, rewind/timeshift, recordings, Movies, Shows, My List, Smart Return, Health Center, package identity and permanent signer.

2103223 remains a TEST CANDIDATE until physical onn. testing passes launch -> guide -> menus -> preview -> player -> Multi-View -> return loops without black screens, lost focus or progressive slowdown.
