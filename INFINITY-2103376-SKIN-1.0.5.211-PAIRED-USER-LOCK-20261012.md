# Infinity compact ZIP preview — paired physical-device acceptance lock

**Status: USER ACCEPTED / LOCKED — 2026-10-12 (America/Detroit).**

The user installed/tested the candidate pair and reported **"fixed lock both"**.
This authorizes freezing **both APK 2103376 and Skin 1.0.5.211 together**
as the next approved Infinity compact ZIP-preview baseline, without
rebuilding, modifying, merging, or deleting either runtime component.

## Exact approved installable artifacts

| Component | Verified installable file | Size | SHA-256 |
| --- | --- | ---: | --- |
| Infinity Android APK, `com.projectinfinity.kodi`, versionCode **2103376** | `Infinity-2103376-Signed-Test.apk` (same APK payload as CI artifact `Cobra-2103376-Critical-Preview-RC1.apk`) | 159257399 bytes | `8e8e139929592daedb63e0e41040258d655f132fd025b236de7dee1e88b47649` |
| Infinity Skin add-on `skin.infinity.diggz`, version **1.0.5.211** | `skin.infinity.diggz-1.0.5.211-Compact-ZIP-Preview-RC1.zip` | 59059702 bytes | `460762f78ad2a1cb2d54639e973d20a5958de0c22575a0d7f228b7f1cdc73815` |

These are a **paired lock**: do not substitute APK 2103375, Skin 210,
or a rebuilt/rehydrated package with differing bytes without renewed validation.
The approved deliverables are those the user already received and tested.

## Pinned source and exact evidence

- **APK source lock branch:** `locked-infinity-apk-2103376-user-passed-20261012`.
- **APK packaging source commit:** `808b4acc4d1a6aa1cbc8bc4a1848de88b81103e6`; its parent native correction is `4754a12ec684592030ba52994997ed76d3629364`.
- **APK signed CI:** run `38323908660` — SUCCESS; artifact `11779569440` (`Cobra-2103376-Critical-Preview-Signed-Test-APK`), 207 original regression tests passed and permanent signing verified.
- **Skin source lock branch:** `locked-infinity-skin-1.0.5.211-user-passed-20261012`.
- **Exact Skin 211 implementation/packaging commit:** `081771fe0dadff4890c110daf631a5759ba28f8e`; the checked-out final skin lock branch was created from `1d3a24bd0e5cef06727d8caa577e3b2dc22af0a8`, adding **test-harness corrections only**, not skin runtime changes.
- **Skin Kodi 21.3 actual renderer CI:** run `38329752589` — SUCCESS; renderer evidence artifact `11782707338`. This is a renderer test, **not** a skin ZIP.
- **Skin candidate package validation:** 64 tests passed, 30 existing files changed, nine new files added, zero removed, 2939 existing ZIP entries (payload and compressed content) preserved exactly; valid `skin.infinity.diggz` add-on ID and `1.0.5.211` version.
- **Exact Skin 210 parent ZIP:** SHA-256 `8febf697772ece72c9a445d0b5b6fd2650f97889a00e1e311dc0588199596bb3`.
- Skin candidate preservation receipt `repairs/skin-211-compact-preview/package_candidate.py` + `SKIN-211-PRESERVATION.json` were generated against that exact parent. Its original pre-acceptance `locked:false` field describes the state **before** this user approval. It is not a reason to modify the accepted package.

## Preservation / future handoffs

- This lock is an acceptance and source-freeze record; the preceding candidate's
  `physical_device_accepted:false` field is historical. User acceptance is
  now recorded here from the explicit report, not inferred from desktop CI.
- **Keep earlier locked APK 2103374 and locked Skin 1.0.5.208 unchanged** as
  rollback/historical checkpoints. Keep parent Skin 210 and earlier source
  commits available for diagnostics, without promoting the regressed preview.
- Do not change the signed APK, skin ZIP, add-on ID, app package ID,
  signing identity, preview controls, playback, Cobra, providers, or unrelated UI.
- Future work must branch **from the relevant exact pinned source commit**
  and must not move these lock branches or overwrite the SHA-pinned files.
  A new test candidate needs a new version and explicit user acceptance before
  replacing this approved pair.
- This document was added as a **receipt-only commit** on the Skin lock branch.
  It does not alter the approved source or binary deliverables. GitHub branch
  names express a process lock; they are not a claim of server-enforced branch
  protection or an immutable Git tag.
