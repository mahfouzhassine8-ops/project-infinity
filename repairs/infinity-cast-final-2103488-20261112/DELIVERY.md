# Cast-only signed QA and forward recovery

**QA 2103490 is an engineering candidate. Physical Fold/TV acceptance is pending.**
The exact development APK is original-signed 2103488, SHA-256
`4217b217bca06084121572bbde71164abe67d05ef49741c78d4f83c5c5d4a566`.
Protected 2103486 and the existing signed artifacts remain unchanged.

| Download | APK inside the artifact ZIP | Source commit |
|---|---|---|
| [Cast QA 2103490](https://github.com/mahfouzhassine8-ops/project-infinity/actions/runs/43325382217/artifacts/13992273256) | `Infinity-2103490-Combined-Original-Signer.apk` | `d311f22ddd30d3c7313a3f8f009c8f8a8e3325cd` |
| [Forward recovery 2103491](https://github.com/mahfouzhassine8-ops/project-infinity/actions/runs/43326721200/artifacts/13993745514) | `Infinity-2103491-Combined-Original-Signer.apk` | `9ad36336b23c91d45de7dec8d45a192a2702868d` |

Download the artifact ZIP and extract its APK. GitHub may require sign-in.
The hashes below apply to the extracted APKs, not the ZIP archives.

```text
63b1e380d9ff079e47793b0a182725561a9265cd63a0de288fc8357dfb1d7733  Infinity-2103490-Combined-Original-Signer.apk
78af2c811e471007ef4e2280b0f4c65050020656bd226425997ebfc7128562c0  Infinity-2103491-Combined-Original-Signer.apk
```

Both use package `com.projectinfinity.kodi` and the original 4096-bit RSA
certificate SHA-256:
`d7adeb68e9341596a02bd3262b737a0f45fc6e771ed7e60285437e833b58c6d7`.
Actual `apksigner` verification passed v1, v2 and v3 for both APKs. The sole
original signing workflow **397702717** signed them; no replacement key or
signing implementation was introduced. Registry generations are 75 and 76.
Neither signing operation promotes an accepted baseline.

## Implemented Cast changes

- Sender-side progressive, HLS and DASH delivery, including rewritten adaptive
  manifests, relative URLs, registered renditions/init/segment/key endpoints,
  byte ranges and authenticated source requests. Provider URLs, cookies and
  private headers stay on the sender. Source response cookies use bounded,
  origin-scoped RAM and are retired with the transfer.
- Explicit video-receiver selection automatically prepares and loads media.
  Phone playback continues during preparation. Only actual receiver PLAYING
  establishes Now Casting. An optional existing tracking acknowledgment does
  not block media loading; remote progress requires that acknowledgment.
- Compact cyan-accent controls with existing theme lookup; inactive transports
  hidden, labeled position/seek, Pause/Resume, separate Close Controls and
  Return to Phone / Disconnect. Both existing entry-point locations remain exact.
- Source-bound return to the existing phone player; failure/end/cancel paths
  retire owned media delivery, callbacks, clock channel and native RAM state.
  A failed pre-handoff transfer does not rewind untouched phone playback.
- Credential-safe stage/status diagnostics. No shutdown, persistence or provider
  implementation is changed. Cleanup corrections do not establish the exact
  cause of the owner's earlier shutdown checkpoint failure.

See [SOURCE-CHANGES.json](SOURCE-CHANGES.json) for each production file's before/
after hash and [REPAIR-AND-PRESERVATION.md](REPAIR-AND-PRESERVATION.md) for the
individual source corrections and retained historical failures.

## Preservation

The signed QA comparison against exact 2103488 passed. Exactly four existing
payload members changed:

1. `classes6.dex`: isolated Cast implementation/private SDK subset.
2. `lib/arm64-v8a/libkodi.so`: reviewed Cast-only native source correction.
3. `AndroidManifest.xml`: typed versionCode only.
4. `assets/experience-component-updates.properties`: Infinity version label only.

**7,771 payload members are byte-identical; zero additions or removals.** The
original five DEX files, Cobra 2103445, Command Center 0.3.5.83 and its signed
modules, skin 1.0.5.274, Movies/Infinity Movies, Home Continue Watching, TV,
Search/providers, tracking/resume, settings schemas and all unrelated resources
are preserved. No user profile, account, database or settings file was read or
modified by packaging.

Native compilation retained 9,410 protected base files and the already existing
Cast CMake/builtin hooks, which are also unchanged against the 2103488 source
snapshot. Only the Cast translation unit changed. All 71,213 protected native
exports and the same 11 dependencies remain. The native source restoration uses
the preserved base provenance already contained in 2103488; candidate APK
assembly always starts with the exact signed 2103488 APK.

Recovery 2103491 restores **2103486 functionality** through the previously
verified signed 2103489 forward-recovery payload. Only its two APK/Infinity
version metadata members change; 7,767 members remain identical to that recovery.
It retains signed CC84/skin275 recovery metadata to avoid a module downgrade.
Recovery deliberately restores protected functionality and is not a second Cast
candidate. The original 2103486 artifact and lock remain unchanged.

Full signed-member receipts: [QA](SIGNED-CANDIDATE-PASS.json),
[recovery](SIGNED-RECOVERY-PASS.json), [unsigned preparation](PACKAGE-PREPARATION.json).

## Verification accounting

| Check | Result / evidence |
|---|---|
| Progressive authenticated HTTP, range/privacy/cancellation | PASS: 38 focused assertions |
| Adaptive authenticated HTTP, actual FFmpeg decode/seek | PASS: 57 assertions; TS/fMP4/separate-audio HLS, AES-128 HLS, DASH templates/timelines and single-file ranges |
| Actual Cast C++ translation unit with mocked player/GUI/message backends | PASS; source identity, cancellation/terminal outcomes and pure RAM release |
| Narrow registry/manifest release guard | PASS: six focused cases |
| Full Android ARM64 compile/link and ABI/source protection | PASS: [43314732573](https://github.com/mahfouzhassine8-ops/project-infinity/actions/runs/43314732573) |
| Android API 36 private HTTP/HLS/DASH, cookies, resources, five cleanup cycles and idle listener release | PASS: [43321698528](https://github.com/mahfouzhassine8-ops/project-infinity/actions/runs/43321698528); disposable component has no real receiver or Kodi JNI player |
| Exact complete pair staging | PASS: [43323900250](https://github.com/mahfouzhassine8-ops/project-infinity/actions/runs/43323900250) |
| Registry proposals | PASS: [43324721387](https://github.com/mahfouzhassine8-ops/project-infinity/actions/runs/43324721387), [43326213071](https://github.com/mahfouzhassine8-ops/project-infinity/actions/runs/43326213071) |
| Original signing, full signed APK comparison | PASS: [43325382217](https://github.com/mahfouzhassine8-ops/project-infinity/actions/runs/43325382217), [43326721200](https://github.com/mahfouzhassine8-ops/project-infinity/actions/runs/43326721200) |
| Android signed88 → QA90 → forward91 normal install, signature/package and retained data ownership | PASS: [43327402170](https://github.com/mahfouzhassine8-ops/project-infinity/actions/runs/43327402170) |
| Physical streaming-provider TV playback, controls/return, tracking continuity, Fold layouts/themes and post-Cast normal shutdown | NOT TESTED: one owner acceptance session after signing |

The earlier Android XML capability failures and actual C++ API mismatch were
corrected and retained as failure evidence. Subsequent probe failures exposed
case-sensitive fixture header matching and duplicate Activity probes during SDK
resource installation. The final probe admits exactly one transport test per
process, verifies original resource identity across recreation, and retains all
transport/privacy/cleanup assertions. Historical failures are not relabeled PASS.

The actual Android sequence retained UID `10216`, the same package data directory
and the same first-install timestamp at every step. There was no app launch,
uninstall, reset or forced downgrade. See
[ANDROID-INSTALL-RECOVERY-PASS.json](ANDROID-INSTALL-RECOVERY-PASS.json). This
checks Android update ownership; it does not inspect the owner's physical data.

## Installation and one owner acceptance

Install **2103490** as a normal Android update over the declared 2103488
installation. Do not uninstall, clear data, reset add-ons or force a downgrade.
Keep **2103491** available; install it as an ordinary higher-version update only
if deliberately returning to protected 2103486 functionality. Existing signed
module versions and all profile data are retained by the established update path.

Follow [FOLD-QA.md](FOLD-QA.md) once: play a streaming-provider movie, choose the
video receiver, confirm actual TV playback/position/controls, distinguish Close
Controls from Disconnect, confirm return/local resume and Continue Watching,
then normal Exit and relaunch. Physical device/receiver results remain the
owner's acceptance decision. No additional diagnostic installation is requested.

Supported delivery still requires receiver-compatible codecs and an available
local IPv4 receiver route. DRM/SAMPLE-AES/non-identity key systems, unsupported
HLS variable/content-steering features, unavailable legitimate source credentials
and unsupported codec/manifest combinations fail explicitly. No provider is
rewritten and no access control is bypassed. The environment has no physical
Onn/Fold receiver, so a successful real streaming-provider transfer and post-Cast
shutdown are not asserted from the host/component/build results.
