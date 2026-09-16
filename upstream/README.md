# Infinity Kodi Update Watcher & Source Port Toolkit — v1

**Delivery status: prepared locally, not deployed or running.**
This folder and the three `infinity-kodi-*.yml` workflows are GitHub infrastructure.
They are NOT an Infinity add-on, skin ZIP, firmware update, or installable APK.

## In everyday terms

The lookout checks official Kodi tags every day. A new stable-shaped source tag
creates a GitHub issue addressed to the repository owner. The workshop then
compares the new source with our known Kodi base and tries to carry Infinity's
changes forward in an isolated source copy. Conflicts are reported rather than
silently guessed away. The installed application never receives an automatic update.

## Exact baseline — do not choose a similarly named branch

- Repository: `mahfouzhassine8-ops/project-infinity`.
- Kodi: `21.3-Omega`, commit `a3a448d26b8d560a65655dab2cd122994dc4e146`.
- Delivered RC3: `infinity-lifecycle-repair-rc3`, commit
  `5f7d9b311568cca053d9c0e082463baca1bd99e0`, successful run `35071438615`.
- RC3 APK: versionCode `2103138`, SHA-256
  `202246685314324514ccd919a1521f187fdf6285c77d0622a2d481deb3aa7829`.
- Skin `1.0.5.141`: SHA-256
  `c300da2f1ba47e19d5fe0e0c9f4928a3ac046afe6d12afdce3d4200dd2e99ff9`.
- Health Center `2.5.6`: SHA-256
  `7988cc82ebe5bfd9346862bb13dc74ebb7107cbad8973efaa84a946a910b4101`.

The other similarly named RC3 branch and older RC2 branch are NOT substituted.
Separately developed newer runtime candidates are not silently promoted. When
another runtime is accepted, deliberately update the baseline, recipe, source
checks, source-file hashes and workflow checkout pin together in a reviewed change.
The current installed versions of all other companions must be exported and
recorded before a real engine migration; this toolkit does not invent that inventory.

## Included workflows

### `Infinity | Kodi Update Watcher`

Scheduled for **13:17 UTC daily**, plus manual Run workflow. The schedule becomes
active only after deployment to the repository's default branch (`main`) and
Actions is enabled. It checks official `xbmc/xbmc` tags, resolves annotated tags to
commits, and verifies the old pinned tag has not moved. It excludes alpha/beta/RC
names and GitHub Releases marked draft/prerelease. A GitHub Release 404 is
reported as **source tag only**, not as evidence of available Android binaries.

An issue is created once per new tag+commit, with an owner mention/assignment.
Closed issues remain acknowledged. A moved previously detected tag creates a
warning instead of automatically analyzing it. The newest newly announced target
gets a source-only analysis. Other new stable targets still receive separate
alerts and can be analyzed manually. If analysis fails after an alert, use the
manual analysis workflow to retry; the daily watcher deliberately does not spam
or recreate its issue. Check failures fail the workflow, not return 'up to date'.

GitHub notification delivery depends on account/repository notification settings.
This is not an in-app Infinity popup and not a scheduled ChatGPT message. There is
no guarantee of exact cron delivery. GitHub can disable schedules in public
repositories after 60 days without activity; check the Actions page and re-enable
if necessary. No fake keepalive commits are generated.

### `Infinity | Kodi Port Analysis`

Manual inputs: target tag, optional expected target commit. Default target
`21.3-Omega` is the installation acceptance/self-replay test, **not a new engine**.
The watcher can call the same workflow for a newly detected stable source tag.

1. Check out the exact delivered RC3 recipe, independently of the infrastructure
   branch. Validate every source file against the archived recipe inventory.
2. Download only pinned official Kodi source. Reconstruct the existing source
   via the same ordered, hash-gated transforms as the RC3 pipeline. No SDK,
   Gradle build, compiler invocation or signing step is run.
