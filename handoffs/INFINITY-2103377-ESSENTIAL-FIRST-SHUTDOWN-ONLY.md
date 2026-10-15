# INFINITY 2103377 — ESSENTIAL-FIRST EXIT / SHUTDOWN-ONLY BRIEF (REVISED)

**This supersedes the earlier shutdown-only brief. Documentation correction only; no runtime code edited.**

**Repository:** `mahfouzhassine8-ops/project-infinity`  
**Authorization:** PROCEED **only** on shutdown. Final candidate lock requires explicit user approval.  
**Exact base:** `locked/infinity-2103377-rails-handoff-rc1-20261015`  
**Lock commit:** `7d3aca64b34d00520908cf4afd531a4687124525`  
**Approved APK:** `Infinity-2103377-Rails-Handoff-RC1-Signed-Test.apk`  
**SHA-256:** `de8ce3f122db7bb8b2b3681e7c6ce9caf67cf38888b17ef1f82ff7759fa8a3db`

**Preserve unchanged:** skin 1.0.5.223, installed Rails Helper 0.2.6, Mocha, Rails Handoff RC1, Python Retirement RC1, providers, playback, PiP, Trakt, Continuity, Arctic Mirage, all approved features and user data.

## One mission: Power → Close, nothing else

1. **When Infinity is running, change nothing.** Keep normal Python providers, scripts, updates, screensaver, playback, and startup behavior. **No maintenance control center, scheduling changes or third-party Python modifications.**

2. **On Close, save only verified essentials as mandatory.** Reject new optional work **without blocking first-party save handlers or essential background jobs**. Independently verify durability of Resume Hub, watched position/progress, favourites, Infinity/Kodi/skin settings, profiles, playback checkpoint, and required Kodi databases. Essential first-party Command Center/compatibility Python save participants remain protected. Protect essential files and transactions against subsequent or concurrent writes through process death. A third-party write to a shared protected database **cannot** automatically be classified as optional.

3. **Change the complete shutdown path, not just the last check.** The locked source's `InfinityAndroidCheckpoint::Pump` stage 4 currently waits on foreign Python retirement **before** stage 5 settings/database saves. Remove that optional dependency **upstream of essential saves**, and remove it from final native authorization. Distinguish optional versus essential jobs. Keep any active Android-side receipt validator, owner-bound PID/session identity, generation, seal and deadline checks consistent. Preserve every essential write proof.

4. **Optional retirement never vetoes exit.** Third-party interpreter retirement, provider caches, metadata/EPG refreshes, repository updates, and full interpreter-by-interpreter cleanup are **not mandatory**. Do **not** wait out a new grace period, optional `Stop(true)` escalation, join, or callback timeout. An optional cooperative stop request may be sent without waiting. **Once essential writes are durably verified**, terminate the **whole owning Android process**; do not run partial Kodi/C++ teardown against live Python threads.

5. **Keep the full 17-owner ledger truthful, not a 17/17 fiction.** Optional owners may be `UNFINISHED` / `FAILED` without blocking *essential* authorization. Label essential-verified forced process exit separately from full graceful all-owners exit. Do not claim optional saves, interpreter retirements, or confirmed PID death merely because an exit was requested; require actual Android/owner-lease death evidence. Preserve accurate failure details.

6. **Protected-save failure still fails authorization.** If an essential file, shared write, database transaction, protected writer, or seal/readback is unverified, report the exact blocker. Never bypass it or manufacture safe close. Optional third-party in-flight caches, settings or databases **may be lost or corrupted** by forced exit; Resume Hub does not protect their data, and recovery is not guaranteed.

## Strict no-touch

Only the *shutdown* state machine, protected-write admission/barrier, essential-versus-optional owner receipts, final exit authorization, and directly required native/Android termination protocol may change. **NO** Rails, Mocha, skin, helper, Movie/TV startup, touch/GUI, provider files, normal app startup, playback behavior, Resume Hub UI/semantics, settings behavior, database schema, or unrelated code. Locked signed APK remains byte-for-byte intact; use a separate permanently signed test candidate with rollback. **Never** add async `SystemExit` watchdogs, swallowed exceptions, fake save receipts or unsafe partial interpreter destruction.

## Evidence gates

Source-diff/hash preservation; essential save good/bad paths; first-party Python save callback; active protected writer and SQLite transaction; indefinitely hung optional worker; optional write exception; native/Android validation agreement; actual process death and data-preserving reopening. Full ARM64 build and signing. Physical Fold: quick Close **and** Close after ordinary extended mixed use, app-switching/screensaver cycles, saved watched/settings/favourites, and Rails regression check. **No arbitrary one-hour viewing prerequisite; no promotion/lock without user approval.** If the essential barrier cannot be proven, report the blocker—not a broader redesign or a bypass.
