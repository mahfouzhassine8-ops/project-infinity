# 2103368 delivery

- Source: `2515c1a281abf9e57cfdbf570244c69f751a1437`
- Successful complete Android, native and signed package run:
  https://github.com/mahfouzhassine8-ops/project-infinity/actions/runs/38137092930
- APK: `Infinity-2103368-Installer-Close-RC1.apk` (159,245,111 bytes)
- APK SHA-256: `a6b22a0b761ddc9eba108e1f235001c961592dd911edff8c48a0abc6fb3592c8`
- Permanent signer SHA-256: `d7adeb68e9341596a02bd3262b737a0f45fc6e771ed7e60285437e833b58c6d7`
- Evidence: `Infinity-2103368-Installer-Close-Evidence.zip` (16,592,969 bytes)
- Evidence SHA-256: `5df3e68b952b2653b9d9aa7de10256722fba7bd340d79e5df4a9096ff5425ceb`

Both files are saved and available for delivery. Transfers match the immutable
CI artifact hashes. APK native and add-on bytes match their source-associated
proofs. v1/v2/v3 signatures verify; package is `com.projectinfinity.kodi`, version
code 2103368, version name `1.0.9-Installer-Close-RC1`.

All 4,169 compared protected 2103365 entries are unchanged. Original 2103365
and 2103367 APK hashes still match. Completed 2103367 integration assets and
all 17-owner close requirements are preserved.

The reproduced storage-ancestor permission defect is fixed and regression
verified. Physical close remains unconfirmed; the diagnostic supplied before
this repair has no syscall error. See DIAGNOSIS.md for the evidence limits.
Install as an update, retry add-on installation, then test Close and retain a
new diagnostic if it fails. Release remains unlocked pending physical acceptance.
