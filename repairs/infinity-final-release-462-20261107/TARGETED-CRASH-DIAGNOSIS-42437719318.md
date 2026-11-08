# Infinity 2103464 Android17 — actual crash diagnosis, isolated follow-up

## Scope and authorization
Records and QA-only changes. Exact signed 2103462/464/465 APKs, native libkodi, Cobra, skin, Command Center, external Umbrella/POV/Nixtoons, standard Movies/TV and Infinity Trakt remain **untouched**. No installation or acceptance is implied.

## Reuse proven evidence, no blanket rerun
- Passing Umbrella/POV host branch: `locks/umbrella-pov-native-search-host-pass-20261107` pointing to `16af10e42265f9f5155efd54849b25871c50aa0f`.
- Passing host run `42435806833`, archived artifact `13598889647` (NOT-APK).
- Android source commit `152ae1bed123894af9669640edd2f6508cd80996`, run `42437719318`, artifact `13601500225` (`FOLD-PENDING`).
- Verified Android gates recorded in `ANDROID-VERIFICATION.json`: exact signed upgrade preserved UID/data and 78 module hashes; four front/inner light/dark observations; seven completed Search cycles and first Umbrella heading activation. These are checkpointed in `locks/infinity464-reuse-passed-gates-20261107`.
- The next TV search `SpongeBob` displayed an Umbrella heading with 7 results and WatchNixtoons2 with 1. A `select-row` request to open the Umbrella heading (request seq 192) received no reply during the 160-second deadline.

## New decisive findings in existing crash evidence
- This was **not** only a GitHub false-negative or a slow provider. `release-android-results/LOGCAT.txt` records `Fatal signal 6 (SIGABRT)` at `2026-11-08 02:36:12.944 UTC` for `com.projectinfinity.kodi:kodi` (PID 4925, thread 5135). The system confirms the process died at `02:36:14.408 UTC`; the final screenshot shows Android home.
- Tombstone abort message: `Scudo ERROR: invalid chunk state when deallocating address ...`. This is a native allocator-state violation; it is consistent with invalid/double-free or a related memory-lifetime error, **not** by itself proof of a particular application-line defect.
- ARM64 translated stack includes `CGUIListItem::~CGUIListItem`, `CGUIInfoManager::GetMultiInfoLabel`, `XBMCAddon::xbmc::getInfoLabel`, and Python invoker frames; crash occurred while a background Python invocation was retrieving live GUI list info. The test also logged `Control 50 in window 10025 has been asked to focus, but it can't`.
- The test runner's last displayed error `Timed out: selected select-row; None` concealed the earlier crash because it polled `reply.json` after the app died. The former `controller_access` import issue from run `42435881141` is *not* this crash.
- **Cause not yet established:** This could be a verifier-induced UI lifetime race or a defect reproducible through normal user navigation. Do not label it either one as fact.

## Narrow completed QA correction on this diagnosis-only branch
- `verify_android_release.py` `Device.command` now calls `self.alive()` before each selected-action reply read. Its existing PID check raises an uncaught assertion if the native engine died; that should stop polling immediately rather than burning the entire 160-second action timeout. No signed APK/source runtime changes.

## Next technical step (targeted; no full 30-minute rerun now)
1. Analyze request 192 and crash stack together, focusing on the test's use of `Container.SetViewMode(50)`, `SetFocus(50,index,absolute)`, `Container(50).ListItem.FileNameAndPath`, and the `Input.Select` call while the Search All list may be invalidating/rebuilding. Ensure test reads do not outlive live list objects or cross unsafe GUI-thread boundaries.
2. Design a **minimal isolated replay** on the *exact* signed app, one TV Search All `SpongeBob` heading activation, with crash/tombstone capture and process-PID monitoring. Do not replace native provider searches, disable checks, or relabel untested behavior as PASS.
3. Only if the same native allocator failure is shown to be a genuine user-path defect, propose a minimally scoped production repair and separately request approval. Do not modify Cobra, unrelated native engine components, signing identity or existing behavior.
4. Retain independent unverified release gates (remaining Search cycle, watched/UI/Info/Downloads, real Fold manual acceptance, signed forward recovery) until verified or explicitly revisited. Source/host PASS is not final Android acceptance.

The goal is to stop unnecessary repeated verification, preserve genuine PASS, and avoid distributing a potentially crashing ZIP/APK.
