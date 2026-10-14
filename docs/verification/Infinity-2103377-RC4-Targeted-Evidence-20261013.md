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

Local packaged test candidate: **`skin.infinity.diggz-1.0.5.212-RC4-Continuity-Retirement-TEST.zip`**, SHA256 **0440a062162992562f1dfe1bc55aeb8dbe0a54c088bbeb3eff54c6d77f4c2bdc**.
Built directly from locked skin .211 ZIP; preserves byte-identical content in **2,976 of 2,978 ZIP entries**. Only `addon.xml` version/description and `resources/lib/infinity_continuity.py` changed. No UI/layout/theme/asset changes. It adds cooperative abort gates around the two read-only metadata RPCs and a final dirty trace flush/retry, without pretending to interrupt an RPC already blocked. Six **local mocked Python checks passed**: normal behavior, abort before metadata, abort between RPCs, no duplicate lock owner, trace preservation, and retry-on-error. Device exit time and 17-owner save acceptance remain unverified.

This candidate is NOT proven to make Infinity Continuity retire in 200ms and must not replace the locked skin without deliberate physical testing and approval.

## Trakt — root cause candidate, preserve scrobble writes

The upstream public `script.trakt` **3.9.0** source has an `xbmc.service` library named **`default.py`**, which calls `traktService().run()`. In `resources/lib/service.py`, `run()` uses a configurable startup `xbmc.sleep(startup_delay*1000)` and on shutdown calls an **unbounded `self.syncThread.join()`**. A running sync thread can therefore block main-service retirement even though `Monitor.waitForAbort(1)` was awakened. This is a concrete plausible root-cause path, NOT a diagnosis of the user's exact installed build or an observed Trakt stack trace.

Corrective action, after installed-version/source verification: place the service's startup delay on an interruptible Monitor wait; make read-only sync phases and their network requests cooperatively cancel on Close; let durable queued scrobbles and watched-state writes complete; then join a fully retired sync thread. **Never** replace the join with a short detached-thread timeout, blanket kill Python sockets, abandon writers, or fake persistence receipts.

## Acceptance gate

The complete RC4 requirement remains: fully loaded Close drains both final writers, yields **17/17** real owner receipts, database seal and valid `SAFE_TO_TERMINATE` authorization, exits the Infinity process safely, and reopens with watched/resume state, settings, Trakt, favourites, skin and providers intact. No production lock yet.
