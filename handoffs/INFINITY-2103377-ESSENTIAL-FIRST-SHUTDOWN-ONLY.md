# Infinity 2103377 — GPT-6 Extra High, Shutdown-Only Brief

**Authorization:** PROCEED on shutdown only. **Final lock requires explicit physical-device approval.**
**Repo:** `mahfouzhassine8-ops/project-infinity`
**Parent lock:** `locked/infinity-2103377-rails-handoff-rc1-20261015`, commit `7d3aca64b34d00520908cf4afd531a4687124525`.
**Locked APK:** `Infinity-2103377-Rails-Handoff-RC1-Signed-Test.apk`, SHA-256 `de8ce3f122db7bb8b2b3681e7c6ce9caf67cf38888b17ef1f82ff7759fa8a3db`.
**Preserve:** skin 1.0.5.223, installed Rails Helper 0.2.6, Mocha Rails, native Rails Handoff RC1, Python retirement RC1, all current approved features and user data.

## Mission: final exit authorization only

- While Infinity runs, preserve all normal Kodi playback, providers, add-ons, updates, Arctic Mirage, PiP, Trakt, Continuity, Resume Hub, and UI behavior.
- At **Power → Close**, stop new optional work; establish a protected-write barrier. Independently **verify durable essential saves**: Resume Hub, watched progress, favourites, settings, profiles, and required Kodi databases. Ensure optional workers cannot alter protected state after the barrier.
- Keep the existing **17-owner diagnostics and truthful per-owner receipts**, but make *final exit authorization* depend on verified essential durability, **not** retirement of every third-party Python interpreter, optional cache, or update.
- If essentials pass but optional Python workers remain, terminate the **whole Android process**, without destructive partial Kodi/C++ interpreter teardown. Record forced exit distinctly from graceful retirement. Never falsely mark unfinished third-party writes successful.
- If any protected write is dirty/unverified, report **essential-save failure** and do not claim safe completion. Do not assume Resume Hub covers every third-party setting or shared DB.

## Strict no-touch boundary

Change **only native shutdown authorization, essential-write barrier, or final Android termination code** required by the evidence. **Do not change** skin, helper, Rails, Movies/TV scheduling, Mocha, touch/GUI, provider Python, playback, UI, Resume Hub functionality, data formats, or any unrelated runtime. Never modify the locked APK; produce a separate permanently signed test candidate. No watchdog `SystemExit`, ignored save exceptions, or fabricated success receipts.

## Verification

Native host tests: essential save success/failure, a protected writer still active, hanging optional Python threads, direct process death, genuine vs optional save receipts. Full ARM64 compile, signing/cert/payload preservation. Physical Fold: quick, loaded, extended mixed-use Close, reopen, essential data intact, actual process death, no Rails regressions. **Never lock without user approval.**
