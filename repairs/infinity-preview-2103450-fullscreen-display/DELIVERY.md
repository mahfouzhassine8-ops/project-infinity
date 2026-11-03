# Infinity Preview2103451 — signed testing candidate

One original-key-signed combined install-over APK is delivered for physical Fold
acceptance. Signed2103450 remains protected;2103451 is not locked or promoted.

- [Signed APK download (ZIP)](https://github.com/mahfouzhassine8-ops/project-infinity/actions/runs/41568721264/artifacts/13200361701). Extract `Infinity-2103451-Combined-Original-Signer.apk`.
- [Exact matching component ZIPs](https://github.com/mahfouzhassine8-ops/project-infinity/actions/runs/41568721264/artifacts/13200925524): INFINITY, COBRA, CHOOSER_SHELL and MINIMAL_ANDROID_CONTRACT.
- [Successful signing/build41568721264](https://github.com/mahfouzhassine8-ops/project-infinity/actions/runs/41568721264).
- [Successful selected Android verification41567002286](https://github.com/mahfouzhassine8-ops/project-infinity/actions/runs/41567002286).
- [Recovery: unchanged signed2103450](https://github.com/mahfouzhassine8-ops/project-infinity/actions/runs/41541654995/artifacts/13186062986).

Package:`com.projectinfinity.kodi`; versionCode:`2103451` (higher than2103450).
Inherited versionName:`1.0.9-Final-Corrections-TEST0011` is preserved.
APK size:778596097bytes. Signing source:
`e50e68dad4c50690601bacbe1724507912b70fbd`.
Exact tested component preparation source:
`fb0051879ec92ee502305d35e1f6d7c1c4ac6180`, producer41568299660.
Original RSA4096 certificate SHA256:
`d7adeb68e9341596a02bd3262b737a0f45fc6e771ed7e60285437e833b58c6d7`.
Independent apksigner verification confirms v1,v2 and v3 signatures and the same
certificate as the actual signed450 APK. Package identity, higher code and the
unchanged manifest contract support install-over compatibility. Actual Fold
installation remains unverified here. Do not uninstall or clear application data.

## Implemented behavior

Fullscreen is between Display and Auto rotate in the existing horizontal rail.
Entering maximizes the available video viewport, temporarily selects proportional
Fill/crop, and hides app chrome/system bars as Android permits. Tapping video
reveals overlay controls without shrinking the viewport. Exit/first Back restores
the prior Best Fit/Fill/Stretch choice, normal layout and complete system-bar
request policy. Rotation, decoder and media position remain independent.

Display has the approved three described choices, left radios, selected-only
cyan outline/tint, palette Appearance action, divider and cyan Done pill, with
existing System/Light/Dark preferences. Stretch distorts only when selected.
The original Engine, request/routing, resume database, call/audio policy and
protected playback/lifecycle methods remain exact. No new player/application,
provider operation, service, migration or background worker is introduced.

Production implementation files changed are only:
`InfinityExternalPlayerActivity.java`, `InfinityPreviewChrome.java` (Control glyph)
and new `InfinityPreviewDisplayDialog.java`, all under the existing isolated
Preview runtime. Owner registration, branch admission, version metadata and
focused test/release evidence support the existing original signing mechanism.
Original signer, assembly, inventory and authority-validation implementations
remain frozen. Source/method/class guards enumerate the permitted UI changes.

## Available verification

15 focused host tests PASS: actual View input/native Canvas and targeted retained
controls, themes, short/cover/inner layouts, save/resize, rotation, call policy and
previously-failing full-system-bar restoration. Their decoder is a terminal spy.

Actual API37.1 Android decoding/input separately PASS in41567002286:233 recorded
observations,11 Fullscreen entries,16/16 decoded edge samples per entry, four
viewport/orientation sizes, wide/portrait/square media, all three prior Display
choices restored, native scrolling to lower options, Resume/Start Over and actual
source package/control/foreground ownership with final decoder release. The
square-marker ratios are0.96 Best Fit,1.00465 Fill and8.64 Stretch; only explicit
Stretch distorts. Largest observed hidden-chrome response0.623s is emulator
evidence, not a physical Fold performance claim. Six focused release-protocol
checks PASS, including rejection of wrong baseline, frozen-member mutation,
wrong version/DEX and incomplete runtime evidence. Passing source-specific
checkpoints and all failed/cancelled attempts are retained separately.

After downloading the published artifacts, independent verification checked archive
SHA256/CRC, original certificates, every APK member, package/version identity and
all component payload/DEX bytes. Results are in [delivery-evidence](delivery-evidence).
No shutdown suite was run; protected shutdown code/payload is unchanged.

## Exact signed450 preservation

7611 payload members and all47 native libraries are byte-identical. Cobra's
compiled payload and its entire ZIP are identical; shared/contract ZIP is also
identical.630 unrelated complete Infinity class definitions, including the
original engine/resume/routing, remain exact. Kodi assets/add-ons/providers, skin,
resources, icons, shared DEX, chooser/Splash code and shutdown are preserved.
User data was not accessed, reset or migrated.

Every changed APK member is enumerated below; there are no added/removed members:

| Member | Authorized difference |
|---|---|
| classes3.dex | Only scoped Preview UI classes; exact tested DEX5634f2376e5d0bf6176ebef6fa1ac16bb22fdecc1d018ac078f266bb757fe9b8 |
| AndroidManifest.xml | App versionCode2103450→2103451 only |
| assets/experience-component-updates.properties | Infinity451/Cobra445 truthful version labels |
| META-INF/MANIFEST.MF | Expected v1 signature metadata |
| META-INF/INFINITY.SF | Expected v1 signature metadata |
| META-INF/INFINITY.RSA | Expected original-certificate v1 signature |

The APK signing block is regenerated with the same permanent identity. Component
DEX/assets match the signed APK; the frozen shared manifest's normalized functional
content matches, with app-wide versionCode injected by the existing combiner.
The inherited build receipt contains historical launcher-icon transform metadata;
that describes existing baseline content. Exact450→451 comparison confirms no
icon/resource change in this release.

## Checksums

| Delivered file | SHA256 |
|---|---|
| Infinity-2103451-Combined-Original-Signer.apk | d77c31c458c4571212022bea7cea1e76c1d415cd5792b780b3c655fba97c6399 |
| INFINITY.zip | 7aea7edf649f5718bf858d97c61ec87e976ddd84cee320bed28b78721f449130 |
| COBRA.zip | f63d4c1e491dc94591c5623bf02be90d4f9c187b91a0511b36398ee96745f8a8 |
| CHOOSER_SHELL.zip | 70da3f8ff060c4709ef8c0a61821f001a24355d6f3c086ecaf9c6fc707d42360 |
| MINIMAL_ANDROID_CONTRACT.zip | 1c4a2890ef5ca8665b86b148dd293c06a56d76ec846de1e0c9c037a3b0151a25 |

Signed download archive SHA256:
`7e2eb67204ecc24e1a9d27007e90050b40683f0442bd8c32aec9b3bac32a9c41`.
Components download archive SHA256:
`e5f3017e5154625561103580c86020eab0176cc4d1f6ca033f0c1bb8726baedd`.
Machine-readable [all checksums](delivery-evidence/DELIVERY-SHA256SUMS),
[signature](delivery-evidence/CANDIDATE-SIGNATURE.txt),
[every-member comparison](delivery-evidence/ALL-APK-MEMBERS.json),
[published verification](delivery-evidence/PUBLISHED-VERIFICATION.json) and
[component matching](delivery-evidence/PUBLISHED-COMPONENT-MATCH.json) are retained.

## Remaining visual/device acceptance

Independent direct original-PNG/native-render review confirms all five identified
structural differences are corrected. The coding executor did not personally
access the private originals; attribution and original hashes are documented in
REFERENCE-PROVENANCE.md. Retained stylistic differences are lighter font weights,
different Best Fit/Fill glyphs, gray rather than cyan palette icon and a flatter
Done-button finish. Pixel equivalence/exact visual acceptance is not claimed.
These differences are disclosed for the user's physical visual review.

Physical Galaxy Fold8 Ultra acceptance remains pending: genuine fold/unfold,
One UI/cutouts/gestures/multi-window, device rotation and media/provider behavior
cannot be certified by host/emulator checks. Use [FOLD-ACCEPTANCE.md](FOLD-ACCEPTANCE.md):
check Fullscreen on cover/inner portrait/landscape, tap/reveal/exit/Back, prior-mode
restoration, fit/crop/stretch, themes/Appearance, full rail scrolling and existing
controls/resume/source return. Keep2103450 as recovery. No automatic lock or
promotion has occurred; accepted_pointer_updated is false and protected lock
hashes remain unchanged.
