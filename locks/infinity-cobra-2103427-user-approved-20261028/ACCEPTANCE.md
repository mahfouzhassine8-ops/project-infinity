# User-approved combined Infinity/Cobra release — 2103427

**User decision:** “Okay lock what we have it's perfect” (2026-10-28, America/Detroit). Freeze the **already signed** 2103427 combined release without modifying its bytes. The user has approved retaining this release; no new individual device performance measurements or fresh shutdown tests are implied by this statement.

## Exact frozen signed release
- Repository: `mahfouzhassine8-ops/project-infinity`.
- Immutable-by-convention source snapshot: `lock/infinity-cobra-2103427-user-approved-20261028` **at exact signed-source SHA** `782242090483982c39a78f9c4da932a4751bdafc`.
- Signed APK: `Infinity-2103427-Combined-Original-Signer.apk`, package `com.projectinfinity.kodi`, versionCode `2103427`.
- APK SHA256: `cd0c8ab5c77067e508baea0ad7d5207b3d6c73775b86387d4099a67cfe4215ca`.
- Original signing certificate SHA256: `d7adeb68e9341596a02bd3262b737a0f45fc6e771ed7e60285437e833b58c6d7`.
- Successful signing workflow: https://github.com/mahfouzhassine8-ops/project-infinity/actions/runs/40769526963
- Signed APK artifact: https://github.com/mahfouzhassine8-ops/project-infinity/actions/runs/40769526963/artifacts/12852945082
- Exact matching four component ZIP artifact: https://github.com/mahfouzhassine8-ops/project-infinity/actions/runs/40769526963/artifacts/12852670776
- Detailed delivery receipt, checksum list, host tests and disclosure of outstanding gaps: `repairs/infinity-only-performance-2103425/continuation/DELIVERY.md`, `COMPLETION-LEDGER.md`, and `results/FINAL-CI-RECEIPT.json` at documentation commit `709386dff69d2b62e056987fa9f715a7f372182c`.

## Approved component identities and scope
- Infinity component `2103420.isolation.1.performance.2`, Command Center `0.3.5.51`, skin `1.0.5.248`. Retain both P0 corrections: Trakt/Infinity Movie/TV rail isolation and exact TV Progress Shows routing, plus earlier signed 2103426 performance changes and 2103427 bounded projection work.
- Cobra remains at `bundled-2103420.isolation.1.fold-reflow.2`, last-updated label `2103423`; exact original COBRA ZIP SHA256 `eb30afa0e1ab9f50da897db27a604cb79a47059ff355c763dc7d7c955ddbcb6b`.
- Chooser presentation and behavior preserved. The only approved chooser delta is version metadata showing Infinity `2103427`, Cobra `2103423`, app `2103427`.
- Shared Android-contract ZIP SHA256 `6e93a1eb8e47f7fc9bc6f1dbc9208b555e2e62445ca2a3065d4e17a3b473ba33`; all 47 native libs and 5 DEX files unchanged from 2103425. Shutdown/persistence binaries remain frozen; shutdown tests were NOT RUN in this corrective continuation.
- Original 2103425 recovery ref `lock/infinity-cobra-2103425-fold-approved-chooser-20261028` at `db730100a3bfea7e06d2e6c3434e89aeb6fa8a15` and 2103420 historic ref `lock/infinity-2103420-user-approved-baseline-20261026` at `883c64a4de6f87077893921454de71bba850235b` remain intact.

## Freeze and evidence policy
- No changes to the frozen 2103427 source ref or installed APK; do not silently restart optimizations, move this ref, release a different candidate, or overwrite its signing authority/artifacts. Future work, if separately authorized, must use a new isolated engineering branch and a higher release version after focused verification.
- The user's approval supersedes pending release-acceptance status **as an approval decision**, not as proof every originally proposed optimization was implemented or measured. The completion ledger retains unsolved/unverified native queue, cold-start, thermal, device frame-pacing, Search and native constructor issues. No Android performance numbers or device QA logs were manufactured.
- This receipt is documentation only, separate from the exact signed source ref. It requires **no** APK rebuild, component regeneration, test rerun, or data change.
