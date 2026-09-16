# Infinity Kodi upstream maintenance v1

**A daily lookout and a source-port laboratory, not an unattended app updater.**

## Daily operation

The **Kodi stable update watcher** runs at 11:37 UTC daily, on manual dispatch,
and on infrastructure updates on `main`. It reads official `xbmc/xbmc` releases,
checks numeric versions, resolves the release tag to a full commit SHA and
rejects drafts, alpha/beta/RC releases and nightlies. A changed pinned tag is an
error requiring investigation, not an update silently accepted.

A new stable release gets a disposable source comparison and patch replay.
The result produces one notification mentioning `@mahfouzhassine8-ops` in the
conversation of **maintenance PR #6**, including a link to the analysis run.
This repository has Issues disabled. PR conversation comments work without
changing that administrative setting. Alerts continue after PR #6 is merged.
Keep that discussion unlocked and retain its Actions-owned comment markers.
Only Actions-owned comments suppress duplicates; unrelated comments cannot.

The first successful watcher run posts a clearly labelled **setup confirmation**
once. That is not a new Kodi update. Normal GitHub account notification preferences
determine email/mobile delivery; there is no new in-app update popup.
Network/API/pagination failures fail visibly rather than reporting no updates.
Ambiguous POST failures are not retried blindly; the next run checks history first.

## Exact protected app

`baseline.json` pins Kodi `21.3-Omega` at
`a3a448d26b8d560a65655dab2cd122994dc4e146`, the shipped RC3 source at
`5f7d9b311568cca053d9c0e082463baca1bd99e0` (run `35071438615`), external
skin **1.0.5.141**, and Health Center **2.5.6**, including full artifact hashes.
The current app source is NOT the older `main` branch. Other branches also called
RC3 are not substitutes. The real RC3 APK hash ends in `829`; an earlier chat
message accidentally omitted its final digit. Use the full manifest hash.
Other companion versions are not fully inventoried here. Capture the target
device's complete companion inventory before an actual migration; do not guess.

## Source-port process

1. Check out clean pinned Kodi 21.3 and the exact pinned RC3 recipe into NEW
   temporary directories. Existing workspaces are rejected, never deleted.
2. Run only that recipe's source transforms in the original order. Capture eight
   full-index/binary patch stages with checksums and file ownership. Check the
   seven final Android source hashes against the shipped RC3 artifact and run its
   existing late-callback lifecycle host tests. No native/APK build is invoked.
3. Compare complete local upstream Git trees, not a potentially truncated REST
   file list. Renames retain both old and new paths. Report direct overlaps and
   broader renderer/player/JNI/API/toolchain/database/input compatibility domains.
4. Replay patches into a disposable candidate worktree. Stop at the FIRST conflict.
   Never automatically choose ours/theirs or erase an upstream fix to pass a gate.
5. Clean replay yields SOURCE ONLY. A clean patch is not a compatibility certificate.
   Same-base infrastructure verification requires exact source-tree round-trip.

Outputs include `impact.json`, `ownership.json`, `patch-series.json`, patches,
receipts, logs and `SUMMARY.md`. A successful replay also produces a source ZIP.
That ZIP still contains OLD package/version metadata and must not be released
unchanged as a new Kodi-based Infinity.

The **manual source port lab** accepts an exact official release tag, never a branch.
Prerelease analysis needs explicit opt-in and remains source-only.

## Actual upgrade gates -- deliberately not automatic

There is **no generic new-Kodi APK builder enabled in v1**. The RC3 Android-only
packager reuses the old Kodi engine; it MUST NOT be used to claim an engine upgrade.
For each new target, a reviewed release-specific build adapter must bind the exact
upstream SHA, patch hashes and final source tree. It must select/pin the appropriate
JDK/SDK/NDK/CMake/dependencies, resolve conflicts, compile the NEW native engine,
verify matched JNI/resources/manifest/signer, assign a deliberate new versionCode,
and run the existing test suites. For a new engine its hash SHOULD change.

Device acceptance includes phone/Fold AND TV remote-only use, playback/audio/subtitles,
Cobra handoff/PiP/Multi-View/lifetime races, rotation/resume, Normal/Extended background,
skin navigation/System Hub/Power, Health Center and Python/binary add-ons.
Use an isolated candidate app/profile or dedicated test device, not the user's sole
working installation. Back up the complete user profile/databases before any major
in-place upgrade. An old APK alone does not roll back migrated databases.

No workflow here builds/signs/installs APKs, pushes source branches, merges app
changes, or promotes the locked baseline. The only automatic write is a notification
comment in PR #6. Baseline promotion requires explicit approval after acceptance.

## Scheduling and recovery

Schedules run only from the default branch, so merge this infrastructure into `main`
after its own checks pass. Opening a PR alone does not activate the watcher.
GitHub may delay scheduled runs or disable public-repository schedules after 60 days
without repository activity. Check Actions if the daily heartbeat stops; no dummy
commits or keepalive tricks are used. Workflow artifacts expire after 30 days;
archive approved migration evidence separately. Reconstruction uses pinned Git
source commits rather than expiring Actions artifacts.

Manual check: Actions -> **Infinity | Kodi stable update watcher** -> Run workflow.
The summary and `watch.json` give the last successful check time and stable version.

```sh
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tooling/infinity_upstream -v
# Network, Git, patch, ImageMagick, DejaVu and javac are needed for the source proof:
python3 tooling/infinity_upstream/port.py --selftest --workspace /tmp/infinity-new-sandbox --out /tmp/infinity-proof
```

Primary references:
- https://github.com/xbmc/xbmc/blob/master/docs/README.Android.md
- https://github.com/xbmc/xbmc/blob/master/tools/depends/README.md
- https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows
- https://docs.github.com/en/rest/releases/releases