3. Export 11 ordered source-transform stages as binary-capable Git patches;
   inventory every changed/added/deleted file and its owner layer and hashes.
   Verify the published RC3 final Java/manifest/Gradle/CMake source receipts.
4. Compare the complete old/new Git trees (not a truncated API compare list).
   Report direct collisions and changes to renderer, input, playback, APIs,
   build/dependencies and database areas. No collision is not a compatibility proof.
5. Replay the patches into a disposable target worktree using Git three-way
   application. Stop at the first conflict/rejection; never skip a dependent patch
   and never weaken the original preimage gates.
6. For the same-base self-test, require an exact final Git-tree match. For a new
   target, export the clean candidate source/patches or a blocked conflict report.

A source archive is named **NOT-AN-APK**. It may retain old version metadata until
review; it is not a releasable application and must not be installed or promoted.

### `Infinity | Upstream Infrastructure Tests`

Offline regression tests on changes to the infrastructure's paths. Unit tests
exercise actual Git patch replay, binary changes, additions/deletions, conflicts,
non-overlapping upstream changes, >300-file diffs, numeric version ordering,
prerelease exclusion, notifications, moved tags and source baseline protection.
This job does not invoke any old native-engine workflow.

## Where automatic work stops

This v1 implements detection, notification, source comparison, ownership inventory
and source-only patch replay. **It does not implement an automatic APK build for
an unknown future Kodi version.** An engineer must review conflicts and provide
a target-specific build/toolchain adapter. That adapter must rebuild a coherent
native/Java/resource/binary-add-on set rather than transplanting a new `libkodi.so`
into the old APK. The RC3 Java-only repacker is not a Kodi-major-upgrade builder.

The old engine's hash is a baseline identity, not the required hash for a new
engine. Engine upgrades intentionally change native bytes; compare provenance,
JNI/API contracts and required features instead. Keep the old release intact.

A later compile must use an isolated candidate, have a forward versionCode and
verified signer, and pass real-device tests. Test on a separate device/profile or
reviewed separate package identity. A build in a separate Git branch is NOT by
itself safe to install over production userdata. Database upgrades may prevent a
simple APK downgrade. Back up actual userdata separately; source/APK backups do
not contain installed accounts, libraries, databases or provider configuration.

## Security boundaries

- No `contents: write`, signing secrets, automatic merges/releases/installations,
  or automatic baseline updates in these workflows.
- Only the notification job has `issues: write`; source analysis remains read-only.
- No `pull_request_target`, untrusted source execution or cross-host API redirects.
- Existing production scripts, workflow files, skin and companion ZIPs are not
  replaced by this package.
- Tag inputs are validated, passed through environment variables, and never
  interpolated into shell source.
- Actions use explicit releases; review and pin their immutable commit SHAs before
  enforcing a stricter organizational supply-chain policy. They are not represented
  as immutable commits in this v1 package.
- API and network failures require attention rather than fake success.
- Actions artifacts are time-limited evidence, not the only copy of a baseline;
  source reconstruction pins repository commits rather than old APK artifact IDs.

## Local tests

From the repository root:

```sh
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s upstream/tests -v
```

Python 3.10+ and Git are needed. Real source reconstruction additionally requires
network access, ImageMagick, `patch`, DejaVu fonts and an untouched checkout of the
pinned RC3 recipe. The GitHub workflow provisions only these source-transform tools.
The full reconstruction and live issue/scheduler run have **not** been executed
in the delivery session; do not mark deployment accepted until those pass.

## Primary technical references

- Schedule/default-branch/inactivity limits:
  https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows#schedule
- Minimum workflow permissions:
  https://docs.github.com/en/actions/tutorials/authenticate-with-github_token
- Releases versus tags:
  https://docs.github.com/en/rest/releases/releases
- Official Kodi tags:
  https://github.com/xbmc/xbmc/tags
- Recorded release baseline:
  https://kodi.tv/article/kodi-21-3-omega-release/
