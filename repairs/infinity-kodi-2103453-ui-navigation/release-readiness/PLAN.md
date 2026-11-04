# Controlled Android/Fold release readiness — planning only

User-authorized continuation of exact source checkpoint
`1cc7684bd05581c21f31682cdb0f2d4e156a585e`, using signed combined 2103453 as the
proposed base. No application/source repair or behavioral test is selected.

Selected read-only readiness checks, recorded before execution:

- Verify available signed 2103453 bytes, APK identity, original certificate and
  protected engine; compare the checkpoint's source overlay to its exact member
  preimages and enumerate every proposed payload change.
- Inspect existing runtime authentication manifests and original signing/owner
  gates for required packaging metadata. Do not change or bypass those gates.
- Read current GitHub version registry, releases/tags and signing workflow/artifact
  inventory to identify the next unused candidate version and a higher recovery
  version. Do not reserve versions or dispatch workflows.
- Assess a forward recovery that reinstates exact 2103453 functional payload at
  a higher versionCode, preserving package/certificate/user data. An older APK
  or an unsigned rehearsal is not a ready install-over recovery artifact.
- Prepare an explicit acceptance procedure for this UI/navigation/library scope.
  Reuse completed host/Linux evidence; no new application, shutdown or Android
  test is run under release-readiness planning.

No APK/component build, signing, installation, release, promotion or lock.
Packaging and recovery authorization remains a separate user decision after the
concrete plan and blockers are reported. All existing checkpoints and locks stay
unchanged. Only readiness documentation/evidence may be added to this branch.
