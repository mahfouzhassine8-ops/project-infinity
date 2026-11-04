# Kodi 2103452 — original-key physical Fold testing candidate

[Download APK archive](https://github.com/mahfouzhassine8-ops/project-infinity/actions/runs/41742368066/artifacts/13282546349) · [Matching component ZIP archive](https://github.com/mahfouzhassine8-ops/project-infinity/actions/runs/41742368066/artifacts/13282361545) · [Successful signing run](https://github.com/mahfouzhassine8-ops/project-infinity/actions/runs/41742368066) · [CI preservation/signing evidence](https://github.com/mahfouzhassine8-ops/project-infinity/actions/runs/41742368066/artifacts/13283010363)

Extract `Infinity-2103452-Combined-Original-Signer.apk` from the APK archive.
Package: `com.projectinfinity.kodi`; versionCode `2103452` (higher than451).
Exact signed APK size: 778,743,553 bytes.
Signed source: `f5b6dbb22bfa0f0ee3d540f7566baa06128e07ac`.
Native source/build: `765b92bc8af1452ffc2bbb19a03a3de229a90255`, run41729462691.
Owner preparation: source7e3d4bf5070777e777838bbb819d35b267cb23f4, run41741416133.

APK SHA256:
`efc24cc53e25675360bb70a2c8c0122cfc107f99035d04c957265d08206f6729`

Original permanent certificate SHA256 (SDK v1/v2/v3 verification passed):
`d7adeb68e9341596a02bd3262b737a0f45fc6e771ed7e60285437e833b58c6d7`

[All five deliverable checksums](evidence/SHA256SUMS-2103452.txt).
These are the actual APK/component ZIP hashes, distinct from the GitHub artifact
archive hashes in [DELIVERY452.json](evidence/DELIVERY452.json).

## Authorized changes and exact preservation

The existing compiled engine is reused; no native rebuild or additional repair
was performed for packaging. The engine contains only the five reviewed P0
source edits over the exact9411-file native foundation. Its SHA256 remains
`f89a40b5653c0091a06edd44f6ac5cdf056a649301b6751ee638c8ba88db9674`.

Actual signed451-to-downloaded-signed452 comparison found exactly three changed
nonsignature APK members:

- `lib/arm64-v8a/libkodi.so`: the source-bound watched receipt/display-dispatch repair.
- `AndroidManifest.xml`: typed versionCode only,451 to452; normalized manifest exact.
- `assets/experience-component-updates.properties`: truthful Infinity version452;
  Cobra remains445. No chooser executable/appearance change.

The remaining7611 payload members are identical, including all five DEX,
resources/skin/add-on/provider payloads and46 other native libraries. Signatures
and ZIP alignment/container layout are regenerated through the original signer.
All119 protected Java contracts, ownership rules and the accepted pointer remain
unchanged. Cobra.zip and MINIMAL_ANDROID_CONTRACT.zip remain byte-identical to451.
Every published component payload/DEX partition was compared with the actual
signed APK; the frozen manifest component retains its existing version-normalized
assembler contract. Preview's engine/UI/resume memory/routing and Cobra code/data
were not changed. No user profile, database, setting or file was modified here.

See [signed APK comparison](evidence/SIGNED452-APK-PRESERVATION.json),
[every APK member hash](evidence/SIGNED452-ALL-APK-MEMBER-HASHES.json), and
[published APK/component binding](evidence/PUBLISHED452-VERIFICATION.json).

## Results and limits

| Check | Result |
| --- | --- |
| Existing14 watched-job and7 lifecycle host cases | Retained PASS; actual code/control-flow peers and SQLite fixtures, not Android |
| Actual native barrier header / protected-resource refusal | PASS; existing extra refusal predicate retained |
| Full matching ARM64 engine / retained ABI | PASS, run41729462691; no rebuild |
| Five selected release/security/preservation contracts | PASS; no app/shutdown suite |
| Official preparation/source/artifact/generation/owner/sole-signer gates | PASS |
| Original permanent signature / package / higher version / alignment | PASS; install-over identity requirements met |
| Actual downloaded artifact SHA/CRC, APK member and all4 component matches | PASS |
| Actual Android app, shutdown, database callback/final fence, surface lifecycle and ANR | NOT RUN; remote target unavailable; physical Fold testing pending |
| Historical job973/token976 item/provider route | UNKNOWN; no local-video inference |
| Physical acceptance / final lock | PENDING USER ONLY; no automatic promotion |

This is a scoped testing candidate, not proof that both historical failures are
fully fixed. The bounded reviewed native-database job/callback path gains a
verified receipt. Recursive/UPnP/PVR/unreviewed paths remain Unknown and blocking.
The checkpoint-active native loop can service the real display setup/destroy
callbacks without admitting ordinary writes or acknowledging cleanup early.
Android behavior remains unverified; neither host success nor compilation proves
ANR clearance or complete real-provider shutdown durability.

## Safe physical test

Follow [FOLD-P0-TEST-PROCEDURE.md](FOLD-P0-TEST-PROCEDURE.md).
First close the existing app normally and let verified saving finish. If the
current session reports CHECKPOINT_FAILED/unresolved saving, leave it intact and
capture diagnostics; do not force-close or install over that unresolved save.
No uninstall or data clearing is required or authorized.

Independently check normal Close/reopen, a disposable single-item watched update
with actual readback, Stop/Back/Home, screen-off/on/background return and genuine
front/inner Fold transitions. Test the combined failed-checkpoint lifecycle case
only if it occurs naturally; otherwise record NOT REPRODUCED. Preserve all
Unknown blockers. Retain private diagnostics with exact app/native/session/time
identity and report PASS/FAIL/NOT RUN accurately. The user alone accepts or rejects
this candidate. Original451 APK/source and all recovery locks remain unchanged.

## Release protection handling

The original package/signature/ownership/protected-contract gates were retained.
The existing permanent policy permits engineering-reviewed, Fold-pending package
creation independently of behavioral/shutdown testing. The user's current
explicit physical-candidate authorization is recorded in
[FOLD-CANDIDATE-AUTHORIZATION.md](FOLD-CANDIDATE-AUTHORIZATION.md).

Only the existing combined workflow accesses the original key through unchanged
`assemble.py sign`. Its branch/owner/version selection was extended narrowly to
this candidate, with an added exact451 recovery-lock check. The two existing
unsigned P0 workflows were audited and added to the reviewed inventory after the
unchanged signer policy correctly refused them as unreviewed. Retired signers
remain disabled; no key, credential, ownership classifier, runtime safeguard,
timeout or accepted-pointer validation was weakened. Runtime evidence is explicitly
blocked/pending, never fabricated as PASS.
