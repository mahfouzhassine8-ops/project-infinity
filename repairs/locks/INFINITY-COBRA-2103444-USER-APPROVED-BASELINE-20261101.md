**2103444 is the user-approved combined Infinity/Cobra baseline.**

On 2026-11-01 the user instructed: “Lock it”, referring to the delivered original-key signed 2103444 APK. This records explicit acceptance and supersedes its earlier candidate-only status. No individual physical-device test results were supplied or inferred.

- Baseline reference: `lock/infinity-cobra-2103444-user-approved-20261101`
- Exact signed source: `1b7a4ef16524854fab77a1c974538aee8a1132bb`
- APK: `Infinity-2103444-Combined-Original-Signer.apk`
- APK SHA-256: `38dff935ffc0967e2c16e8d61e6e4bfd693fcb73bbaa130e8fa354e468b85a76`
- Original certificate SHA-256: `d7adeb68e9341596a02bd3262b737a0f45fc6e771ed7e60285437e833b58c6d7`
- [Successful signing run 41284148114](https://github.com/mahfouzhassine8-ops/project-infinity/actions/runs/41284148114)
- [Exact signed APK artifact](https://github.com/mahfouzhassine8-ops/project-infinity/actions/runs/41284148114/artifacts/13074830138)
- [Exact matching component ZIPs](https://github.com/mahfouzhassine8-ops/project-infinity/actions/runs/41284148114/artifacts/13074134837)
- [Component checksums and delivery evidence](../cobra-2103442-end-to-end-quality-refresh/delivery444/SHA256SUMS)
- [Machine-readable acceptance record](INFINITY-COBRA-2103444-USER-APPROVED-BASELINE-20261101.json)

The lock reference resolves to the exact source used by the successful signer, rather than the later documentation commit. The APK, component ZIPs, original signing identity, source and test evidence are unchanged. Infinity retains the exact accepted 2103437 component; shared/native functionality, chooser behavior, icons and shutdown remain unchanged. No application changes, builds, signing operations, installations, data operations or application/shutdown tests accompany this lock.

Signed 2103442 remains the previous recovery baseline at `lock/infinity-cobra-2103442-user-approved-20261101`, source `2e88f85250ef2e46952192cf0fdb42ac5af7c9c8`. Its lock, artifacts and all older recovery references are retained. Future user-authorized work must preserve and compare against this exact 2103444 component vector. Never move or overwrite either accepted reference.

The [original delivery evidence](https://github.com/mahfouzhassine8-ops/project-infinity/blob/9b8536e344bf3d92c5210bac15824c294f1e6471/repairs/cobra-2103442-end-to-end-quality-refresh/DELIVERY.md) remains authoritative for what was measured. In particular, source/host/package/signature checks and actual Android install-over passed; the complete candidate Android interaction matrix remained blocked by the observer readiness deadline in run 41286787645. User acceptance does not change that result into PASS or turn host measurements into physical Fold measurements. Historical signing-authority and test receipts remain unmodified.

GitHub confirms the new lock reference exists at the exact signed source, but reports `protected: false`. Server-enforced immutability is **not enabled**. The existing integration lacks permission to create the required ruleset (the earlier attempt returned HTTP 403, `Resource not accessible by integration`); that denied operation was not retried or bypassed. A repository administrator must use **Settings → Rules → Rulesets**, targeting only `refs/heads/lock/infinity-cobra-2103444-user-approved-20261101`, and enable **Restrict updates** and **Restrict deletions**. Other repository rules and recovery references are untouched.

The signed artifact and component links were available when recorded. GitHub Actions reports their existing retention deadline as **2027-01-30 07:16:50 UTC**; the Git reference and this acceptance record do not extend artifact storage retention.
