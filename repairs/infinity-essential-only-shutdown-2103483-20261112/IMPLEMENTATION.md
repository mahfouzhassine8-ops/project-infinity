# Essential-only shutdown correction over protected 2103483

The existing coordinator already classified third-party Python services as optional. The failure was in its native persistence evidence: pre-operation metadata audits and rejected native-library loads could permanently poison the protected-writer ledger without establishing a completed operation or an active native writer. An optional service's historical warning then vetoed final admission.

The correction changes three native Python persistence headers. It does not change the coordinator's essential-owner list or waive its admission, quiescence, seal, durability, or authorization checks.

- `InfinityPythonWriteHooks.h`: extend the existing native operation leases to metadata primitives (`chmod`, `chown`, `utime`, `setxattr`, `removexattr`). Keep the lease from the actual primitive's entry through its return/error, including cached function references. Use converted actual audit targets.
- `InfinityPythonPersistence.h`: correlate metadata audits to the exact operation, writer, and thread; record actual native-loader outcomes through the captured original loader. A known pre-image Android namespace rejection is a failed load, not evidence of an active native engine. Retain strict treatment of uncertain targets, nested/custom conversion, ambiguous audits, loaded unknown native images, and active protected writes. Preserve read-only identity lookup of the already-running engine.
- `InfinityPythonPersistenceSource.h`: bind that original native loader through the existing observer. Leave all service source and library-path decisions unchanged.

Optional services cannot admit new writes through a closed protected-storage fence. Unfinished actual protected operations and successfully loaded unverified native workers remain safety blockers. No library-name exemption, Core allowlist, service disable, forced process kill, or Core path activation was added.

## Frozen engineering evidence

Native source: `9ce852ebb044a82853ef93af24e34a07ed96daff`.
Actual Android ARM64 engine SHA-256: `b75747363c83a548d61463c2fd434be909f27c07d4872fa9d9c61642a3757635`.

Run `43186634362`: full ARM64 compilation/link and baseline ABI verification passed. All 71,213 baseline global exports and 11 native dependencies were preserved. The source comparison preserved 9,409 native files and changed only the three headers above. Focused real-CPython host cases passed, including baseline negative control, active-operation races, cached calls, unknown writes, loaded native images, custom-argument/audit spoofing, and engine identity lookup after sealing.

Run `43196958708`: actual unchanged Core source and library were installed; its original namespace load rejection occurred. Normal Android Close completed in 2,722 ms with all 16 essential owners durable, zero protected-write blockers, two optional writers unfinished, and no remaining app-UID processes. The workflow failed afterward on an outdated test-only single-UUID Java seal assertion. The authentic receipt passes the protected baseline's actual three-owner seal format; the raw workflow failure remains recorded. Relaunch was not executed in that attempt.

The isolated `talloc_lib_init+32` startup SIGSEGV in run `43195343018` also occurred with unchanged 2103483 in control `43166899782`. Its underlying cause is not established. This inherited emulator/native-bridge limitation is not marked passed or patched here.

Run `43193780823`: exact-2103483 unsigned packaging passed. Apart from the native engine and the two required version metadata members, 7,766 APK payload members are byte-identical. Cobra, Java/DEX, add-ons, authenticated module manifests, skin, settings defaults, and Core source/path are unchanged. No user profile or database is included in the replacement payload.

Android continuation, original signing, signed install-over/forward recovery, and physical Fold acceptance have separate results. This document does not claim their completion.
