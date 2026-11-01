# INFINITY/COBRA 2103445 — USER-APPROVED LOCK (2026-11-01)

**2103445 is now the user-approved combined Infinity/Cobra signed baseline.**

The user explicitly instructed **“Lock it”** after delivery and discussion of the signed **2103445** Cobra rotation and Fullscreen audio refinement. This acceptance authorizes recording the exact delivered signed source as the new baseline, **without claiming any physical Galaxy Fold tests or reclassifying historical failed/blocked tests**.

## Exact identity — pin only the successful original signed source

- User-approved reference: `lock/infinity-cobra-2103445-user-approved-20261101`
- **Exact signed source commit:** `6cf75639a46ec6b0c858ae32abc102450fdc0974`
- Signed APK: `Infinity-2103445-Combined-Original-Signer.apk`
- **Signed APK SHA-256:** `b7e78393ade7e52d8653823a0ad72ae99614a5a8e0b6cdedf5d5d15a9e643400`
- Permanent original signing certificate SHA-256: `d7adeb68e9341596a02bd3262b737a0f45fc6e771ed7e60285437e833b58c6d7`
- Package: `com.projectinfinity.kodi`; versionCode: `2103445`
- [Successful original-key signing run 41349763470](https://github.com/mahfouzhassine8-ops/project-infinity/actions/runs/41349763470)
- [Actual signed APK artifact](https://github.com/mahfouzhassine8-ops/project-infinity/actions/runs/41349763470/artifacts/13100188760)
- [Exact matching component ZIPs](https://github.com/mahfouzhassine8-ops/project-infinity/actions/runs/41349763470/artifacts/13101240484)
- [Signing/integrity evidence](https://github.com/mahfouzhassine8-ops/project-infinity/actions/runs/41349763470/artifacts/13100876195)
- [Authoritative 2103445 original delivery record](../cobra-2103444-rotation-audio/DELIVERY.md)
- [Component checksum receipt](../cobra-2103444-rotation-audio/delivery445/SHA256SUMS)

## Accepted change scope (exact delivered 2103445)

1. **Universal Cobra rotation button** alternates auto-rotation activation with locking **the exact currently displayed orientation**. Applies across installed Cobra modes and their Fullscreen states.
2. **Fullscreen Mute/Unmute** appears between Channels and Display in every Cobra mode's Fullscreen toolbar, using player-owned audio state, previous volume restoration and Multi-View selected audio stream ownership.
3. All other accepted **2103444** Cobra functionality and performance optimizations are retained; no extra features are approved by this acceptance.

**Preservation evidence:** Relative to signed 2103444, 7,611 nonsignature payload members are unchanged; no payload members added/removed; all 47 native libraries are unchanged. The entire Infinity ZIP and 7,516 Infinity payload members are byte-identical, with the original **Infinity 2103437** component preserved. The minimal/shared component and native Kodi, shared Android/Media3 executable code, resources, launcher icons, chooser executable and shutdown owner remain unchanged. Chooser **version metadata** truthfully advances Cobra's version. The only changed payload members are Cobra's `classes4.dex`, `AndroidManifest.xml` typed versionCode and `assets/experience-component-updates.properties`; the original signer regenerates signature records. Full bytes/hashes under `delivery445/`.

## Verification limitations — preserve historical evidence

- Original-key signature v1/v2/v3, exact APK/component correspondence, package identity, ZIP alignment, release preservation gates and host tests **passed** as documented in `DELIVERY.md`.
- Five new targeted rotation/audio host checks and one post-sign Pro Sports toolbar host check pass, plus selected unchanged behavior regression checks. Some historical UI fixture failures also reproduce on the unchanged 2103444 baseline and remain **failures**, not silently upgraded to PASS.
- **No actual 2103445 Android runtime matrix, physical Galaxy Fold installation/sensor tests, audible output tests, real PiP/decoder/session continuity tests or physical fold/window acceptance have been reported.** These stay unverified despite this user-approved lock.
- This lock contains **no newly executed app tests, APK rebuild, signing, install, data operation, shutdown test or code change**. The source to lock is the successful signer's source, not the later delivery documentation commit.
- The signed 2103445 is approved as a **version baseline**, not as proof of unperformed physical tests.

## Recovery and preservation

The prior signed **2103444** is retained unchanged at `lock/infinity-cobra-2103444-user-approved-20261101`, source `1b7a4ef16524854fab77a1c974538aee8a1132bb`. Signed **2103442** and older recovery references/artifacts remain preserved. Future work must start from the exact `2103445` accepted component vector, on a **separate work branch**, preserving unrelated Infinity, Cobra and Kodi components. No additional edits to this accepted reference without new explicit authorization.

**GitHub protection limitation:** this branch reference records the frozen source, but does not itself guarantee server-enforced immutability. If ruleset protection is still unavailable to the connected GitHub integration, a repository administrator must separately enable **Restrict updates** and **Restrict deletions** for the exact new lock branch. Do not misrepresent a created branch as server-protected.

GitHub Actions artifacts were available at acceptance check; current GitHub listed retention expiration `2027-01-30T21:00:54Z`. Lock references and documentation do not extend artifact retention.
