# INFINITY — SAVED PROGRESS / PAUSED AT #6

**Requested by the user:** Save the work already completed. **Status:** PAUSED, no further implementation or build authorized by this savepoint.
**Saved on:** 2026-10-18.
**GitHub branch:** `work/infinity-post-2103384-feature-restoration`.
**Verified predecessor head:** `636749dc1d5007e425c156db6ae2a099185508b6`.
**Authoritative live tracker:** `repairs/four-repair-20261018/REQUIREMENTS-1-16-TRACKER.md`.

## Precise 1–16 completion

- [x] **#1 Player Rotate / Playback** — isolated skin 1.0.5.228 white/cyan corrections; targeted source/ZIP checks passed. Physical Fold and single-APK qualification pending.
- [x] **#2 Continue Playing** — original Command Center actions preserved; helper 0.1.1 stale state/data-loss reversal repaired; host tests/ZIP parity passed. Later helper 0.1.2 includes this repair.
- [x] **#3 Video Sources two-tap and hold** — mismatched add-on ID launch blocked in opt-in native path; compiled C++ regression/host run 39154244497 passed.
- [x] **#4 Video Sources exact context menu / Hide vs Disable** — helper 0.1.2 selected-ID/capability/confirmation guard passed 15 menu and 22 CC tests, run 39155208245; no Hide=Disable.
- [x] **#5 Blue watched / Resume Hub / Watchlist / Collection** — original presentation & native index preserved; Watched Bridge 1.0.1 stale popup intent guard, 47/47 host tests, run 39156538395. Prior Android native watched-row failures remain open in final integration, not rewritten as passes.
- [ ] **#6 Movie/TV Rails first-hold, correct Mocha options, black ghost popup** — existing Rails 0.2.6 Mocha path defect corrected in staged experimental Rails **0.2.7**. It is **not** a completed or approved release. **STOP AT THE BLOCKER BELOW**.
- [ ] **#7–16** — no implementation under this new sequential process yet; all original requirements remain mandatory.

**Count: 5/16 individually implemented/host-verified.** This is NOT 5/16 physical Fold-approved or a finished integrated APK.

## #6 work actually saved

**Repo source files:** `repairs/item6-rails-20261018/build.py`, `reference_build.py`, their focused tests and workflow; see commits `b03244dbfe7e2241eb6dde3c6ac1c4c5a9586fa8`, `9a85c137d3cd2fb281857beda5532ea9ffd4f337`, and tracker update `636749dc1d5007e425c156db6ae2a099185508b6`.

**Defect and correction:** The Rails 0.2.6 helper's `resources/lib/mocha.py` verified the approved Mocha XML in the skin but attempted to instantiate the custom dialog using the Rails add-on directory where that XML was missing. The experimental 0.2.7 proposal copies the exact approved XML into helper-owned resources and updates the dialog's path verification. Keep original safe Kodi fallback. Do not edit the user's Super Favourites plugin, keymaps, native input engine, Rails Store, data or Cobra.

**Provenance:** Original Rails 0.2.6 ZIP SHA-256 `5e4ff64592d6f8660d17db1077ed85a368c02f4eb14442760797b1d133c08179`. Source-only staged 0.2.7 candidate SHA-256 `e3b8614bc024d25159b64721ec5efe2b26b8c1bf0589dc03a0a33e7a9f02eddf`. GitHub Actions artifact **12148361418** `script.infinity.rails-0.2.7-Mocha-Options-TEST.zip`, 15 entries total (14 retained, 12 unchanged, 2 source files changed, 1 approved XML added, 0 deletions). Host run [39159573926](https://github.com/mahfouzhassine8-ops/project-infinity/actions/runs/39159573926) **GREEN** with 9 focused checks. Locked baseline check [39159819383](https://github.com/mahfouzhassine8-ops/project-infinity/actions/runs/39159819383) **GREEN**. Earlier run **39158974182** failed on draft-asset GitHub access; the later source used a hash-pinned Rails-only section verified independently, without adopting rejected APK 2103388 as a release base.

## STOP: required user authorization before finishing #6

**Conflict with completed #4:** `repairs/four-repair-20261018/addon/runtime.py` restricts `rails_supported()` to an **exact version 0.2.6** check. Replacing the Rails helper with version 0.2.7 without changing that predicate would silently hide #4's approved `Add to Infinity Rails` action.

**Do not change #4 while claiming it is untouched.** The minimal proposed compatibility adjustment is to accept only reviewed Rails versions 0.2.6 and 0.2.7 in that one eligibility predicate, then rerun #4 menu, #6 Rails and change-scope tests. **This has NOT been authorized or implemented. Await explicit user approval, or devise and prove an alternative that truly preserves all protected behavior.** #6 stays unchecked.

**Historical physical black-popup distinction:** The prior captured black rectangle involved installed Super Favourites global long-press mapping and a float-to-int menu position error. The Mocha resource correction alone does **not** prove that physical failure is resolved; the actual one-hold/black-panel Fold test is outstanding.

## Immutable preservation / final release rules

- **COBRA IS OFF LIMITS:** no Cobra code, assets, configs, dependencies or function changes, including shared-component regressions.
- Protect all completed #1–5 exactly; no unrelated feature, UI, skin, add-on, input, playback or shader modifications.
- Locked signed APK 2103384 SHA-256 `b571676731bb9bdccb25134c557be613e15cc9adaf77d6675dabc8e0586e54af`; preserve locked skin 1.0.5.223, user-installed .225, Diggz data, provider configurations, saved progress, signer and installed app state.
- Reject experimental 2103388 as a release due to its earlier Compatibility-service loss. 2103389 is an unsigned draft, NOT a finished verified APK.
- Do NOT build/ship a final APK until all 16 individual implementations are signed off, all binding instructions verified, and an exact one-APK install-over, Android17/API37, physical Fold (One UI9), genuine Close/reopen, data and Cobra functional preservation gate passes.
- **No reinstall, no clearing data, no fabricated pass, no baseline promotion, and no final lock without user approval.**

**Resume point:** User is paused at #6. Read this savepoint and the live tracker before taking any action. First resolve the #4-vs-#6 version conflict with explicit authorization; then test the actual Mocha/first-hold runtime. Do not restart #1–5.
