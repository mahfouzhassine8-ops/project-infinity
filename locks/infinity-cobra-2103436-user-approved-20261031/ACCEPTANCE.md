# Signed 2103436 — user-approved working lock (October 31, 2026)

**User instruction:** "Lock it for now its good but I found somthing else but that will have to wait."

**Decision:** Preserve the EXACT signed 2103436 install-over candidate as the current working baseline for **both installed experiences**, with the user-approved **Cobra Cards drawer sizing correction**. This is provisional working acceptance ("good for now"), **not** a claim that every UI scenario or automated runtime test passed. The user reports a separate later issue but has **not disclosed or authorized** its repair; do not investigate, interpret, or change anything in response until separately instructed.

## Exact signed release identity — immutable source snapshot

| Item | Value |
|---|---|
| Android package | `com.projectinfinity.kodi` |
| Combined APK versionCode | `2103436` |
| Original-key signed APK | `Infinity-2103436-Combined-Original-Signer.apk` |
| Signed APK SHA256 | `ff8e7ec16cb10028aef50579161de92b205e97ca8131195098753fb3821bdbc6` |
| Original certificate SHA256 | `d7adeb68e9341596a02bd3262b737a0f45fc6e771ed7e60285437e833b58c6d7` |
| Exact signed source SHA | `7bbe08363b493146ca7ed67cb872e9a98b1d888b` |
| Original-key signed workflow | [41182386594](https://github.com/mahfouzhassine8-ops/project-infinity/actions/runs/41182386594) — SUCCESS |
| Exact signed APK artifact | [13035124135](https://github.com/mahfouzhassine8-ops/project-infinity/actions/runs/41182386594/artifacts/13035124135) |
| Matching owner ZIPs | [13035079327](https://github.com/mahfouzhassine8-ops/project-infinity/actions/runs/41182386594/artifacts/13035079327) |
| Immutable-by-convention source reference | `lock/infinity-cobra-2103436-user-approved-20261031` → `7bbe08363b493146ca7ed67cb872e9a98b1d888b` |

**Prior baseline:** User-locked signed 2103435, commit `e0c6153588992001d84076d33fdf8f0d676c0d00`, lock `lock/infinity-cobra-2103435-user-approved-20261031`. Preserve previous signed versions and their corresponding APKs/hashes. Rejected 2103434 remains rejection evidence, not the fallback.

## Exact ownership, scope and preservation

- **Changed functional owner:** Cobra only — fix for Cards drawer-induced incorrect responsive width, based on `70c0e3e0ad6cf3100cce6bc599be4e79d424e803`. Native `InfinityLiveActivity.cobraLayoutGuide` and `CobraCardsLayout.State.physicalLayout` use the Cards-only `CobraCardsDrawerViewport.location` helper. This coordinates with existing drawer translation; no drawer animator, layout design, player or storage system is redesigned.
- **Unchanged owner:** Infinity remains EXACT 2103435 functional payload. Preserve skin, Command Center, loading experience, providers, playback and all module assets; **no Infinity development** was approved for this 436 feature. Preserve chooser executable/UI, Minimal Android, launcher icons, 47 native libs and protected shutdown.
- Official signing/preservation run compared signed 435 and signed 436: exactly **three permitted changed nonsignature APK members**: `classes4.dex`, versionCode-only `AndroidManifest.xml`, and `assets/experience-component-updates.properties` (Cobra 436, Infinity still 435); **7,611 other members** unchanged. Signature-related archive changes are expected from re-signing.
- The preserved user experience includes Cards on both cover and inner displays, all other Cobra view modes, drawer actions, fullscreen/PiP/More, decoder/session, user profiles/settings, EPG, favorites, original signing ID, and install-over data. No user-data clear/uninstall/migration or shutdown test performed by the lock action.
- Protected signed 436 artifacts and source must **NOT** be overwritten, rebuilt in place, rebased, or silently promoted from current engineering head. Do not use later QA commits as a substitute for the signed source identity.

## Verification and known limits — preserve truthfully

- Five selected Robolectric SDK35 host tests passed (drawer sizes, fold/rotation, insets/ownership, front/other-mode negative controls, interrupted motions). Synthetic player/guide fixtures are **not** real decoder or physical Fold verification.
- Successful original-key signing and mandatory actual APK/component preservation verification: run **41182386594**.
- Two later Android 17 emulator journey runs **41182990993** and **41183933643** ended **FAILURE**, not PASS; the latter stopped at the safety check `Repeated or unrecognized Android dialog refused after one OK`. Their failure evidence remains preserved. Do not relabel these runtime checks as successes or claim complete Android emulator acceptance.
- Codex did **not** review original 20728/20729 video bytes or static PDF/JPEG frames in its workspace due to file-access limitations. This is a verification limitation, not evidence of a product defect.
- **User's own present statement** provides provisional real-device acceptance: **"for now its good"**. It does not identify what the later issue is, which feature it affects or authorize more changes. Do not speculate. No automatic release promotion or unsanctioned tests are needed to honor the requested source/artifact lock.

## Future development policy / freeze

1. **STOP** work on this approved 436 artifact. Keep this exact locked release as the working recovery base. No ongoing rebuilds, extra QA loops, speculative hardening or new releases are requested by this lock.
2. **Defer the unreported new issue** until user chooses to discuss it. Do not automatically create an issue-specific task, edit files, or investigate a presumed defect.
3. When user authorizes new work later, start a *new* development branch from exact signed 436 source commit. **One experience changed per release**, with the other frozen unless explicitly authorized.
4. Always compare against exact signed 436 APK/owner content. No unrelated edits, loss of user data, automatic lock changes or unreviewed compiler/resource differences. Subsequent testing APK gets a separate version number and user device acceptance before any future lock.
5. This is a Git reference and acceptance record, **not a GitHub branch-protection enforcement guarantee** or a change to the installed device. GitHub artifacts may have retention expiry; retain backup of the signed 436 APK and owner ZIPs.

**STATUS: USER-APPROVED 2103436 WORKING LOCK; NO NEW BUILD OR PRODUCTION CHANGE FOR THE LOCK.**
