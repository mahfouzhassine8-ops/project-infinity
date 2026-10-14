# Infinity 2103377 — RC4 targeted shutdown handoff (unlocked)

Protected and untouched: APK **2103376**, skin **1.0.5.211**, package **com.projectinfinity.kodi**. RC3 native compiled SHA and 274-case Android green receipts remain authoritative; RC4 must not supersede them without an equal or stronger verification.

## What is actually known

- RC3 signed test candidate: GitHub run **38502916722**. RC3 native-green run **38498786704** and Android 274 tests **38495506871**. The signed candidate is not locked or approved based only on those host results.
- User's quick-close capture reportedly completed in **3.09 seconds**, with all 17 required save owners. Full-loaded close **still failed**, with Trakt and Infinity Continuity reportedly last.
- `CScriptInvocationManager::AndroidCheckpointUnresolvedWriters()` derives `unidentified:...` from **`!thread->GetAddon()`**; it does not identify the launch mechanism. `BeginAndroidCheckpoint()` already calls `NotifyScriptAborting(thread.get())` and `invoker->Stop(false)` for these generic scripts. Neither a direct `RunScript` launch nor an unresponsive `time.sleep` loop has yet been demonstrated.
- The exact `infinity_continuity.py` and `script.trakt/default.py` contents do not occur in the RC3 repository tree. Trakt's reported ~74.20-second retirement **does not prove** socket, JSON-RPC, or sync work without operation-level evidence. Do not modify unrelated add-ons or globally cancel Python networking.

## Actual RC4 source change on this branch

- Guarded Android notification only: first recovery advisory moved **2.5 seconds → 6.5 seconds**, after normal drain observed in the report.
- All `script_persistence.pending_writers` entries are examined; the current names/count replace first-entry-only assignment.
- While shutdown remains eligible, the displayed pending names are refreshed every second. A null/empty snapshot instead uses a non-accusatory message. Existing explicit Keep Waiting / Force Close chooser ownership is preserved; no automatic force exit.
- Matching 6.5-second gate in Splash; no changes to native checkpoint, Trakt or Continuity code, saved-state participants or termination authorization.
- Android re-verification: **GitHub run 38508366685**, triggered for 274 unchanged tests and the new UI source-contract checks. This run must be inspected; starting it is not a green result. This branch contains **no signed RC4 APK**.

## Required evidence before attempting the two runtime repairs

1. Latest **full-load RC3** diagnostic ZIP from the failing session, with session/timestamps, script persistence status and per-invoker trace. Do not reuse earlier RC2 or quick-close traces as causal proof.
2. The actual installed `infinity_continuity.py` file and where it is launched from; its filename is not proof that it is compiled into the APK. Check its main loop, blocking calls, checkpoints and how it saves state before adding abort responsiveness.
3. The installed Trakt add-on version/source plus a call/operation trace locating the 74.20-second delay (read-only request, JSON-RPC, synchronization, or persistent write). Do not cancel scrobble or watched-state writes. No blanket Python socket kills.
4. Preserve the **17/17 final owner receipts**, database seal and `SAFE_TO_TERMINATE` authority. Verify after a fully-loaded normal Close *and reopen* that progress, watched markers, Trakt, settings, favourites, providers, and all other approved features remain intact.

Do not claim two-service retirement success, the full-load shutdown repaired, or RC4 locked until the necessary device evidence and actual executable changes have been verified.
