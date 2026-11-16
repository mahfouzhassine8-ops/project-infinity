The owner-authorized fast QA pair is original-signed and passed Android install-over verification. It includes only the reviewed closed-file shutdown observer, narrow Silent Mode promotion policy and bounded Cast discovery. Continue Playing, Otaku Watchlist and Empty Shell remain deferred and unchanged. Signed2103500 remains protected; no accepted-baseline pointer is promoted.

| APK | Version | SHA-256 |
| --- | --- | --- |
| Combined QA | 2103502 | `f35b6e6015d91185d76a12b4f21cec17c9eaa65ef07b17d8fed91a547dfffb28` |
| Forward recovery restoring500 functionality | 2103503 | `5d4b9435b3df094878fd99629f0a365fafb628af72e9e98ac751a95e021cab76` |

Both use package `com.projectinfinity.kodi` and the original certificate SHA-256 `d7adeb68e9341596a02bd3262b737a0f45fc6e771ed7e60285437e833b58c6d7`. Actual v1/v2/v3 signatures passed the unchanged original signer workflow397702717 and independent APK verification.

The signed QA preserves7772 of7776 payload members byte-for-byte. Only `lib/arm64-v8a/libkodi.so`, `classes6.dex`, the versionCode-only manifest and Infinity version label differ. Recovery preserves7774, changing only version metadata. Cobra2103445, providers, Search, tracking, profile/database assets, skin, existing Cast relay/remuxing and unrelated APK members remain unchanged. No owner profile or database was accessed or modified.

| Gate | Evidence |
| --- | --- |
| Reused full ARM64 engine and exact ABI | PASS run43774504911, engine `ed2d955d1825bf838ea50a712782e54b69926d40605270a2f241efd913202ee7`; no native rebuild |
| Retained observer Android bridge | Eight PASS run43771832750, bound to earlier observer-only engine. Real error/SQLite/durability/late-write negative cases retained |
| Retained Silent Mode classifier | 39 host checks PASS; final policy compiled in reused engine; actual installed-source coverage and GUI behavior unverified |
| Retained Cast discovery SDK lifecycle | 21 PASS run43762472390; physical receiver discovery/playback unverified |
| Completed unsigned assembly reused | PASS run43781637786 |
| Exact owner registration preparation | PASS run43784613251; generations87/88; unchanged authority transition and protected contracts |
| Original-key QA signing | PASS run43785765772; source `92bef1bcf056abf58d6754354173565e56f907ac` |
| Original-key recovery signing | PASS run43786312699; source `4c6bc0b4a06828f43639761e481c1d42d2fcbc34` |
| Actual Android install-over and recovery | PASS run43786801531:500→502→503; same UID10216, data directory and first-install time; no launch, uninstall, reset or downgrade |
| Astra review | PASS exact registration lineage, actual signed APK archives/certificates/member preservation, original signing route, install receipt and publication source |

Install2103502 over the existing app using Android's normal Update action. Do not uninstall or clear data. Reserve2103503 for recovery if needed; its higher versionCode restores500 functionality over502. Recovery is not a second routine installation.

One owner Fold acceptance session remains. PackageManager verification establishes upgrade/recovery compatibility; it does not prove full application startup/shutdown, owner-profile contents, physical Fold behavior or TV playback. No deferred repair is claimed as fixed.

Only the audit catalog was expanded for the three already reviewed unsigned500 CI workflows; the original signing implementation, ownership gate and durability guards remained unchanged. Astra required that only the catalog's authority hash change, preserving every other protected source pin.

Signed QA artifact: https://github.com/mahfouzhassine8-ops/project-infinity/actions/runs/43785765772/artifacts/14189813969

Signed recovery artifact: https://github.com/mahfouzhassine8-ops/project-infinity/actions/runs/43786312699/artifacts/14189769692

Publication PASS: run43787698779, source `2729d9f1dfee49bf7d2a225df51560d830df98a6`. Both direct APK links returned HTTP200 with exact sizes; the public checksum file was downloaded and verified. GitHub asset digests equal the independently reviewed APK hashes. Final metadata is in `QA-FINAL-DELIVERY.json`.

Release: https://github.com/mahfouzhassine8-ops/project-infinity/releases/tag/infinity-2103502-fast-qa

Infinity-2103502-Combined-Original-Signer.apk: https://github.com/mahfouzhassine8-ops/project-infinity/releases/download/infinity-2103502-fast-qa/Infinity-2103502-Combined-Original-Signer.apk

INFINITY-2103502-QA-VERIFICATION.zip: https://github.com/mahfouzhassine8-ops/project-infinity/releases/download/infinity-2103502-fast-qa/INFINITY-2103502-QA-VERIFICATION.zip

Infinity-2103503-Combined-Original-Signer.apk: https://github.com/mahfouzhassine8-ops/project-infinity/releases/download/infinity-2103502-fast-qa/Infinity-2103503-Combined-Original-Signer.apk

INSTALL-AND-RECOVERY.md: https://github.com/mahfouzhassine8-ops/project-infinity/releases/download/infinity-2103502-fast-qa/INSTALL-AND-RECOVERY.md

SHA256SUMS: https://github.com/mahfouzhassine8-ops/project-infinity/releases/download/infinity-2103502-fast-qa/SHA256SUMS
