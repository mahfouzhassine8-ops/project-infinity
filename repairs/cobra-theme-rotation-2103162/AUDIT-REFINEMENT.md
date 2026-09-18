# 2103162 audit refinement

Parent: 3448904bd16e07d1e66f9a8bc6125eff41dc38ec. Locked baseline: 0ff8b5463ae6adf26ef0f20d64bc1b10f6c5a593 (2103161). Neither locked runtime nor HM 2.0.3 is replaced.

## Reproduced failure
The Run 12 evidence archive has one failing theme-roundtrip assertion. The same assertion fails locally: the persistent pointer switches to built-in, but a paused Robolectric clock prevents pending frame/publication messages from completing. Advancing bounded 16 ms frames, without skipping assertions or increasing the timeout, makes the roundtrip pass. See Robolectric 4.14 ShadowPausedLooper idle versus idleFor documentation.

## Actual defects found beyond that test
- The proposed Activity orientation requester duplicated the existing InfinityCobraDeviceBridge requester and its cached orientation. All requests now delegate to that one existing bridge.
- Resumed/terminal/fullscreen eligibility is explicit and remains enforced when the bridge processes a later policy/window callback.
- Fullscreen-to-preview releases orientation while retaining the same player and TextureView. Invalid Multi-View input no longer resets fullscreen orientation.
- Repeated built-in resets preserve the last installed snapshot instead of erasing its pointer.
- Visual-package installation refreshes the visible Settings status; new theme rows have stable roles and are themed after they are added.
- The existing unthemed drawer-header recovery manager remains available. The new normal Theme entry uses the same Settings control factory.

## Local verification before push
Exact 2103160 sources from the saved Android harness reproduced the locked 2103161 hashes, then the current 2103162 patch. Java compilation passed. The 46 inherited Android tests passed unchanged; 16 targeted Android UI/storage/device-bridge tests passed, with zero failures or skips. Hardening records 22 reversible edits and pins every final source hash to those tested locally. CI repeats compilation, signer/native/assets/resource checks, and all 62 Android tests before publishing any APK.

No Kodi C/C++ build, renderer edits, provider/EPG algorithm changes, credentials, system auto-rotate writes, or physical-device acceptance are claimed. The controlled player verifies no restart/release during the tested handoff; actual playback, Fold posture, OEM orientation behavior and real GPU surfaces remain device acceptance gates.
