# Actual third-party Core source attribution — next shutdown fix target

Owner authorized correction for Essential-First from signed **2103480**. Evidence at 54e6134f; coordinator receipt-order candidate f00ab026 remains preserved, host-only verified.

## New public-source finding (2026-11-10)

Published upstream project: `Vashiel/repository.adulthideout`, service `service.adulthideout.core/service.py`, current master Git blob **eb680f261bd5aa9b683263f2d835ead317800a1e**:
https://github.com/Vashiel/repository.adulthideout/blob/master/service.adulthideout.core/service.py

- November 3, 2026 AdultHideout 1.0.26 introduced an **in-process Android native Rust Core**. The service's own `addon.xml` advertises 1.0.1; the main plugin is now 1.0.27 as of November 9. The owner's diagnostic identifies the same service ID, but **the installed service.py SHA/version and actual downloaded .so SHA remain unverified**. Do not equate publisher code or manifest with installed user bytes.
- `service.py::start_engine`, around lines 410–490, on Android walks app-private `code_cache`, `cache`, `files` and `special://temp` paths to copy `libadulthideout_core.so` into the Kodi process's native loader-accessible directory. It calls **`shutil.copy2(lib_path, candidate)`**, then **`os.chmod(candidate, 0o755)`**, then **`ctypes.CDLL(actual_lib_path)`**, then `start_core_service(8191)`.
- `shutil.copy2` intentionally copies mode/timestamps/extended attributes through Python `copystat`; these align with reported `os.utime`, `os.chmod` and `os.setxattr` audit categories. The explicit chmod and ctypes.CDLL match the remaining two categories. A second download path calls `os.chmod` after staging a SHA-checked binary.
- `service.py::run_kodi_service`, around lines 536–662, initializes or downloads the native image, runs watchdog health/restart every 1–10 seconds, and at normal monitor exit calls `stop_core_service()`. This is service intention, **not proof** Rust tasks have joined or protected resources are durable at the time Kodi's Python interpreter retires.
- Public source directly explains *how* the four types of audit events can arise, without indicating that they mutated essential data. The new native service release postdates the historical signed 2103419/2103420 successful Android Close runs, giving an evidence-supported **new environment hypothesis**, not proof of the owner's installed update version.

## Why the existing shutdown gate rejects this

Signed-419-era source already had `InfinityPythonPersistence.h::Audit` marking `os.chmod/os.utime/os.setxattr` as `unclassified_native_persistence_operation` and `ctypes.dlopen` as an unknown external/opaque writer unless it satisfies `ApprovedNativeLookup`. The existing ledger's `Retired()` intentionally keeps hard blockers after an interpreter stops. Signed80 changed optional Python ownership but retained the final fail-closed protected-resource seal.

The comparison demonstrates **no newly introduced broad audit rule**. Older green Android Close cases did not establish coverage of this newly released Rust Core. Thus don't claim a shutdown-code regression, an essential data leak, or a dangerous successful operation without matching installed evidence.

## Engineering correction, scope-limited

1. **Reduce unnecessary metadata operations at their origin where authorized**: upstream `shutil.copy2` copies file metadata that is not inherently required to load a `.so`. An upstream-friendly source correction could use a bounded content-only copy into exact app-private destination with file-identity/symlink checks, verify bytes against the pinned SHA manifest, set only necessary load permissions and require atomic replacement. This alone is **insufficient to authorize Close**, since `ctypes.CDLL` starts native Rust tasks in the Kodi process. Provider-source edits require explicit owner scope and are update-sensitive; do not slip them into protected Infinity APK.
2. **Establish the native-engine lifecycle**. For a published and matched local binary, verify its exact SHA/manifest and actual `stop_core_service` return/resource-retirement semantics, including worker/network shutdown, pending native file writes and aliases. If this cannot be proven, keep the opaque blocker; unlike a pure Python service, in-process Rust can outlive interpreter shutdown.
3. **Then implement update-resistant Infinity policy**, not a blanket service exemption: only operations with verified target/path, mutation duration/outcome and protected-data isolation can retire without failing the final gate. Generic `ctypes`, metadata operations, arbitrary `addon_data` or temporary symlinks remain guarded. New/unverified provider versions fail closed and report the exact unsupported lifecycle without consuming authorization.
4. Preserve proven `f00ab026` independent save receipts; do not rewrite successful essential saves or change the 25s deadline.
5. Selected host negative cases: an unknown native library that may write protected data MUST still veto Close; positive: known private file-copy/lifecycle with verifiable retirement MUST not prevent successful durable Essential-First. Android real process-death/data-preserving reopening and original signer only after a meaningful candidate is ready. Cobra and native shared behavior unchanged unless exact Infinity-only isolation proven; no import of networking78/79; startup changes remain separate.

