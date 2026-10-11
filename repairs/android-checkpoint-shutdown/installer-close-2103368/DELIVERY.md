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
verified. The subsequent physical phone shutdown test passed: all 17 required
owners were durable, with zero blockers, checkpoint save and shutdown
authorization confirmed, and engine death observed. The coordinator reached
COMPLETE in 9.427 seconds.

Acceptance evidence is `Infinity-Diagnostics-20261011-133450.zip`, SHA-256
`908336b938f77c265e07869a7723fefeeda2464c85ef80dd26abdd8ba0e58fcd`,
session `b7934632-bd23-4b44-97de-fb76326c013f`, PID 27311.
The native receipt matches the final native status; its JSON SHA-256 is
`9bdd55b82ba33b84a76112febd2cdcfc05317260dfb12255178f836a3cc1d348`.

The user explicitly designated 2103368 an official candidate and requested
the lock on 2026-10-11: "Lock. This is officially a candidate".
The exact signed APK and source above are now the locked official candidate.
See LOCK.json for the acceptance record and preservation rules. The protected
2103365 rollback baseline remains retained. This documentation lock does not
rebuild or publish a production release.

The accepted phone has Health Center 2.5.18; the separate 2.5.19 update is not
part of this accepted installation. Four failed installer business outcomes
were durably settled and did not block shutdown. Their persistence acceptance
does not assert successful add-on installation. See DIAGNOSIS.md for the
original investigation and evidence limits.
