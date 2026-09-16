# Infinity Kodi upstream maintenance v1

**A lookout and a source-port laboratory, NOT an unattended application updater.**

The known working app is not on `main`: it is the specific RC3 APK paired with the
independent locked skin and Health Center. Never select the newest-looking branch
or any other APK called RC3. `baseline.json` pins the actual shipped artifact,
source commit and seven independently recorded final Android source hashes.

## What is installed

* **Kodi stable update watcher** runs daily at 11:37 UTC, on manual dispatch and on
  infrastructure changes on `main`. It checks official `xbmc/xbmc` releases,
  verifies tags resolve to full commit hashes, excludes drafts/prereleases/nightlies,
  compares versions numerically, and checks the pinned base tag for movement.
* New stable releases get disposable source analysis, a collision map, replay
  results, and one GitHub issue mentioning/assigning the repository owner.
  Closed issues are remembered: there is no daily repeated alert for the same tag.
  Normal GitHub notification preferences determine email/mobile delivery.
* **Source port lab** accepts a specific official release tag. Prerelease source
  analysis is possible only with explicit opt-in. There is no automatic beta adoption.
* **Infrastructure checks** test filtering, conflict handling and isolation, then
  reconstruct shipped RC3 on Kodi 21.3 and verify a same-base patch round-trip.

No workflow here runs Gradle, CMake builds, signing, installation, branch pushes,
merges, app updates, or lock promotion. The only automatic write is a notification
issue. A green workflow is NOT an APK compatibility certificate.

## Exact current baseline

* Kodi `21.3-Omega`, commit `a3a448d26b8d560a65655dab2cd122994dc4e146`.
* RC3 source `5f7d9b311568cca053d9c0e082463baca1bd99e0`, run `35071438615`,
  APK versionCode `2103138`. Use the full hash in `baseline.json` (including its
  final digit), not the historically truncated hash in a chat message.
* External skin **1.0.5.141**, Health Center **2.5.6**: fingerprinted and unchanged.
* Other companion versions are not fully inventoried in this lock. Capture the
  device's complete companion inventory before an actual migration; don't guess.
* Other concurrent RC3/UI-runtime branches are deliberately not merged or selected.

## How source migration works

1. Check out the exact pinned Infinity recipe in a fresh temporary directory.
2. Check out untouched pinned Kodi 21.3. Run the audited SOURCE transforms in the
   same order as RC3, but omit the native/Android build and APK packaging steps.
3. Capture eight independently identifiable patch stages, file owners, provenance
   and checksums. Verify seven golden source hashes from the shipped RC3 artifact,
   and rerun its existing late-callback lifecycle host regression tests.
4. Resolve the candidate Kodi tag through the official release record (not its
   mutable `target_commitish`). Recheck it immediately before source replay.
5. Compare complete local Git trees; there is no 300-file REST compare truncation.
   Renames show both old and new paths. Flag direct overlaps and broader API,
   renderer, player, toolchain, dependency, database and input risk domains.
6. Replay binary/full-index patches in order using three-way application. Stop at
   the first conflict; never force `ours`, `theirs`, fuzzy replacement or deletion
   of an upstream fix. Upload failure logs and identify remaining unapplied stages.
7. Clean textual replay produces **source only**, never an installable update.
   JSON and Markdown explicitly mark compatibility/build approval as pending.

The replayed source still contains old package/version metadata by design. It
must NOT be built/released unchanged and called a new Kodi-based Infinity.

## What still requires release-specific engineering

There is intentionally **no generic new-Kodi APK builder enabled in v1**. The
existing RC3 packager reuses a 21.3 engine and resources; using it for Kodi 22 would
be false versioning and potentially ABI-incompatible. A real engine upgrade needs
an actual build of that new engine with matched dependencies, resources and JNI.

For each target, review the impact report and create a release-specific build
adapter on a separate candidate branch. It must bind to the exact upstream SHA,
patch-series hashes and final candidate tree. It must:

* choose and pin compatible JDK/SDK/NDK/CMake/FFmpeg/Python/add-on dependencies;
* resolve each conflict without overwriting upstream fixes;
* verify native/Java JNI declarations, resources, manifest, package identity and
  signer; assign a deliberate, monotonic versionCode, not RC3's unchanged value;
* preserve or port all Infinity capabilities and run the existing test suites;
* test phone/Fold AND a TV using D-pad only; test Cobra handoff/PiP/Multi-View,
  lifetime races, pause/resume, Normal/Extended mode, all skin routes and companions;
* inventory binary/Python add-ons and check Kodi skin/window APIs;
* use an isolated candidate application/profile or a dedicated test device until
  acceptance. Do NOT update the user's sole working installation for a smoke test;
* make a complete user-profile/database backup before any in-place major upgrade.

A previous APK alone is NOT a guaranteed data rollback after database migration.
For a NEW engine, its native hash should change. Compare to the approved new build,
not the old `libkodi.so` hash. Keep the old artifact independently available.

Only explicit approval after build and device gates allows promotion. Changing
`baseline.json` is a reviewed release operation, never something the watcher does.

## Operation and limitations

GitHub schedules run only from the default branch. These files must be installed
on `main` to activate the daily check; merely opening a PR isn't enough.
Scheduled jobs can be delayed. Public-repository schedules may be disabled after
60 days without repository activity. Check Actions if the daily heartbeat stops;
no dummy commits/secret keepalive is used. API failures and exhausted pagination
fail explicitly; they are never shown as 'no updates'.

Run manually: Actions -> **Infinity | Kodi stable update watcher** -> Run workflow.
Read the last run's summary / `watch.json` for the last successful check time.
New-release GitHub issues link to the source impact report and artifacts.
Artifacts expire after 30 days; archive approved reports/patch series separately
for long-term retention. Source reconstruction uses pinned Git commits, not
expired Actions artifacts. The device-side app contains no new update menu.

## Local tests

```sh
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tooling/infinity_upstream -v
# Network, Git, patch, ImageMagick, DejaVu and javac are needed for the source proof:
python3 tooling/infinity_upstream/port.py --selftest --workspace /tmp/infinity-new-sandbox --out /tmp/infinity-proof
```

Reusing an existing workspace is rejected rather than deleting it. Temporary
source changes never get copied into the actual project or the locked ZIPs.

## Primary references

* Kodi source/build guide: https://github.com/xbmc/xbmc/blob/master/docs/README.Android.md
* Kodi dependency system: https://github.com/xbmc/xbmc/blob/master/tools/depends/README.md
* GitHub scheduling: https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows
* Releases API: https://docs.github.com/en/rest/releases/releases
