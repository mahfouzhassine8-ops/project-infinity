# Infinity 2103377 — RC5 source change and acceptance boundary

## User decision (authoritative)
Infinity's in-house **Resume Hub** owns watched state, Continue Playing and resume persistence. **Trakt is optional**: keep `script.trakt` installed, working, enabled if the user chooses, and freely updatable, without treating its own network sync or background service as an Infinity save-owner requirement. Trakt should receive a cooperative shutdown stop request when Infinity closes. **Do not modify, patch, disable, or uninstall Trakt.**

## Protected release baselines
Locked APK: **2103376**. Locked skin: **1.0.5.211**. Package: `com.projectinfinity.kodi`. No approved or installed baselines are changed in GitHub. RC3's early Python abort, owner-specific Playlist Browser Curl cancellation, early provisional local snapshot, RC4's 6.5-second dynamic recovery notice, and 274 Android regression cases all remain.

## Actual RC5 native implementation
New script `repairs/shutdown-rc5-2103377/optional_shutdown.py` patches only two native Kodi translation units **after** reconstructing the verified RC3 engine:

1. `xbmc/platform/android/activity/InfinityScriptCheckpointContracts.cpp`: a `script.trakt` **registered add-on ID** and exactly translated `script.trakt/default.py` launch path receives `stop-only:trakt-cloud-owned`. This is **not pinned to a Trakt source hash**, so Trakt may update ordinarily. All spoofed/unrelated add-ons fail closed. The raw skin Continuity path gets `stop-only:continuity-diagnostic` only for the approved skin's exact SHA-256 (**1.0.5.211** `a9a5477eec6ae1684d04d6b0a574be3f6b07172ca793240af82c8d26a421c9d1` or experimental **1.0.5.212** `97469b505ffae522b31a5bf96ef4313b2b184d1abd5937ee52b65dd7fe96599a`). Its trace is optional diagnostic history, not viewing progress.
2. `xbmc/interfaces/generic/ScriptInvocationManager.cpp`: **stop-only** invokers join the existing **native Close Request cooperative Monitor/Stop(false)** dispatch, but are not admitted into the unknown-writer checkpoint ledger. They are *not counted as persisted and do not have fake receipts*. Other unknown scripts still require true interpreter retirement and file/SQLite durability before Infinity's `python_services` owner can complete.

The original mandatory **17-owner** save sequence, Command Center, Resume Hub, provider/add-on APIs, database barriers, final `SAFE_TO_TERMINATE` authorization and Android Recents handling remain unchanged. No Trakt Python, account, credentials, skin ZIP or other add-on is repackaged. The RC5 Android build changes versionName only to label the test candidate, and reruns the 274 unchanged test cases.

## Important limit
This policy **does not guarantee** that an interrupted Trakt HTTP/scrobble operation reaches the remote Trakt server. Trakt operates normally while Infinity is ON; on Close it is cooperative best-effort only. A long-running optional Trakt interpreter may remain alive until Infinity terminates the process after the unrelated **17/17** local-first save authorizations. No automatic process kill or shortcut of local mandatory writes is introduced.

## Testing and status
- RC5 native workflow: `38514584184` initially stopped in a **new source assertion** (it expected three identical legacy guards; there are exactly two). Fixed only the assertion, not the native behavioral patch; corrected CI run `38515015273`.
- Fresh RC5 Android workflow: `38514680851`; all 274 Android tests passed, APK donor packaging still required a final green verification receipt as of initial report.
- Complete native compilation, signed RC5 APK, and **full-loaded Fold** Close → exit → reopen with **17/17 owner receipts** must be confirmed separately. Green CI is not physical proof. No RC5 lock/promote authorized by test results alone.
