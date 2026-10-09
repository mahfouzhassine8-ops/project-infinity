# Kodi 22 Piers vs Infinity 21.3 — selective shutdown forward-port review

**Source-only review branch. Not a build, release, approved lock, or fixed ANR.**
Base: `repair/infinity-python-exit-2103334` at `5fe46bf82bdab4e3a0f08af8aac9a8db64171810`.
Upstream comparison: Kodi 21.3-Omega vs Piers `6844af29cc7e05ebcf9e753342c43a7862db1b59` (2026-10-08).

## One reviewed forward-port candidate

`UPSTREAM-843ed46-StopPlaying.patch` is the narrow `CApplication::StopPlaying()` fix from [xbmc/xbmc commit 843ed46](https://github.com/xbmc/xbmc/commit/843ed46fc638b0623fd0d25e865e16f676f61273). It releases the GUI graphics and frame-move guards during `ClosePlayer()`, preventing the upstream-proven PAPlayer/script GUI-lock deadlock. It also reads active window after the player closes.

The current Infinity 2103334 native source-manifest SHA-256 for `xbmc/application/Application.cpp` is `e20467d13ceabdbf9634c9341e31e7ba96aa42172dc8941baed83111dcc080d6`. The complete exact native source is not committed here. Never blindly `git apply` this patch to a different source tree. The source-only companion package includes a fail-closed preimage/hash-checked applicator and tests. This branch stores the upstream patch for review, **not an applied production source change**.

Host tests completed for the companion package: 6 source-gate tests, one compiled C++ lock-cycle model, and a `git apply --check`/apply check against the exact Kodi 21.3 method fixture. These do **not** prove the actual generated 3334 source will match, native compilation, Android compatibility, or Fold acceptance.

## Explicitly excluded from this port

- Kodi 22 Android GLES teardown PR #28485: merged and then **reverted** by `42ef18c7d9df` on 2026-07-26; not a safe forward-port.
- Kodi 22 Python 3.14 thread-state/interpreter refactor: not a drop-in fix for Infinity's CPython 3.11.7 native/GIL modifications.
- `CScriptInvocationManager::Uninitialize` ranges refactors and `CThread::Join`: no demonstrated resolution of Infinity's unknown script-invoker target.
- `ApplicationMessenger`: Infinity 3334 already carries the reviewed late-request queue recheck; upstream Piers does not add an equivalent repair to transplant.
- Kodi `6332b0f9a7e` scanner cancellation before `CancelJobs()`: genuinely relevant, but Infinity 3327 introduced earlier `BeginShutdown()` before scanner cancellation. It needs an Infinity-specific ordering design/test, not a standalone literal cherry-pick.
- Kodi Omega Python circular-reference shutdown PR #25400 was merged in 2024, preceding Kodi 21.3, and must not be re-added.

The original PID 32099 last wait was inside native script-invoker final join, **not proven to be player closing**. No claim this patch resolves its five-minute ANR. No changes to skin, providers, playback core binary, resume state, persistence, accepted/rollback refs, application shutdown coordinator, or final joins.

**Required before application:** verify exact full generated source hash and patch preimage; review diff; compile on exact verified native lineage; test player + GUI script concurrency, folds/multiview, Kodi shutdown, and actual Fold close/reopen with retained state. Halt if any gate fails.