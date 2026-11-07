# Infinity Search shared settings acceptance — verified engineering finding

Date: 2026-11-07. **No released repair, no APK.**

## Existing architecture and observed defect

Infinity's original `Files.GetDirectory` calls invoke the installed provider's native search, not a replacement search engine. The user trace captured 31 returned WatchNixtoons2 rows and 2 returned Crew rows, all discarded afterward by `_provider_result` when the **provider's own** settings file changed.

The installed response signature includes the complete settings-file stat tuple (device/inode/size/mtime/ctime). This establishes that the file was rewritten, **not** that the search result is wrong.

## Actual experiments

1. Protected source restoration tests: 7/7 PASS, [run 42361785232](https://github.com/mahfouzhassine8-ops/project-infinity/actions/runs/42361785232).
2. Representative settings mutation matrix: 4/4 PASS as a *diagnosis*, [run 42362290378](https://github.com/mahfouzhassine8-ops/project-infinity/actions/runs/42362290378).
3. Existing shared native-provider Search UI routing: 9/9 host PASS, [run 42363351875](https://github.com/mahfouzhassine8-ops/project-infinity/actions/runs/42363351875).
4. Fail-closed, request-bound settings-proof policy MODEL: 15/15 host cases PASS, [run 42417182606](https://github.com/mahfouzhassine8-ops/project-infinity/actions/runs/42417182606).
5. **Isolated only**, the alternative fresh-provider-owned-result relaxation: 12/12 host tests demonstrate that synthetic Crew/Nixtoons results would survive while source, dependency, cancellation and profile checks still work. [Run 42417751874](https://github.com/mahfouzhassine8-ops/project-infinity/actions/runs/42417751874).

## Why the simple relaxation is rejected for release

The same candidate also **accepts** an actual meaningful configuration edit and an A→B→A edit-and-revert while the native request is running. These are explicitly modeled tests, not assurances. It violates the existing strict negative requirements. The known positive results cannot be promoted by relabeling those cases as success.

The alternative code remains isolated at `work/infinity-search-provider-owned-fresh-results-20261107`. Neither it nor the model branch is installed or applied to any protected source.

The fail-closed policy MODEL requires a native-verified per-request timeline: exact request binding, complete ordered writer coverage including direct-file writers, effective search-configuration classification of **each** mutation, no observer gaps/overflows, stable sources and checkpoint/cancellation handling. The current API does **not** produce that authenticated timeline; Python-provided JSON cannot attest it. An XML endpoint comparison or Kodi callback alone cannot prove it.

## Next actual engineering gate

Implement and **source-bind** the native observer to the existing bounded `CScriptRunner` Search lease and Kodi settings writers without changing third-party search logic; or identify an equivalently provable snapshot-consistency mechanism. It must reject external/unobserved file writes and meaningful intermediate changes, yet permit proven provider-owned bookkeeping. Only after that passes native and host negative tests should `_provider_result` be updated and its genuine native runtime behavior verified.

Do not claim native API availability, real direct-file writer coverage, or a completed fix from these host fixtures.

**Release decision: HOLD.** No unsigned workaround ZIP, signer change, partial APK, user reinstall or repeated Fold crash collection. The protected baseline `86d5b5e2`, unified Search source `c75e6de6`, separate native keyboard `92bb6ecb`, graphics candidate `4ee6a5f`, all Cobra/Preview locks, and installed APK remain untouched.
