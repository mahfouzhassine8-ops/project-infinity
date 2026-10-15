# Cobra 2103280 — user-approved locked baseline

Locked at the user's explicit request on 2026-10-01 (America/Detroit): "Lock it", following delivery of the verified 2103280 APK.

## Exact approved package

- APK: `Infinity-2103280-Audit-Followup-RC1.apk`
- Version code: `2103280`
- Version name: `1.0.9-Audit-Followup-RC1`
- Size: `93536543` bytes
- SHA-256: `e12654c0d81b6b04c4507f2c8bfde9e92761ab5a93ac16b86a3f89f9b7656870`
- Signing certificate SHA-256: `d7adeb68e9341596a02bd3262b737a0f45fc6e771ed7e60285437e833b58c6d7`
- Approved source/report commit: `39ff28b4a35c1f39b09249fd55cb7efb5ce4c9ce`
- Build/runtime source commit: `29ec5acd15d3565df665e340de71ae610193f834`
- Parent locked baseline: `60e1893d8591a29fab7e952ea2d3caedb0b13fa5` (2103279)
- Delivered file ID: `libfile_7c7140018ed88191868e5d40ba5f3e5d`

## Verification and preservation

- Successful build/signing and Android runtime run: https://github.com/mahfouzhassine8-ops/project-infinity/actions/runs/36818383789
- 522 regression tests passed; 20 protected renders remain byte-identical.
- Both recording runtime scenarios passed after installation over 2103279. Saved recording bytes, local decode, scrubber seeking, rewind, Smart Return, and cleared completed-recording state were checked.
- Package artifact: `11142822751`, ZIP SHA-256 `c9a45d77c1b48be3b34960cac1bcb888032eaa88b168e64284177daf909f1ec4`.
- Runtime artifact: `11142569561`, ZIP SHA-256 `b3b54afa8cde668d2614e8c7cbb4fad302d9d8a71e5c496fac5773ae492af480`.
- All 46 native libraries, 4,039 assets, and Android resources remain byte-identical.
- No rebuild or application source change accompanies this lock. The earlier 2103279 lock remains unchanged.

## Audit status

This user-approved lock does not declare the entire end-to-end brief complete or assert physical Fold acceptance. The documented remaining app-owned combinations and physical/device/account-dependent checks remain open. Continue any repairs on a new forward branch from this baseline; never modify this locked branch.

Historical candidate-only reports predate this user-approved lock. This record is authoritative for lock status.
