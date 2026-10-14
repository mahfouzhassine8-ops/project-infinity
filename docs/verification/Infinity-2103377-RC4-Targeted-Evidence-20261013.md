# Infinity 2103377 — RC4 targeted shutdown evidence (unlocked)

This is a targeted implementation and evidence record, not a shipping acceptance.
Protect unchanged **APK 2103376**, **skin 1.0.5.211**, package **com.projectinfinity.kodi**, RC3's green native engine, and all persistence/termination authority.

## Verified checks

- RC3 signed test artifact is run **38502916722**; native full build **38498786704**, 274-case Java receipt **38495506871**.
- RC4 notification repair compiled, tested, and verified: **GitHub Actions 38508366685, success**, including the **274 unchanged Android tests**. It changes only the generated Android Java recovery notice and Splash eligibility, not the native save barrier.
- Recovery notice now waits **6.5 s**, checks all *current* `script_persistence.pending_writers`, displays actual remaining services and count, refreshes once per second, and never auto-force-terminates. Source contract checks passed.
- The RC4 branch contains no signed RC4 APK. The RC4 Continuity-only candidate skin is a separate local ZIP requiring device testing and is NOT the approved locked skin.

## Real Fold diagnostics — current session evidence

Two existing user Library exports were inspected by exact filename. Do not conflate these sessions or earlier RC2 traces.

- **`Infinity-Diagnostics-20261013-231759.zip`**: quick Close ~**3.09 s**, mandatory **17/17 owners** completed, native authorization and normal completion reported; 37 writers retired.
- **`Infinity-Diagnostics-20261013-233546.zip`**: full load ~**64.0 s** after process start before Close; checkpoint **FAILED at ~25.1 s**. Only playback, Command Center, compat, and PVR had finished; remaining 13 owners were not finalized. Two writers pending: `script.trakt:default.py` and `unidentified:infinity_continuity.py`. This capture supplies NO 17/17 final receipt and no authorized termination.
- Untruncated `shutdown/critical.jsonl` specifically confirms `script.trakt` invoker **26** returned Python bytecode **+74.136 s** after Close and interpreter retired with a durability receipt **+74.171 s**. Native VFS return entries ~+0.046 s do not identify the Python call that held it for ~74 s. A Python socket timeout or read-only library sync is plausible but NOT proven.

## Infinity Continuity — the actual source and launch

The locked, fully preserved skin ZIP **`skin.infinity.diggz-1.0.5.211-Compact-ZIP-Preview-RC1.zip`** contains exactly:
- `skin.infinity.diggz/resources/lib/infinity_continuity.py` (223 lines, original SHA256 **a9a5477eec6ae1684d04d6b0a574be3f6b07172ca793240af82c8d26a421c9d1**)
- `skin.infinity.diggz/unified/Home.xml`: `RunScript(special://skin/resources/lib/infinity_continuity.py)`

That *does* confirm the raw launch behind the native `unidentified` tag. Contrary to the initial theory, it ALREADY calls `xbmc.Monitor().abortRequested()` and `waitForAbort(.1 or .5)`; there is no `time.sleep` busy loop. It does perform **two synchronous Kodi JSON-RPC requests** for screensaver identity and writes a short content-free `continuity.json` trace periodically. The current runtime capture does not tell us whether it was inside either RPC at Close.

### Isolated Continuity candidate (not yet a shutdown fix)

Local packaged test candidate: **`skin.infinity.diggz-1.0.5.212-RC4-Continuity-Retirement-TEST.zip`**, SHA256 **7f26593ff5f1c2bd8d9efa1a0fe3ef0f7b3d400ec165e373a143d71efe2c67d4**.
Built directly from locked skin .211 ZIP; preserves byte-identical content in **2,976 of 2,978 ZIP entries**. Only `addon.xml` version/description and `resources/lib/infinity_continuity.py` changed. No UI/layout/theme/asset changes. It adds cooperative abort gates around the two read-only metadata RPCs and a final dirty trace flush/retry, without pretending to interrupt an RPC already blocked. Six **local mocked Python checks passed**: normal behavior, abort before metadata, abort between RPCs, no duplicate lock owner, trace preservation, and retry-on-error. Device exit time and 17-owner save acceptance remain unverified.

This candidate is NOT proven to make Infinity Continuity retire in 200ms and must not replace the locked skin without deliberate physical testing and approval.

## Trakt — root cause candidate, preserve scrobble writes

The upstream public `script.trakt` **3.9.0** source has an `xbmc.service` library named **`default.py`**, which calls `traktService().run()`. In `resources/lib/service.py`, `run()` uses a configurable startup `xbmc.sleep(startup_delay*1000)` and on shutdown calls an **unbounded `self.syncThread.join()`**. A running sync thread can therefore block main-service retirement even though `Monitor.waitForAbort(1)` was awakened. This is a concrete plausible root-cause path, NOT a diagnosis of the user's exact installed build or an observed Trakt stack trace.

