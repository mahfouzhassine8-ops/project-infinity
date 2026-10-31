# Signed Infinity loading testing candidate 2103437

**One actual original-key signed install-over APK is delivered.** Physical Fold
acceptance remains pending. Signed 2103436 and its protected lock are unchanged;
no new lock or promotion was created.

- [Download signed APK archive](https://github.com/mahfouzhassine8-ops/project-infinity/actions/runs/41194267440/artifacts/13039304383)
- [Download exact matching component ZIPs](https://github.com/mahfouzhassine8-ops/project-infinity/actions/runs/41194267440/artifacts/13040113384)
- [Successful signing/build run 41194267440](https://github.com/mahfouzhassine8-ops/project-infinity/actions/runs/41194267440)
- [Signing source 31d55543e3a01a37975c396c0291ff26d98cc4b8](https://github.com/mahfouzhassine8-ops/project-infinity/commit/31d55543e3a01a37975c396c0291ff26d98cc4b8)
- Infinity implementation/component source: `116d7146d0ceeaa3d6b3b1b98799c62b515fea0a`.
- Successful authenticated preparation: [41193983471](https://github.com/mahfouzhassine8-ops/project-infinity/actions/runs/41193983471).

Extract `Infinity-2103437-Combined-Original-Signer.apk` from the APK archive and
install over the existing app. The component ZIPs match this APK; they are not
separate Android applications. Package identity remains `com.projectinfinity.kodi`.
VersionCode 2103437 is greater than protected 2103436; no uninstall, clearing data,
database migration or preference reset is used.

## SHA256

| File | SHA256 |
| --- | --- |
| Infinity-2103437-Combined-Original-Signer.apk | `6852a7e50003648e56a9f6f0f9e185a1f80f341b4bad9c4c6be7e2f02856b88c` |
| INFINITY.zip | `d03b4d5e845dfb5e1d6bb75c1967c7b6a2e55c5b17a7c65d66d43d43abd2e73d` |
| COBRA.zip | `41d812863992d9200bbd7708cc03c4a4c048354ccb67cc4ff73ec8c5fb6bb0cb` |
| MINIMAL_ANDROID_CONTRACT.zip | `432bfb7b246a504d9550e1de39368c3b7e0946532f1c695531ed891e74ef03d8` |
| CHOOSER_SHELL.zip | `ae00ab80b9f766762e931b2c12848a0d7ec44f5df1cce329b1a5c8ac9e473b14` |

Original certificate SHA256:
`d7adeb68e9341596a02bd3262b737a0f45fc6e771ed7e60285437e833b58c6d7`.
Both exact signed436 and the downloaded437 APK independently pass apksigner
verification with that certificate and v1/v2/v3 signatures. CI also checks 16KB
native ZIP alignment. The Infinity module's 76-file manifest is authenticated by
the same original RSA identity and verified with the frozen native verifier.

## Implementation and comparison

| Behavior | Signed436 / earlier checkpoint evidence | Delivered437 evidence |
| --- | --- | --- |
| Independent task completion, profile ownership and background resize | Four focused signed436 host failures | Four corrective cases pass; retained final observer source and existing regressions |
| Foreground cancellation versus delayed background work | Reproduced dropped independent background start | Separate retirement boundary; regression passes |
| Selected-item ownership and common navigation | Fixed window ownership and incomplete common-frame coverage | Local token/capability ownership;219 additive eligible border calls and 913 observer pairs; 65 statically reachable windows |
| Native busy | Signed436 group unconditionally invisible | Native-owned Home/Videos drawer projection; actual full-skin Videos cue and terminal cleanup verified on Linux; supported native progress/Cancel retained |
| Overlapping native and selected state | Potential hidden/duplicate cue during modal ownership | Native cue takes precedence and survives matching foreground token; actual full-skin overlap capture verified |
| Reported approximately 75-second VIDEOS delay | Recording bytes unavailable; exact selected provider/route not established | Not reproduced, attributed or claimed fixed; original native/provider action contracts preserved |

No quantified real-provider, Android or physical Fold speed improvement is
claimed. The full-skin fixture's 4.5-second provider wait is deliberately injected
QA behavior, not production code or a performance benchmark. Native directory
navigation activates Videos before results; it cannot safely retain the prior
screen without changing that native contract. Destination-local feedback is used.

## Verification and preservation

Retained 28 focused host cases, 25 minimal Linux Kodi fixture assertions and 9 image
checks. The final fallback change additionally passed 11 generated-source tests
and 15 actual full-skin Linux assertions. Five selected release-protocol checks
pass. These are not Android/Fold acceptance results; historical minimal-fixture
checks were not relabeled as testing every production window.

Official artifact archive hashes were verified. Independent inspection of the
actual downloaded signed APK confirms exact matching component members, all 5 DEX
files, and original signature. The final comparison against the exact original
signed436 APK enumerates **101 changed ZIP members**: 90 functional Infinity
loading members, 6 required Infinity version/integrity members, 1 truthful chooser
version-label member, 1 typed APK versionCode member and 3 regenerated original-key
APK signature members. No member was added or removed. There are 7,516 unchanged
non-signature members. All 47 native libraries, every DEX, `resources.arsc`, launcher
resources, Cobra and minimal/shared ZIPs remain byte-identical to signed436.

The chooser executable/UI is unchanged; only Infinity's truthful last-updated
label advances. Player, provider, Search routing, service/persistence/shutdown
source and user data are untouched. No shutdown test or physical installation ran.

Evidence:
- [Every changed APK member, including signatures](results/delivery437/COMPLETE-APK-DELTA.json)
- [All non-signature member hashes, signed436 versus signed437](results/delivery437/ALL-APK-MEMBERS.json)
- [Independent matching ZIP/APK comparison](results/delivery437/MATCHING-COMPONENTS.json)
- [Original-certificate verification](results/delivery437/CANDIDATE-SIGNATURE.txt)
- [Individual review of 90 functional members](results/MEMBER-SCOPE-REVIEW.json)
- [Full-skin evidence and exact limits](results/FINAL-FULL-SKIN.json)
- [Navigation/readiness matrix](COVERAGE.md)
- [Focused Fold acceptance procedure](FOLD-ACCEPTANCE.md)

## Device-only and unsupported coverage

No compatible Android runtime was available; the known broken emulator was not
rerun. Android 17/Fold, real provider failures/cancellation, all themes, fold/rotate,
PiP/playback return and device frame pacing remain for physical acceptance.
Full-skin Linux used QA directory content and dependency registrations, not real
providers or protected services. Home busy projection and unsupported-window
fallback are source checked; native runtime captures reached Videos from all
three origins. Windows without a verified drawer projection retain native busy
UI; required progress/error dialogs remain. External artwork/provider work with
no trustworthy lifecycle signal is not assigned fabricated loading state.

Preparation run 41193823006 stopped before APK creation because a relative path
was passed to the unchanged verifier, which requires an absolute root. The call
was corrected; run 41193983471 passed all checks. No check was bypassed and only
one signed APK candidate was produced. Earlier failed renderer setup evidence is
retained and excluded from passing results. `results/delivery437/STATUS.json` is
the final delivery status; older checkpoint status files remain historical.
