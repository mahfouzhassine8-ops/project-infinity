# Controlled UI candidate and forward recovery packaging

User authorization: build, verify and sign 2103454 and 2103455 only; no installation, acceptance, promotion or lock. Base is exact signed 2103453. Source overlay is fixed at 1cc7684bd05581c21f31682cdb0f2d4e156a585e; readiness at fd8a7dbace118a908508f324a5a8ba0a70d765aa.

Selected checks recorded before execution:

- Original signed base, source preimages, exact 19-member candidate allowlist and 7,602 protected members; reject unexpected DEX/native/resource/source changes.
- Candidate and recovery metadata semantics, original-key module authentication and skin protected inventories; invalid source/hash/signature/version must fail.
- Recovery from candidate: strictly higher APK/module/skin versions, exact baseline functional code, unchanged authenticated installer; stale helper import rejected and restored normal entry points cannot reach candidate-only code. Preserve unknown local changes and persistence barriers.
- Existing original owner/authority lineage, immutable source/artifact binding, version availability, pre-key and post-sign checks. Focused packaging tests only; do not repeat completed application tests or run shutdown suites.
- Inspect available supported isolated Android target; if unavailable, record install-over/recovery as pending. No primary-device installation is authorized.

Only this packaging directory, the sole trusted workflow, its exact authority branch selector and release-authority records may change. Original signer, ownership engine, accepted registry, security policies and all application code remain frozen. New module signatures are generated only inside the existing original-key workflow after all unsigned source and ownership gates pass.

Deliver both APKs with matching component ZIPs and evidence only when both preservation/signature/recovery gates pass. Stop on unexplained failed gates. Scudo remains unresolved.
