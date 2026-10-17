# Infinity-only Android validation — experimental gate, 2026-10-17

## What the old red tests really established

The historical Android probes installed `com.projectinfinity.kodi`, not the official
`org.xbmc.kodi` APK. They exercised Infinity's Android Essential-First Close
coordinator and packaged native engine, **but** ran a controlled startup
environment with synthetic add-on services and, in some paths, Estuary instead
of the real Infinity skin and the Fold's Diggz profile. Those results cannot
be equated with the physical phone configuration.

Locked, permanently signed **TEST4 2103377**, SHA-256
`bcdcbed5aeaed0bf30e6e590d9ceda7c0177d780b12e98773fa9503beb793286`,
had three Fold Close receipts with essential checkpoint saved and original
engine death. The historical Android fresh/loaded cases passed, cold and
core-initialized failed. The Fold receipts did **not** establish whole-package
death in every case. Preserve all of that evidence.

Signed **TEST3 2103382**, SHA-256
`6e28bfea7cdb5e497ee21601a714e738db7a57edc3c5c0d29a9c19d461031854`,
is still the *improved candidate*, not a replacement with TEST4. Its native
producer declared the TEST4 shutdown coordinator and write-admission source
unchanged. That declaration does not prove identical runtime behavior, nor
that the historical deadline problem was fixed.

## New Infinity-specific actual-APK path

- `infinity_only_gate.py` rejects official Kodi APKs, wrong signer, missing
  native engine, wrong version and mismatched APK digest.
- `infinity_full_stack_assets.py` requires the exact full 1.0.5.225
  `skin.infinity.diggz` ZIP, Rails 0.2.6 ZIP, original manifest requirements
  and approved Command Center / compat source. It refuses to substitute the
  reduced Estuary/Kodi rendering fixture or modify dependencies.
- `infinity_full_stack_android.py` launches signed Infinity on an isolated
  Android emulator, validates that actual Infinity skin loaded, retains its
  screenshot, and **now invokes Infinity's own Power Close** through
  `InfinityPowerControlActivity` after the integrated application loads.
- `infinity_full_stack_close.py` requires original Infinity essential
  write/owner/engine-death proof and separate full-package death and reopen
  evidence. It does not classify a stock Kodi exit or a failed checkpoint as
  success. Existing red startup-stress tests are never cleared or waived.
- `infinity-complete-full-stack-android.yml` contains two separate, pinned
  candidates: TEST4 is a **reference only**, TEST3 is the **current improved
  candidate**. Both see the same full 1.0.5.225 skin and Rails packages, so
  this specific comparison isolates signed native-app behavior. It does not
  reproduce the *historical TEST4 + skin .223* physical installation.
- A successfully loaded skin and a passing normal loaded Close do not
  demonstrate provider resume seeking, full Diggz-profile equality, Fold
  windowing, early-start Close, or universal release acceptance.

## What has been checked, and what has not

**Confirmed source checks:** GitHub 39071333534 passes real native protected
writes, strict full skin/Rails package rejection tests, source compilation, and
Infinity Essential-First receipt regression tests. No actual full-stack
Android execution is evidenced by that green host run.

**Missing before the full-stack emulator run can execute legitimately:**

1. The exact, already-hashed `Infinity-Full-Stack-CI-Inputs-225.zip` must be
   supplied to GitHub as the specifically named restricted Actions artifact.
   It is currently a Library/local file, not a GitHub Actions artifact.
2. The production skin's mandatory `script.skinshortcuts` 2.0.1-or-higher,
   `resource.images.studios.white` and
   `resource.images.recordlabels.white` packages need pinned, authentic
   sources. Do **not** suppress their `addon.xml` requirements.
3. A sanitized, provenance-checked representation of the phone's installed
   Diggz ecosystem would be required to claim complete Fold-environment
   equivalence. Never commit user profiles, credentials or 59 MB copyrighted
   skin/assets openly to the public source repository.
4. The current full-stack workflow is `workflow_dispatch` only on a
   working branch. It is **not yet an automatic, default-branch release gate**
   and cannot be counted as a successful Android run.
5. Full physical Fold shutdown, long-playback and version-specific features
   remain separate acceptance gates with explicit user authorization to lock.

**DO NOT:** switch to stock Kodi; rewrite original TEST4; downgrade TEST3;
disable protected-write barriers to manufacture green; label host or emulator
results as physical-device success; or lock APK/skin/helper without approval.

When the input artifact and dependencies are verified, run the full-stack
Android matrix and compare real loaded Power Close results. Then trace only
actual mismatches, retaining TEST3 enhancements and TEST4 as read-only
reference.
