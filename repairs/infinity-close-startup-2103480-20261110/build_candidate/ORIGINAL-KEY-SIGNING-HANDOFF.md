# Infinity 2103480 — native-shutdown QA signing handoff

**Engineering status (2026-11-11):** Source-matched native engine and **unsigned original-owner QA APK assembly PASS**. A signed installable QA APK **does not exist yet**. The original accepted 2103480 APK and permanent signing identity are untouched.

## Exact authenticated inputs

- Original, already-signed 2103480 Android APK SHA-256: `9cbb4c5f89a214924b6890463aa5842f85b18ff445d04d855e441fa61f4578c2`. GitHub Actions artifact **13771187253**, run **42830516841**.
- Complete ARM64 native engine SHA-256: `503f91109332ef050a604cf15ad604b16e156b55459bafd47c453c3f72de0437`. Passed run **42959455792**, artifact **13830588821**, source commit `5e26af40222bc521638bd184a2bfb0d5dce337f1`.
- Original signed80 component bundles: run **42829229209**, artifact **13770936077**.
- New **unsigned/not installable** original-owner preparation: **PASS** run **42970204230**, artifact **13833695178**; archive digest `sha256:3f5221e00605d7c05bc371dafdae8c2fb14a8058caed798a5a1ec7e3df4eb9b9`.
- QA versionCode **2103482 is provisional, not reserved**. Recheck live release authority and highest issued version before preparing or signing.

## Exact candidate boundary

Approved, recorded unsigned APK changed-member set has exactly:
1. `lib/arm64-v8a/libkodi.so` — only the previously reviewed Essential-First native receipt-order correction.
2. `AndroidManifest.xml` — typed versionCode only.
3. `assets/experience-component-updates.properties` — Infinity's last-updated version label only; Cobra last-updated remains 2103445.

All five DEX files, provider/runtime files, service/Command Center payload, remaining libraries, layouts, resources, and Cobra remain byte-identical to signed80. The original CO​BRA and MINIMAL_ANDROID_CONTRACT component archives were copied and independently hash-checked; no alternative build or installer identity was introduced.

The original native fail-closed gate remains unchanged. In particular **unknown/opaque Python/native writer effects still veto unsafe termination**. The external AdultHideout Core compatibility prototype is **not packaged or installed** by this QA candidate; its runtime image identity/stop-drain behavior has not been proven.

## Next controlled release action

Proceed **only through** the repository's existing original-key combined signer workflow `infinity-combined-release.yml` (sole original-key workflow ID `397702717`). Before exposing keys, reconcile candidate version and actual current canonical generation, register the complete exact prepared owner catalog with source/hash evidence, run the original pre-sign release-ownership/member/DEX/package/signature and original-key policy checks, and refuse a mismatch. The existing signer implementation and original certificate must remain unchanged. Do not create a replacement key, bypass original `release_gate.py`, manufacture a PASS, or auto-lock/promote the candidate.

Then verify the actual permanently signed APK (v1/v2/v3), install-over compatibility with the protected baseline, matching component bundles, complete member diff, original certificate, and recovery coverage. Only a **signed QA candidate** may be offered for the owner's Fold testing. Actual Android Close/process-death/data-preserving reopen (positive and genuine opaque negative) is **NOT RUN** and must remain explicitly pending; an ARM64 build or unsigned package does not certify this.

**Never replace the accepted 2103480 baseline or treat this as final user acceptance.**


## Live signer-authority check — 2026-11-11 01:16 America/Detroit (blocker, not a release)

Authenticated GitHub Actions state:
- Latest original-source native run **42959455792**: completed SUCCESS, exact native source and ABI PASS.
- Latest shutdown original-owner unsigned QA run **42970204230**: completed SUCCESS, artifact **13833695178**, no post-success failure or later signed run in repository's recent Actions run listing. This is **not an installer**.
- Original-only signer policy `repairs/dual-experience-isolation-2103420/signer-policy.json` identifies sole original-key workflow **397702717**; retired original-key workflows are not an alternative.
- Existing original signer `.github/workflows/infinity-combined-release.yml` at this isolated branch contains **no 2103482 route**. Its `sign-performance` job is restricted to dispatch on `work/infinity-2103460-nine-corrections-20261106` and validates only versionCode **2103480 or 2103481**, bound to generations **63 or 64**. It requires an exactly matching registered `release-authority.json` candidate generation and expected complete source-file hash vector **before key access**. Changing the operation, selected branch, version, or current authority without explicit registered admission makes the gate reject by design.
- Candidate QA **2103482** is provisional and has **no confirmed exact original-key release-authority registration**, no approved source-bound signer operation, and no verified signed APK. The existing sign-performance job may **not** be reused by relabeling or faking version/generation. The requested signing workflow would require newly authorized, policy-compliant exact SHA/catalog/version registration and an expressly reviewed internal-QA adapter in the **same sole original signer**, not a second key or detached signing workflow. That authority amendment is **not authorized by current existing registration**; stop at this gate rather than weaken it.
- Actual Android Close/process-death/reopen with preserved settings remains **NOT RUN**. Opaque native writer/AdultHideout resource retirement remains **UNPROVEN** and must not be declared safe. The native fail-closed gate remains mandatory.

**Decision:** No further CI retries or key exposure. Leave verified unsigned QA artifact intact. Next human release-authority decision is to approve/record the exact **2103482** candidate generation/source/catalog hash vector and a strictly gated original-key internal-QA signer path (with recovery coverage), or keep blocked. Recheck current canonical generation before that decision; never treat provisional versionCode as reserved. The protected 2103480 original signed baseline and Cobra remain unchanged.
