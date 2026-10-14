# Infinity Kodi Mobile 2103377 RC5 — LOCKED

**Approved 2026-10-14** after successful physical testing on the Galaxy Fold.

This is the **exact permanently signed APK** that passed the device tests; no production code, app version label or skin was altered to create this lock.

| Property | Locked value |
| --- | --- |
| App ID | `com.projectinfinity.kodi` |
| Version code | `2103377` |
| Version name (unchanged) | `1.0.9-RC5-Optional-Shutdown-Test` |
| APK | `Infinity-2103377-RC5-Optional-Shutdown-Signed-Test.apk` |
| APK SHA-256 | `44bc7753bbaf474403c628052dd7bed31d77148b29c33f76e36d129e98edce90` |
| Signer certificate SHA-256 | `d7adeb68e9341596a02bd3262b737a0f45fc6e771ed7e60285437e833b58c6d7` |
| Required skin | `skin.infinity.diggz` **1.0.5.211**, unchanged |
| Native source commit | `645b0e8b15c45d4c170a8b664073a87cb848b831` |
| Exact signing source commit | `eafaab0d21c1cb20646b08dfe28fea7f769d56e9` |
| Previous locked APK rollback | **2103376** |

### Verified

- Fully built native engine green: GitHub Actions **38517386755**.
- **274/274** Android regressions green: **38514680851**.
- **17/17** targeted C++ contract tests green: **38517351538**.
- Original-certificate permanent signing and byte-for-byte parent-package preservation checks green: **38520156095**.
- User confirmed RC5 Fast Close and two full-load normal shutdowns on the Galaxy Fold.
- Both device shutdown traces reached **SAFE_TO_TERMINATE**, consumed authorization, released engine owner lease and completed Recents cleanup.
- Latest final native save receipt: **17/17 required owners completed**, zero blocking errors, zero active native writers. Second shutdown **3332 ms**. First shutdown approximately **3480 ms**.

### Preserved design

Infinity Resume Hub remains the sole in-house source for local playback/resume history; Trakt remains optional, installed, usable and updateable, and not an Infinity required-save owner. Infinity Continuity continues its runtime diagnostics/reflow coordination and retires optionally at Close. All other Kodi/add-on service shutdown and genuine save/durability proofs remain intact. Existing approved UI/player features, Recents, Choose Your Experience, databases and add-ons are unchanged.

### Future development protection

This lock **supersedes 2103376 as the base for new Infinity Mobile APK candidates**; preserve 2103376 and skin 1.0.5.211 as rollback. Fork future work from the locked source; do not overwrite this APK, change its signature, remove mandatory save receipts, or redesign the now-passing shutdown sequence. Any future candidate must be separately tested and explicitly approved before promotion.

The user's personal diagnostic archive is **not included** in this public release. The lock record includes only summary metrics and its SHA-256. The physical test proves shutdown durability; it does not independently certify every unrelated UI behavior.

**Lock record:** `docs/locks/Infinity-2103377-RC5-Locked-20261014.json`.