Corrective action, after installed-version/source verification: place the service's startup delay on an interruptible Monitor wait; make read-only sync phases and their network requests cooperatively cancel on Close; let durable queued scrobbles and watched-state writes complete; then join a fully retired sync thread. **Never** replace the join with a short detached-thread timeout, blanket kill Python sockets, abandon writers, or fake persistence receipts.

## Acceptance gate

The complete RC4 requirement remains: fully loaded Close drains both final writers, yields **17/17** real owner receipts, database seal and valid `SAFE_TO_TERMINATE` authorization, exits the Infinity process safely, and reopens with watched/resume state, settings, Trakt, favourites, skin and providers intact. No production lock yet.

## Oct 14: installed Trakt source found and repaired locally (experimental)

A user-owned archive `Infinity-Installed-Addon-Code-20261008-071505.zip` contains **Trakt 3.9.0** code with a customized `AM Lite` wait located at the *import time* of `resources/lib/service.py`. This code loops for up to **120 seconds** using `xbmc.sleep(1000)`, without a Kodi abort check. The same source contains a non-time-bounded `syncThread.join()` during shutdown. Both are real source-level shutdown impediments. The 74.2-second physical retirement interval does NOT distinguish which one executed in that session. The Oct 8 archive is not proof that the exact source was still installed on Oct 13.

A **manually invoked, version-and-hash-guarded Kodi program add-on test repair**, `script.infinity.trakt.rc4patch-0.1.0-TEST.zip`, was assembled locally. It does not automatically patch on installation: it offers Apply/Restore via a confirmation dialog, and acts only on installed `script.trakt` version `3.9.0` when the two source hashes match the Oct 8 observed copies. Original files are backed up with verified hashes, replaced atomically, and the test repair can restore those originals. No Trakt user settings, API tokens, databases, watched-state data, or skin files are included or changed. It is **not a replacement `script.trakt` package**.

- service.py source SHA-256: `867f7ad8a4013c5052efdcf0a23c29c48a63ddaff0298bb46650c1eb026f6f7d` → `bc00a34bf028a6ad97b75ee811eaa63883e36481c0adf37aeb52e7f8c0d4e5a5`
- sync.py source SHA-256: `6dfb162ed42740fe1553a585ac9609ade481b907e726d9b179060c1ecf65e2c9` → `14f9fcd7d2d7ded40cb27b3f8f6cc348454fd56da79173a72d41b72a85979249`
- Patch: move Account Manager wait out of module import; register `traktMonitor` before startup waits; use `waitForAbort(1)` to stop immediately when Close arrives; retain 120-second fallback and 180-second freshness check during normal operation; use abort-aware existing startup delay. On active library sync, request cancellation for *new* optional sync stages via its existing `IsCanceled()` checks. **Keep blocking `syncThread.join()`** so actual in-flight state writes are not discarded.
- Targeted host verification: **27/27** real-source-AST mocked Trakt tests, **17/17** temporary-file patcher apply/restore/fault-recovery tests. No physical Fold test, no proof of cancelling an in-flight 90-second HTTP read or write, no permitted termination bypass.
- Preserve Trakt 3.9.0 add-on resources/assets and all user settings. The Oct 8 code snapshot is incomplete as a standalone installable Trakt ZIP, so it was **not** released as a replacement add-on. Only the reversible, preimage-pinned repair add-on is suitable for testing when the installed code matches.

Separately, the locked **skin 1.0.5.211** code was reviewed. `unified/Home.xml` launches `infinity_continuity.py` via raw `RunScript`. That script already used `xbmc.Monitor().waitForAbort(.1/.5)`; the experimental **skin 1.0.5.212** only adds abort checks surrounding optional screensaver JSON-RPC reads and a final dirty-trace flush. Isolated host tests **6/6 passed**. An already-blocked JSON-RPC call cannot be interrupted by that skin patch.

## Test build activity

- RC4 Android 6.5-second/dynamic recovery UI: **274/274** passed, run `38508366685`.
- Signed APK integration workflow: `38512236135` (look up its conclusion; it was queued at writing). The native engine donor remains RC3 run `38498786704`; the Java donor is run `38508366685`. Signed APK is not an add-on auto-installer and does not silently modify Trakt or skin.
- Locked APK **2103376**, locked skin **1.0.5.211**, and approved rollback files remain unchanged. The RC4 skin/Trakt/Android candidates are not production locked. Physical test must verify full-load Close and **17/17** final receipts, clean process exit and progress intact upon reopen.
