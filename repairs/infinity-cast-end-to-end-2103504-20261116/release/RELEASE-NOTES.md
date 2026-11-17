Original-key signed internal QA derived directly from authenticated Infinity2103504. This is not owner acceptance or a baseline promotion.

Cast-owned E-AC3 audio in multiplexed MKV-to-fMP4/HLS becomes AAC-LC stereo192kbps. Original video packets and timestamps are preserved. Existing AAC/direct paths remain unchanged. No Kodi or production DEX rebuild.

- [Install2103506 QA](https://github.com/mahfouzhassine8-ops/project-infinity/releases/download/infinity-2103506-fast-qa/Infinity-2103506-Combined-Original-Signer.apk)
- [2103507 forward recovery](https://github.com/mahfouzhassine8-ops/project-infinity/releases/download/infinity-2103506-fast-qa/Infinity-2103507-Combined-Original-Signer.apk) — restores exact504 payload with higher version metadata; only use if recovery is needed.
- [SHA256SUMS](https://github.com/mahfouzhassine8-ops/project-infinity/releases/download/infinity-2103506-fast-qa/SHA256SUMS)
- [Verification receipts](https://github.com/mahfouzhassine8-ops/project-infinity/releases/download/infinity-2103506-fast-qa/INFINITY-2103506-QA-VERIFICATION.zip)

SHA2562103506: `2d0f6fa80926243934270816fdfc5f83e7ba5f421fd7882a352686999a9eae1d`

SHA2562103507: `8dfc798d14bd1352b59366922693e3c462c8a62807759eee93e17e92efb79341`

Original certificate: `d7adeb68e9341596a02bd3262b737a0f45fc6e771ed7e60285437e833b58c6d7`; v1/v2/v3 verified. Package `com.projectinfinity.kodi`.

Candidate source: `39d29d6a1d92c71ac3e6f4746d82ae5467dc7db2`. Recovery source: `2d5a2d7d5a58c657ac8aca13d5c1de12e724ca39`.

Engineering receipts: [ARM64](https://github.com/mahfouzhassine8-ops/project-infinity/actions/runs/43993371947), [actual Android JNI/relay/playback](https://github.com/mahfouzhassine8-ops/project-infinity/actions/runs/44000750859), [candidate signer](https://github.com/mahfouzhassine8-ops/project-infinity/actions/runs/44003667211), [recovery signer](https://github.com/mahfouzhassine8-ops/project-infinity/actions/runs/44004258589), [PackageManager install-over/recovery](https://github.com/mahfouzhassine8-ops/project-infinity/actions/runs/44005057424).

[Repair, root-cause limits and exact preservation report](https://github.com/mahfouzhassine8-ops/project-infinity/blob/c9f305a103d5bfb4a5c1b3ab901bae61ae939218/repairs/infinity-cast-end-to-end-2103504-20261116/release/REPAIR-AND-PRESERVATION.md). Astra independently reviewed source, actual native/Android receipts, owner proposals and signed payloads. Candidate changes exactly3 payload members: Cast library, manifest version, existing Infinity label;7,774 remain unchanged. Recovery changes only2 metadata members;7,775 remain unchanged. Cobra2103445, DEX, Kodi, modules, Search/providers, tracking, Continue Playing, shutdown, UI/Video Lock, networking, settings and data schemas remain unchanged. No owner data accessed or reset.

Physical Fold/TV video/audio, HEVC rendering, Return to Phone and normal post-Cast shutdown remain pending owner acceptance. The historical receiverERROR4 is not uniquely explained by the available logs; this audio compatibility correction is verified in focused engineering tests, not represented as physical-TV success. Existing504 limitations outside Cast remain unchanged.

Install506 over the existing app; do not uninstall or clear data. Only install507 if recovery is needed. Keep504 protected. No automatic accepted-baseline promotion.
