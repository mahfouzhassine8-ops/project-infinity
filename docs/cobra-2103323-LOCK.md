# Cobra Pro 2103323 — user-approved locked baseline

Locked at the user's explicit instruction on 2026-10-07 (America/Detroit):
“Okay this is the new bace lock it”. This record makes 2103323 the authoritative
Cobra Pro base. It preserves the already verified APK as built; no APK rebuild or
application source change accompanies the lock.

## Exact approved package

- Package: `com.projectinfinity.kodi`.
- APK: `Infinity-2103323-Cobra-Sports-Live-RC1.apk`.
- Version code: `2103323`.
- Version name: `1.0.9-Cobra-Sports-Live-RC1`.
- Size: `157925831` bytes.
- SHA-256: `1ab9354722f5f36c0441f0a604ff38ee8ee5beec11eceaeb415aeef247ae8055`.
- Signing certificate SHA-256: `d7adeb68e9341596a02bd3262b737a0f45fc6e771ed7e60285437e833b58c6d7`.
- APK build/source commit: `5de1ce637d136ab6ae737303e758ad96b092cc57`.
- Successful validation run: `37574574345`.
- Locked branch: `locked-cobra-2103323-sports-live-user-approved-20261007`.
- Delivered Library file: `libfile_2bf3251b593c819182f76fa50bd152f1`.

## Previous rollback preserved

- Previous locked base: Cobra Pro `2103322`.
- APK SHA-256: `1e25361e32dad7b7cc5a6470b2a98b1f5bb9942b3241306571c8aea9b6beff64`.
- Source commit: `712fd77bf5fa343f543fa8f6a1f042e90ad4f13b`.
- Its rollback build and source remain unchanged.

## Verified scope

- 167 automated tests passed, including 16 new Sports feed/ticker tests and all
  151 parent regression tests.
- All 15 supported league configurations are covered. The live ESPN endpoint
  snapshot returned 30/30 successful requests across current and previous dates.
- Source comparison changed only `InfinityLiveActivity.java.in`; the other 253
  source files are identical to 2103322. Protected Java tokens and
  `CobraProUi.java.in` are unchanged.
- APK preservation checks passed for 4,168 payload entries, protected compiled
  code, native engine, assets, resources, package identity and permanent signer.
- Skin remains `skin.infinity.diggz` version `1.0.5.201`; no preference reset or
  data migration was introduced.
- Detailed receipts, the exact source scope, and endpoint observations are in
  `Cobra-2103323-Sports-Audit-Evidence.zip`.

## Validation limits

This user-approved lock records the verified build and automated checks. It does
not claim physical-device acceptance or authenticated real-provider playback.
The live endpoint snapshot is one observation and cannot establish continuous
provider freshness or actual ticker delivery on the user's device. Those remain
unverified. The existing enabled-ticker setting and original Sports UI are
preserved.

Historical candidate-only reports predate this user-approved lock. This record
is authoritative for lock status. Future repairs must start on a forward branch
from this locked baseline and preserve both 2103323 and rollback 2103322.
