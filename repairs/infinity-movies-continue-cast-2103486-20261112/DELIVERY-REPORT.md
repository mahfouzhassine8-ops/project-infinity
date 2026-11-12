# Combined Movies / Continue Playing / Infinity Cast — internal QA

Accepted baseline remains **2103486**, SHA-256
`550b67fa095e2f1c702c073433f754ba3db7cc057e42f1d05fe0789ff264f197`.
Neither APK below changes the accepted-baseline pointer. These are the complete
combined candidate and its forward recovery, not a diagnostics-only release.

| Artifact | Version | Command Center | Skin | Original-signing source |
|---|---:|---|---|---|
| Combined QA candidate | 2103488 | 0.3.5.83 | 1.0.5.274 | `f0aa976d90b262373cea56942a44c9e382ccfaa3` |
| Forward recovery to accepted 2103486 functionality | 2103489 | 0.3.5.84 | 1.0.5.275 | `ab5f3e41721291091e5fe177787156408193c0fa` |

Package ID: `com.projectinfinity.kodi`. Cobra remains **2103445** in both APKs.
The higher recovery versions allow ordinary installation over QA without a
downgrade. Recovery contains original baseline functional source and native code,
with only version and integrity metadata advanced.

## Downloads and APK checksums

- [QA 2103488 — GitHub artifact containing the APK](https://github.com/mahfouzhassine8-ops/project-infinity/actions/runs/43294871896/artifacts/13979655699)
- [Forward recovery 2103489 — GitHub artifact containing the APK](https://github.com/mahfouzhassine8-ops/project-infinity/actions/runs/43295951138/artifacts/13979418392)

The SHA-256 values below identify the extracted **APK**, not its artifact ZIP:

```text
4217b217bca06084121572bbde71164abe67d05ef49741c78d4f83c5c5d4a566  Infinity-2103488-Combined-Original-Signer.apk
5fa350dd945fcb8f294975be6fd16ee3c4432ffa1519089aa70bbde680fdf834  Infinity-2103489-Combined-Original-Signer.apk
```

Both passed original v1/v2/v3 signature verification. Certificate SHA-256:
`d7adeb68e9341596a02bd3262b737a0f45fc6e771ed7e60285437e833b58c6d7`.
Only the established original-key workflow 397702717 and unchanged original APK
assembler signed these APKs. No replacement identity was created.

## Implemented scope

**Saved movies:** `experience.py` verifies the installed provider movie-route
contracts; `plugin.py::_target()` reuses a valid existing saved native movie
source even when its older stable-source stamp is absent. The existing fallback
and navigation machinery remain in place. TV routes and provider implementations
are unchanged. A successful real movie is exposed to the existing navigation
confirmation using the same validated actual-item identity.

**Continue Playing:** the movie-only actual-playing-item fallback in `service.py`
recovers verified movie metadata when the generic RPC item lacks it. Two stable
native snapshots must agree; stale, conflicting and unstarted items are refused.
Only then does the existing recorder/Resume Hub receive the identity. Stream URLs
are marked transient rather than stored as replay routes. Existing duration,
position, percentage, hidden, watched and completion rules are unchanged.

**Cast:** the two requested controls in the existing active `VideoOSD.xml` open
an explicit receiver picker through a bounded native bridge. The new private Java
component integrates the official Cast SDK, remote controls and return to phone.
Its single-source relay keeps provider URLs/query credentials/headers on the
phone. Receiver preparation must succeed before local playback is paused. Failed
or unsupported transfer preserves local playback. Remote progress feeds the
existing recorder through `cast_runtime.py`; no second tracker/database exists.

## Exact preservation

The signed candidate has **7,755 unchanged payload members**, **14 modified
existing members**, and **6 additions**. The signed recovery has **7,761 unchanged
payload members**, **8 modified metadata members**, and **no additions**.

All five original DEX members remain byte-identical under their original names;
Cast is appended as `classes6.dex`. Its SDK, AndroidX and HTTP dependencies are
isolated, with zero original class collisions or Cobra-owned type references.
Original APK resources remain unchanged. The manifest changes only the reviewed
Cast metadata/query and version; no startup initializer, permission, activity,
service or lifecycle replacement was added.

The candidate native engine changes only the Cast builtin/bridge build inputs
(two existing source files plus one added file). All 9,410 other native source
files, 71,213 old exports and eleven native dependencies were preserved.

Shutdown/persistence, Python startup, Search, providers, working TV code, Cobra,
profiles and databases are outside the source delta. Existing databases/settings
were not opened or modified by packaging. The complete before/after SHA-256 member
lists are authoritative:

- [Candidate preservation](release/evidence/candidate/PRESERVATION.json)
- [Recovery preservation](release/evidence/recovery/PRESERVATION.json)
- [Candidate signing receipt](release/evidence/candidate/BUILD-RECEIPT.json)
- [Recovery signing receipt](release/evidence/recovery/BUILD-RECEIPT.json)
- [Actual Android install-over/recovery receipt](release/evidence/INSTALL-OVER-AND-RECOVERY.json)

## Verification and limits

| Check | Result / evidence |
|---|---|
| Focused movie contracts and actual-item host cases | PASS; 15 cases retained, with only affected confirmation/race/eligibility cases rerun for the final correction |
| Cast clock host cases | PASS, 12 cases |
| Private relay actual HTTP host checks | PASS, 30 assertions |
| Real Android ARM64 compilation, link, source and ABI preservation | PASS, run **43239137210** |
| Private Cast SDK/resources/local relay on Android API 36 | PASS, run **43285053644**; no real receiver |
| Complete CC83/84 original module signatures | PASS, run **43292767635** |
| Final complete pair preparation and exact member guard | PASS, run **43293634100** |
| Candidate source-bound authority review / original signing | PASS, runs **43294396170 / 43294871896** |
| Recovery source-bound authority review / original signing | PASS, runs **43295513012 / 43295951138** |
| Signed in-place installation and forward recovery | **PASS**, Android API 36 run **43296801035**; 2103486 → 2103488 → 2103489; UID, dataDir and firstInstallTime unchanged |
| Physical Fold Movies/Home/Cast/normal shutdown | **NOT RUN — owner acceptance after signing** |

Cast currently supports progressive MP4/M4V/WebM on compatible Google Cast video
receivers over a supported local IPv4 route. HLS/DASH, DRM, unsupported Kodi
transport options, audio-only receivers and unsupported routes are refused.
Real receiver transfer and physical Fold layout/behavior are unverified. Host
and component checks do not claim they passed.

The actual Sacrifice `continue-watching.json` record was unavailable. Its existing
Home eligibility was not invented or forced; the recorder and filters were not
weakened to make that card appear. Actual movie handoff, qualifying Home display,
Cast controls and normal shutdown are included in the one owner acceptance session.

## Installation and recovery

Download the QA artifact, extract `Infinity-2103488-Combined-Original-Signer.apk`,
verify its APK checksum and install it over the existing Infinity installation.
Do not uninstall, clear data, reset Kodi or replace provider settings. If the
currently installed version is already above 2103488, do not force installation.

Follow [the single combined Fold acceptance session](FOLD-QA.md). Install
`Infinity-2103489-Combined-Original-Signer.apk` only if returning to accepted
2103486 functionality is needed. It is an ordinary higher-version recovery;
it does not require data deletion or a forced downgrade. Installing recovery
makes 2103488 lower-versioned, so do not attempt to reinstall QA over recovery.

Only the owner can accept a successor. Accepted 2103486 and its signed artifact
and lock remain unchanged.
