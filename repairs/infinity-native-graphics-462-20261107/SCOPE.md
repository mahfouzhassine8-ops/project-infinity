# Infinity APK462 graphics: Android render/gesture lock-order prototype

**Status: isolated source candidate, NOT an accepted graphics repair, NOT an APK.**

Base protected source `86d5b5e2` remains unchanged. Keyboard candidate `92bb6ecb` remains unchanged. Search candidate `c75e6de6` remains unchanged. This branch adds only this repair folder and its isolated GitHub workflow.

## Physical fault and source-level race
APK462's touch path performs a synchronous `QuerySupportedGestures` query through the existing `GUIWindowManager::SendMessage`. This can invoke `SetScalingResolution` and reset `m_origins` on the touch thread. Meanwhile, the GUI frame render path explicitly releases the old graphics critical section in `CGUIWindowManager::Render` and uses `SetOrigin`/`RestoreOrigin`. Previously recorded host TSAN found this same stack race. Physical SIGABRT causation is not uniquely established.

## Scoped candidate
Instead of asynchronously marshalling a gesture-mask response across an unproven checkpoint queue/lifetime contract, keep the original **synchronous** gesture protocol and its original returned pointer ownership.

1. Add an Android-only recursive render/gesture mutex to the existing `CGraphicContext`.
2. Own it for the entire frame render after `CSingleExit` has released the old graphics critical section. Release it **before** that critical section is restored.
3. Own it on the Android `QuerySupportedGestures` path **before** entering `SendMessage` and its graphics critical section.
4. Keep the original `CGUIMessage` response mask and `delete` path byte-identical. No new message, borrow/heap protocol, queue, wait event, checkpoint pump, window callback or native touch action change.

Under these two observed paths, the lock order is `renderGestureGate -> graphicsCriticalSection`. A recursive gate permits the same-thread GUI reentry already supported by the frame loop. It is **not** authorization to add a lock to `SetScalingResolution` alone.

This is a **candidate** until source-matched host TSAN, real ARM64 compilation/full link, shutdown/checkpoint safety review and actual Fold checks establish feasibility. Other callers of graphics mutations and window-system teardown need explicit review before declaring the physical crash repaired.

## Locked preservation
The candidate patch is three files: `xbmc/windowing/GraphicContext.h`, `xbmc/guilib/GUIWindowManager.cpp`, and `xbmc/input/touch/generic/GenericTouchActionHandler.cpp`, plus prior native keyboard candidate `xbmc/guilib/GUIKeyboardFactory.cpp`. All other 9,407 original native sources must remain byte-identical to the exact signed APK462 source map. Non-Android source logic is unchanged. The original published pointer mask and checkpoint code are untouched.

No Cobra, Preview, Search provider source, skin, settings writers, persistence logic, add-on data, signed baselines, certificate, packaging, or installed APK is changed. No version is reused. No user test is requested here.

## Release gates
- TSAN host reproduction after patch must not report the prior origin-stack race.
- Exact Android ARM64 full native engine must compile/link with all source hashes bounded.
- Prior keyboard ASan and Search source results remain separate, not assumed rerun.
- Ensure no new deadlock, gesture regression, object lifetime, checkpoint/failure shutdown or concurrent rendering issue before promoting.
- The unrelated Search settings/ABA fail-safe remains a P0 blocker. Do not release an APK that falsely rejects valid results as a repaired final version.

**Evidence is not approval. If test fails, stop and preserve working baselines.**