### Key blocker remaining

The old private diagnostic has audit event names/counts but no operation targets, return values, installed addon source fingerprint, actual loaded library digest or native task retirement proof. Public upstream source is now an **excellent targeted lead**, not an installed proof. Do not claim full shutdown fixed from a source match alone, and do not publish private diagnostic contents.

### Immediate next engineering action

Use the exact publisher source and the already-verified 2103480 native source binding to prototype a **scoped native-engine lifetime contract** that:
- discriminates metadata actions in verified app-private staging from writes to user-protected paths;
- requires *actual* native engine stop/drain before claiming optional retirement;
- denies Close when a new unknown image/target remains;
- remains separate from Cobra and all other add-on behavior.
Determine whether this requires a small upstream service cooperation or an isolated runtime boundary; explain any unavoidable provider modification/update risk before deployment. This is a fix design, not a request for broad additional logs.

No phone test/export, app modification, new APK, signed release, or provider patch is performed by this attribution record.

## Independent local Python audit reproduction (host only)

I executed a disposable Python `shutil.copy2` test with a source file carrying an extended attribute. Registered a process-local read-only `sys.addaudithook` observer that counted only operation names, then copied the file into a temporary target. The resulting exact CPython audit categories were **one `os.utime`, one `os.listxattr`, one `os.setxattr`, and one `os.chmod`**. Without an extended attribute, `os.utime` and `os.chmod` still occurred, but `os.setxattr` did not. This demonstrates the mechanism from upstream `shutil.copy2` independently, without executing or contacting the third-party Kodi add-on. It is **not** the actual Fold trace, and the 170/340 event counts were not reproduced.

## Precise audit-count fingerprint and host reproduction

The private checkpoint counted the four named event categories **170 `os.utime`, 170 `os.setxattr`, 340 `os.chmod`, and 170 `ctypes.dlopen`**. The published Android `start_engine()` code executes exactly **one `shutil.copy2` + one additional explicit `os.chmod` + one `ctypes.CDLL` per attempted load**. On a disposable host Python 3 test with the source fixture carrying an xattr, `copy2(source, target); os.chmod(target,0o755); ctypes.CDLL(None)` generated **one utime, one setxattr, two chmod, and one dlopen** audit event. `ctypes.CDLL(None)` was used only to trigger the audit event without loading any untrusted image. This precisely reproduces the 1:1:2:1 *category ratio*, not the device's 170 repetitions or exact installed code identity.

A plausible, highly specific cause is **repeated attempts to copy/start the core native library** across the source service's health/restart loop (its 1/10-second polling handles missing/unhealthy engine and may repeat `start_engine`). The device may have tried ~170 loads; no exact attempt count, linker exception or successful Rust runtime state is proved by category counts alone. Investigate this exact loop and whether its `ctypes.CDLL` failed before native code executed; an audit event fires before the operation and cannot certify success. An automatic retry loop must not be treated as 170 proven protected file writes. Do **not** simply erase the sticky blocker or treat an `opaque` DLL as safe without actual lifecycle proof.
