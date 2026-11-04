# Controlled Kodi UI release readiness — 2026-11-04

**Disposition: ready for review of a packaging/recovery plan; not approved to
build, sign or install.** No APK or component archive was produced, no workflow
was dispatched, and no production source, authority registry or recovery lock
was changed. The source candidate remains exactly
`1cc7684bd05581c21f31682cdb0f2d4e156a585e`.

The proposed testing APK is **2103454**. The proposed forward-recovery APK is
**2103455**, restoring **2103453 functional code**, including its exact P0 engine.
These numbers are currently unused in the inspected release records, but are
**not reserved**. Recheck the registry, signed artifacts, active builds and the
device's installed version immediately before any separately authorized build.

## Verified foundation

| Item | Verified value |
|---|---|
| Exact base | Signed combined 2103453; source `cb7c6214807b79661e397cccb0740fc91fab3e24` |
| APK SHA-256 | `08ca19e9ff01e3830253980028dbcdbfb36056fd71b06a18cbfb922158ceaac8` |
| Original certificate SHA-256 | `d7adeb68e9341596a02bd3262b737a0f45fc6e771ed7e60285437e833b58c6d7` |
| Signature verification | Fresh SDK verification passes v1, v2 and v3; one original signer |
| Package / ABI | `com.projectinfinity.kodi` / `arm64-v8a` |
| SDK declarations | minSdk 21, targetSdk 35; not evidence of Android 17 runtime acceptance |
| Exact protected `libkodi.so` | `d0b6f115e839fbe39e764e2fecad47418c501ab1ece853294578652cd0b80b98` |
| Original signing run | [41783963413](https://github.com/mahfouzhassine8-ops/project-infinity/actions/runs/41783963413) |
| Base APK artifact | [13301200085](https://github.com/mahfouzhassine8-ops/project-infinity/actions/runs/41783963413/artifacts/13301200085) |
| Matching component artifact | [13301010393](https://github.com/mahfouzhassine8-ops/project-infinity/actions/runs/41783963413/artifacts/13301010393) |

The original artifacts remain listed and unexpired until 2027-02-02. These are
authenticated GitHub artifact links, not a newly delivered candidate. The local
base and all four component ZIP hashes were verified directly. Every component
payload and DEX partition was compared with the signed APK. The existing frozen
Android-contract ZIP contains a template manifest: only its typed versionCode
differs from the assembled APK. This established exception is explicitly
recorded, not described as byte equality.

| Existing component ZIP | SHA-256 | Proposed treatment |
|---|---|---|
| COBRA | `f63d4c1e491dc94591c5623bf02be90d4f9c187b91a0511b36398ee96745f8a8` | Copy ZIP unchanged |
| MINIMAL_ANDROID_CONTRACT | `1c4a2890ef5ca8665b86b148dd293c06a56d76ec846de1e0c9c037a3b0151a25` | Copy ZIP unchanged; existing combiner changes only APK versionCode |
| INFINITY | `4a7747418633c66cc01bf0cd113ddabd1cdda178179d4c55d01597e883cb1632` | Repack only reviewed UI and trust/version metadata |
| CHOOSER_SHELL | `3d1a0b4e4e0fa7eb56f32a7eb7573d30de618e19678f11cf19e9401bbb9f9776` | Change only existing component-version text; chooser DEX frozen |

## Complete proposed member allowlist

The machine-readable [allowlist](PROPOSED-MEMBER-ALLOWLIST.json) binds each source
member to its exact base and checkpoint SHA-256, and gives a field-level
constraint for each future metadata change. There are **19 payload members**:
11 UI source members and eight packaging metadata members. None has been applied
to an APK. No member deletion is permitted.

Paths below use `CC = assets/addons/script.infinity.commandcenter/` and
`SKIN = assets/addons/skin.infinity.diggz/`.

| Member | Permitted change |
|---|---|
| CC `service.py` | Exact checkpoint source |
| CC `media_view.py` | New, exact checkpoint source |
| SKIN `unified/Includes.xml` | Exact checkpoint source |
| SKIN `unified/MyVideoNav.xml` | Exact checkpoint source |
| SKIN `unified/Custom_1198_InfinityNav.xml` | Exact checkpoint source |
| SKIN `unified/Includes_InfinityMediaLists.xml` | New, exact checkpoint source |
| SKIN `unified/Includes_InfinityVideoOptions.xml` | New, exact checkpoint source |
| SKIN `unified/custom_1136_InfinityVideoViews.xml` | New, exact checkpoint source |
| SKIN `unified/custom_1137_InfinityVideoViewSettings.xml` | New, exact checkpoint source |
| SKIN `unified/custom_1138_InfinityVideoDisableViews.xml` | New, exact checkpoint source |
| SKIN `resources/lib/infinity_library_navigation.py` | New, exact checkpoint source |
| `AndroidManifest.xml` | Typed versionCode only; all other bytes, permissions, handlers and versionName frozen |
| `assets/experience-component-updates.properties` | Infinity version advances; Cobra stays 2103445 |
| CC `addon.xml` | Only `.54` to `.55` package version |
| CC `INFINITY-MODULES.v1` | `.55` generation, changed service/addon hashes and new helper; other records and contracts frozen |
| CC `INFINITY-MODULES.v1.sig` | Original-key signature of that exact manifest |
| SKIN `addon.xml` | Only `1.0.5.251` to `.252`, existing CC dependency `.54` to `.55` |
| SKIN `infinity-skin.json` | Existing candidate/version fields only |
| SKIN `Infinity-Protected-Manifest.json` | Existing version fields and hashes of the specifically authorized changed/new skin files |

The only additional ZIP-member exceptions are the existing APK signing entries:
`META-INF/INFINITY.SF`, `META-INF/INFINITY.RSA`, and `META-INF/MANIFEST.MF`.
The APK v2/v3 signing block must also be regenerated with the original key. There
is **no blanket META-INF exception**. ZIP offsets/compression/alignment can change
as container mechanics; uncompressed protected member bytes cannot.

The baseline has 7,617 members. Four existing UI members change, seven are added;
eight existing metadata members and three signing entries are permitted to
change. The other **7,602 existing members must remain byte-identical**, including
**all five DEX files and all 47 native libraries**. Exact baseline hashes are in
[BASELINE-PROTECTED-MEMBER-HASHES.json](BASELINE-PROTECTED-MEMBER-HASHES.json).
This freezes Preview, Cobra, the engine, provider/add-on code outside the listed
first-party UI files, compiled resources, icons, shared components and shutdown.
Databases and user settings are not packaging inputs and must not be accessed or
migrated. The intended global view preference still uses the existing native
skin-setting persistence mechanism.

This is a verified **base-to-source-overlay comparison and future APK gate**,
not a completed candidate-to-base APK comparison. Candidate hashes and actual
member equality can only be established after separately authorized packaging.

## Why eleven files alone cannot be packaged

Signed 2103453 authenticates Command Center `.54` using a 76-file manifest and
the permanent RSA public key. The changed service would fail its old hash; the
new helper is not admitted by that manifest. The proposed `.55` manifest must
have 77 file records, with no altered entry points, capabilities, protocol,
installation-baseline inventory or unrelated source records. Existing native
and Python verification code stays byte-identical. A new manifest signature is
required; authentication must not be bypassed.

The skin's protected-file inventory must likewise describe the reviewed files.
Its version and existing CC dependency must advance so an installed older skin
can select the new generation. Existing metadata generation in
`repairs/infinity-2103436-end-to-end-loading/release437.py` is a reference for the
established format, not a recipe to execute or a permission to rebuild 2103437.
Actual installed-skin selection and real Command Center integration remain
Android verification requirements.

The skin inventory currently has 942 entries. Update its three changed UI-file
hashes plus `addon.xml` and `infinity-skin.json`, and add the six new skin members:
948 entries in the candidate. It does not hash itself. All other existing
protected-file hashes must remain exactly unchanged.

## Version and signing gates

The read-only inventory covered 584 remote heads/tags, all 12 published GitHub
Releases, the current release and UI branch authorities, the latest 100 workflow
runs and exact 2103453 artifacts. The latest run is successful signing run
41783963413; no active run or issued 2103454/2103455 appeared. The registry still
says `last_issued=2103452` while its candidate and actual signed output are
2103453. The real signed output takes precedence; 2103453 cannot be reused.
Deleted builds or builds outside the inspected repository cannot be ruled out.

The sole trusted signer is workflow **397702717**,
`.github/workflows/infinity-combined-release.yml`. Its existing branch and
version checks authorize previous 451/452/453 routes, **not this UI branch**.
A separately approved packaging change must add an exact UI/recovery producer,
owner allowlist, source/manifest hashes, version/generation and prepared-artifact
bindings. It must retain original signer ownership, serialization, pre-key
integrity gates, authority recheck and post-sign preservation checks. Reusing a
453 route under false metadata or broadening its guard is prohibited.

Repository and artifact metadata access work. Listing secret metadata returns
**403 “Resource not accessible by integration.”** This does not establish that
signing is broken: the trusted workflow succeeded with the original key. It also
does not prove future secret availability. No secret value was requested and no
workflow was dispatched to probe it. Future key access must remain inside the
approved workflow after its gates; no credential replacement is proposed.

## Forward recovery required before installation

The previous recovery evidence is an **unsigned** 2103454 rehearsal restoring
2103452's engine `f89a40b5…`, not 2103453's `d0b6f115…`. It was not issued and is
not a usable recovery artifact for this UI candidate.

Read-only disassembly of **the actual signed 2103453 DEX** confirms the existing
installer compares numeric signed-module generations and will not replace a
valid newer generation with an older one. See
[FORWARD-RECOVERY-CODE-EVIDENCE.json](FORWARD-RECOVERY-CODE-EVIDENCE.json).
Increasing only Android versionCode would therefore be inadequate.

The proposed recovery is:

| Payload | Testing candidate | Forward recovery |
|---|---|---|
| Android versionCode | 2103454 | 2103455, revalidated as higher than installed |
| Command Center generation | 0.3.5.55 | 0.3.5.56, original 2103453 functional files |
| Skin generation | 1.0.5.252 | 1.0.5.253, original 2103453 functional files |
| Native/DEX/providers | Exact 2103453 | Exact 2103453 |
| Package/certificate | Original | Original |

Recovery metadata must truthfully advance versions and authenticate the restored
files; it cannot be byte-identical to 2103453 in those declared metadata fields.
Existing installer preflight, previous-generation backups, signature checks and
unknown-file rejection remain unchanged. It does not remove obsolete helper
files: verification must show any retained candidate-only files are unreferenced
and cannot alter the restored functional UI. No user-data cleanup is allowed.
The new skin preference can remain stored and ignored by restored baseline code.

The recovery archive must exclude the seven candidate-only UI members, restore
the baseline 76-file module inventory and 942-entry skin inventory, and update
only the declared version/trust metadata hashes for that restored generation.
Packaging two versions does not accept either one: record issued versions
without moving any user-approved baseline or lock.

Before installation, require the following under **separate approval**:

1. Produce and independently verify both the controlled candidate and an actual
   original-key-signed, higher-version recovery package through the trusted
   workflow. Keep recovery downloaded and its hash/certificate checked, not only
   a plan or expiring artifact URL.
2. Verify recovery functional files against the signed 2103453 inventory, exact
   engine/DEX hashes, authenticated module generation and skin inventory. Check
   install-over upgrade/recovery behavior in an isolated authorized Android
   target where available; report physical-only limits explicitly.
3. Before user installation, confirm the installed package/certificate/version,
   available storage and recovery accessibility. Finish ordinary saving and
   normal close; unresolved durability/checkpoint obligations block replacement.
   This is an installation precondition, not a newly selected shutdown suite.
4. If the UI candidate fails, install the already verified recovery over it after
   safe normal closure. Never use downgrade flags, uninstall, data clearing,
   forced termination or manual database edits. If safe closure is blocked,
   retain evidence and stop; an APK cannot recover unsaved in-memory writes.
5. Confirm restored module/skin selection and data preservation. Recovery does
   not claim to correct the unresolved Scudo crash or any independent native issue.

No signed UI recovery exists yet. Thus the **usable forward-recovery gate is
pending**, not passed. If the preserved installer cannot safely restore the
functional skin/module on an authorized test target, stop before user
installation and report that conflict; do not alter protected installers.

## Evidence reuse and pending gates

Completed source investigation is not reopened. The existing record retains
39 distinct executed host cases, 145 Linux assertions and 16 reused host cases
(55 cumulative). Source hashes are unchanged. No behavioral test was rerun in
this readiness pass.

The Linux fixture does not start the authenticated production Command Center
service, and its renderer lacks the protected Android layout implementation.
Its screenshots **do not establish visual acceptance**. Actual Android service
integration, skin generation selection, Red Light/other providers, touch,
storage access, video return and Fold geometry remain pending. Original user
media was independently inspected by another reader; this executor does not
claim direct access or physical acceptance.

| Gate | Current finding |
|---|---|
| Exact 453 base, original signature, owner ZIPs and source hashes | Verified read-only |
| Proposed full allowlist and protected inventory | Complete; machine-readable |
| 454 candidate / 455 recovery availability | Unused in inspected records; not reserved |
| Packaging/recovery authorization | **Not granted** |
| Narrow trusted-workflow/authority wiring | **Required; not implemented** |
| New authenticated module and skin metadata | **Required; not generated/signed** |
| Actual candidate/recovery APK comparison and signature verification | **Pending authorized packaging** |
| Usable signed forward recovery | **Not yet available** |
| Android/Fold visual and functional acceptance | **Pending**; checklist prepared |

Future packaging must stop on any unexpected member, signature, ownership,
installed-generation or recovery mismatch. No automatic promotion or lock.
The focused physical procedure is in [FOLD-ACCEPTANCE.md](FOLD-ACCEPTANCE.md).
