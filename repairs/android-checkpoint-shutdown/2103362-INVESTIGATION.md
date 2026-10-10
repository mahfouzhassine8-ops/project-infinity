# Infinity 2103362 shutdown repair candidate

Status: targeted checks passed; candidate build pending. Physical Fold acceptance has not been established. Do not promote this candidate to an accepted baseline solely because CI passes.

## Exact evidence and preservation baseline

- Repository: `mahfouzhassine8-ops/project-infinity`.
- Parent commit: `759813fae0ac9528e021a2e16708db02f124db85`.
- Installed APK: `1.0.9-Runtime-Probe-Retirement-RC1`, version code 2103361. Successful baseline run: https://github.com/mahfouzhassine8-ops/project-infinity/actions/runs/38077503263 .
- Baseline APK SHA256: `70440287e3ac908b1518611992362c2de666a0e6e58cc27083812ba6943fd4c3`.
- Diagnostic: `Infinity-Diagnostics-20261010-162248.zip`, SHA256 `29cbee3023e6faed8a42858b3c9ff556db10d54449b2007d2a4c7e4dcc184c53`.
- Device evidence: Samsung SM-F976U1, Android 17/API 37; Command Center 0.3.5.20, Compatibility 0.8.2.
- Latest checkpoint: CHECKPOINT_FAILED, 9420 ms, checkpoint_saved=false, no termination authorization. First error: `python_services: python_writer:unobserved_diagnostic_child_output`.
- Full supplied inventory: 27 blocking Python observations, 16 advisory observation rows, two unknown native job contracts, 17 checkpoint owners. An observation row can represent multiple occurrences.

## Root causes and minimal repairs

Runtime source files below are under `repairs/android-checkpoint-shutdown/runtime/native/overlay/xbmc/`; Python source is `repairs/android-checkpoint-shutdown/writers/observer.py`.

| Source/function | Root cause | Repair and remaining guarantee |
|---|---|---|
| observer.py: Observer.install_children; interfaces/python/InfinityPythonPersistence.h: Touch | An already permitted read-only child rejects subprocess.DEVNULL as unobserved output. The native filesystem ledger also attempts to fsync the null character device as a durable regular file. The DEVNULL case was reproduced against the baseline. The supplied child-output row has no output-type detail, so its exact stream configuration cannot be reconstructed. | Accept the standard DEVNULL sentinel inside the existing read-only command/environment contract. Exclude null-device contents only when the actual descriptor matches /dev/null's character-device type, inode, device and rdev. Unknown output objects, unknown commands and real files remain checked. Record rejected stream/type details. |
| interfaces/python/InfinityPythonPersistence.h: Audit; new InfinityPythonCryptoContract.h: ApprovedCryptoImage/ApprovedNativeLookup; Observer.install_crypto_loads | All ctypes loading and symbol lookups were treated as opaque writers, including the Crew's bundled cryptographic arithmetic and CPU probes. dlopen(NULL) loads no new library. | Restrict approval to the 18 observed signed-APK crypto images, canonical APK library root, exact SHA256 and exact exported symbols. Verify dlsym's actual mapped image using dladdr. Unknown images, tampered bytes, symlinks, other symbols and ctypes call_function remain blocked. Basename resolution is limited to those 18 names and is independently verified natively. |
| platform/android/activity/InfinityScriptPersistence.h: Touch/CommitWorker | The absent chooser weather snapshot staging leaf was treated as a missing durable user file. The producer's .pending content is a disposable copy of existing Weather labels; it is not user settings or Resume Hub state. The export proves absence/type failure, not exactly where its producer was interrupted. A generic atomic-replace test alone does not reproduce that provenance. | Only the exact weather producer and exact app-private snapshot.json.pending leaf receive an absence-optional contract. A present staging file is still synced. The parent namespace must still sync. Other writers, final snapshot, settings, symlinks, missing parents and genuine missing required files remain blocked. Missing optional SQLite companions now also require parent namespace persistence. |
| addons/AddonManager.cpp: CAddonMgr::UpdateLastUsed | An unnamed lambda actually writes the add-ons database but has no owner receipt; SetLastUsed's boolean result was ignored. Its completed record remained unknown. | Name the job native_databases/addon-last-used. A failed SQL result throws and does not update in-memory Last Used metadata or publish a success event. Require completion after worker/callback/destructor lifecycle; the database barrier separately verifies durability. |
| TextureCacheJob.cpp/h: CTextureCacheJob::GetCheckpointResponsibility/CheckpointSucceeded; TextureCache.cpp: CTextureCache::OnCachingComplete | The cache job has no reviewed contract although its completion callback writes texture metadata. Worker completion alone cannot prove that callback's SQL succeeded. Callback ignored the database wrapper's boolean result. | Require the exact CTextureCacheJob with exact CTextureCache callback, mapped to native_databases/texture-cache-metadata. The callback supplies the verified DB result. Failed image retrieval performs no authoritative metadata write; regenerable cache pixels do not substitute for DB persistence. Unexpected callback/derived types remain unknown. |
| utils/Job.h/JobManager.h/JobManager.cpp/JobCheckpoint.h: receipt admission, OnJobComplete, Complete/GetSnapshot | Completion and callback errors need a process-lifetime obligation even when they happen before Close. Deleting or canceling a newly classified job must not retire it without a receipt. | Retain admitted receipt obligations until verified completion. Keep semantic worker/callback failures and canceled/deleted jobs without a receipt as blockers. Bound receipt inventory and fail closed on overflow. Existing unknown jobs remain protected. |
| platform/android/activity/InfinityAndroidCheckpoint.cpp: RequiredJobsDrained | An already stopped unknown job triggers fatal failure before remaining owners can be checked, hiding independent blockers and leaving settings/profile/database owners pending. | Continue independent owner saving only after all visible required jobs are actually settled. Running jobs, truncated inventories and outstanding callbacks still prevent progression. Unknown/failed/missing receipts remain failed owners, so final SAFE_TO_TERMINATE remains impossible. This gathers the rest of the blockers without overriding authorization. |
| Health Center 2.5.17 default.py: _runtime_findings, _latest_marker_state, _scan_collect, _publish_dashboard_state | Dashboard consumes saved issue keys rather than a fresh verification. Current-log failures can remain active after recovery. An auth success from a different add-on can clear another add-on's error. | Separate companion update 2.5.18: fresh read-only dashboard; matching add-on recovery markers; recurrence reactivates the condition; unscoped failures stay unresolved; positively recovered log rows move to resolved evidence instead of disappearing. A COMPLETE checkpoint is resolved only after validating all 17 owner receipts, proof/identity/generation, consumed authorization and process-death evidence. Failed/incomplete/malformed receipts stay active or unverified. Original historical logs remain retained. |

Crypto evidence: `CRYPTO-2103362-AUDIT.json` records exact binaries, hashes, exports and imports. Reviewed PyCryptodome 3.12.0 source: https://github.com/Legrandin/pycryptodome/tree/d8edf1a6a70d3a65dcda18ee24d96161525f2825 . Reviewed images expose memory/arithmetic/CPU feature operations and no filesystem-writing imports; their library initialization is inert. Their normal PyCryptodome call paths operate on memory. This is a specific reviewed contract, not a general permission for ctypes or arbitrary native execution. ARM64 execution and symbol-image resolution still need device validation.

The exact Health Center 2.5.17 ZIP was recovered and pinned for the separate 2.5.18 code-only build. Its installed version is not established by the Android export. The companion is not silently bundled into or used to overwrite the Fold's dynamically installed Health Center. Its builder verifies the exact source ZIP/default.py preimage and changes only default.py, addon.xml version and the new lifecycle helper; every other package file is retained byte-for-byte. Use it as a reviewed add-on update after checking the installed version; do not overwrite an unreviewed newer/custom Health Center.

## Complete Python blocker and advisory inventory

The following reproduces every supplied observation row. Counts are occurrences, not additional distinct contracts.

| Writer / invoker | Reason | Count | Blocking in 2103361 | Detail | Disposition |
|---|---|---:|---|---|---|
| script.cu.lrclyrics:default.py / 20 | uncaught_script_failure_before_persistence_receipt | 1 | no | (not captured) | Retained advisory; no supplied pending transaction/handle proof. Failed application operation is not proven repaired. |
| plugin.video.tmdbmovies:service.py / 12 | sqlite_write_failed | 26 | no | (not captured) | Retained advisory; no supplied pending transaction/handle proof. Failed application operation is not proven repaired. |
| slyguy.pluto.tv.provider:default.py / 71 | unraisable_python_cleanup_or_write_failure | 2 | no | (not captured) | Retained advisory; no supplied pending transaction/handle proof. Failed application operation is not proven repaired. |
| slyguy.pluto.tv.provider:default.py / 75 | unraisable_python_cleanup_or_write_failure | 2 | no | (not captured) | Retained advisory; no supplied pending transaction/handle proof. Failed application operation is not proven repaired. |
| slyguy.pluto.tv.provider:default.py / 81 | unraisable_python_cleanup_or_write_failure | 2 | no | (not captured) | Retained advisory; no supplied pending transaction/handle proof. Failed application operation is not proven repaired. |
| slyguy.pluto.tv.provider:default.py / 86 | unraisable_python_cleanup_or_write_failure | 2 | no | (not captured) | Retained advisory; no supplied pending transaction/handle proof. Failed application operation is not proven repaired. |
| slyguy.pluto.tv.provider:default.py / 96 | unraisable_python_cleanup_or_write_failure | 2 | no | (not captured) | Retained advisory; no supplied pending transaction/handle proof. Failed application operation is not proven repaired. |
| plugin.video.thecrew:service.py / 8 | unobserved_diagnostic_child_output | 1 | yes | (not captured) | DEVNULL false positive reproduced; exact supplied stream detail unavailable. Other unobserved outputs stay blocked. |
| plugin.video.thecrew:service.py / 8 | sqlite_write_failed | 2 | no | (not captured) | Retained advisory; no supplied pending transaction/handle proof. Failed application operation is not proven repaired. |
| plugin.video.thecrew:service.py / 8 | external_or_opaque_writer_requires_explicit_participant | 1 | yes | event=ctypes.dlopen | Reviewed memory-only load: NULL process image or exact pinned crypto image; all other loads stay blocked. |
| plugin.video.thecrew:service.py / 8 | external_or_opaque_writer_requires_explicit_participant | 1 | yes | event=ctypes.dlopen;target=libCryptodome_Cipher__raw_ecb.so | Reviewed memory-only load: NULL process image or exact pinned crypto image; all other loads stay blocked. |
| plugin.video.thecrew:service.py / 8 | external_or_opaque_writer_requires_explicit_participant | 1 | yes | event=ctypes.dlopen;target=libCryptodome_Cipher__raw_cbc.so | Reviewed memory-only load: NULL process image or exact pinned crypto image; all other loads stay blocked. |
| plugin.video.thecrew:service.py / 8 | external_or_opaque_writer_requires_explicit_participant | 1 | yes | event=ctypes.dlopen;target=libCryptodome_Cipher__raw_cfb.so | Reviewed memory-only load: NULL process image or exact pinned crypto image; all other loads stay blocked. |
| plugin.video.thecrew:service.py / 8 | external_or_opaque_writer_requires_explicit_participant | 1 | yes | event=ctypes.dlopen;target=libCryptodome_Cipher__raw_ofb.so | Reviewed memory-only load: NULL process image or exact pinned crypto image; all other loads stay blocked. |
| plugin.video.thecrew:service.py / 8 | external_or_opaque_writer_requires_explicit_participant | 1 | yes | event=ctypes.dlopen;target=libCryptodome_Cipher__raw_ctr.so | Reviewed memory-only load: NULL process image or exact pinned crypto image; all other loads stay blocked. |
| plugin.video.thecrew:service.py / 8 | external_or_opaque_writer_requires_explicit_participant | 1 | yes | event=ctypes.dlopen;target=libCryptodome_Util__strxor.so | Reviewed memory-only load: NULL process image or exact pinned crypto image; all other loads stay blocked. |
| plugin.video.thecrew:service.py / 8 | external_or_opaque_writer_requires_explicit_participant | 1 | yes | event=ctypes.dlopen;target=libCryptodome_Hash__BLAKE2s.so | Reviewed memory-only load: NULL process image or exact pinned crypto image; all other loads stay blocked. |
| plugin.video.thecrew:service.py / 8 | external_or_opaque_writer_requires_explicit_participant | 1 | yes | event=ctypes.dlopen;target=libCryptodome_Hash__SHA1.so | Reviewed memory-only load: NULL process image or exact pinned crypto image; all other loads stay blocked. |
| plugin.video.thecrew:service.py / 8 | external_or_opaque_writer_requires_explicit_participant | 1 | yes | event=ctypes.dlopen;target=libCryptodome_Hash__SHA256.so | Reviewed memory-only load: NULL process image or exact pinned crypto image; all other loads stay blocked. |
| plugin.video.thecrew:service.py / 8 | external_or_opaque_writer_requires_explicit_participant | 1 | yes | event=ctypes.dlopen;target=libCryptodome_Hash__MD5.so | Reviewed memory-only load: NULL process image or exact pinned crypto image; all other loads stay blocked. |
| plugin.video.thecrew:service.py / 8 | external_or_opaque_writer_requires_explicit_participant | 1 | yes | event=ctypes.dlopen;target=libCryptodome_Cipher__Salsa20.so | Reviewed memory-only load: NULL process image or exact pinned crypto image; all other loads stay blocked. |
| plugin.video.thecrew:service.py / 8 | external_or_opaque_writer_requires_explicit_participant | 1 | yes | event=ctypes.dlopen;target=libCryptodome_Protocol__scrypt.so | Reviewed memory-only load: NULL process image or exact pinned crypto image; all other loads stay blocked. |
| plugin.video.thecrew:service.py / 8 | external_or_opaque_writer_requires_explicit_participant | 1 | yes | event=ctypes.dlopen;target=libCryptodome_Util__cpuid_c.so | Reviewed memory-only load: NULL process image or exact pinned crypto image; all other loads stay blocked. |
| plugin.video.thecrew:service.py / 8 | external_or_opaque_writer_requires_explicit_participant | 1 | yes | event=ctypes.dlopen;target=libCryptodome_Hash__ghash_portable.so | Reviewed memory-only load: NULL process image or exact pinned crypto image; all other loads stay blocked. |
| plugin.video.thecrew:service.py / 8 | external_or_opaque_writer_requires_explicit_participant | 1 | yes | event=ctypes.dlsym;symbol=ghash_portable | Reviewed crypto symbol; require exact export and actual mapped-image hash. |
| plugin.video.thecrew:service.py / 8 | external_or_opaque_writer_requires_explicit_participant | 1 | yes | event=ctypes.dlsym;symbol=ghash_expand_portable | Reviewed crypto symbol; require exact export and actual mapped-image hash. |
| plugin.video.thecrew:service.py / 8 | external_or_opaque_writer_requires_explicit_participant | 1 | yes | event=ctypes.dlsym;symbol=ghash_destroy_portable | Reviewed crypto symbol; require exact export and actual mapped-image hash. |
| plugin.video.thecrew:service.py / 8 | external_or_opaque_writer_requires_explicit_participant | 1 | yes | event=ctypes.dlsym;symbol=have_clmul | Reviewed crypto symbol; require exact export and actual mapped-image hash. |
| plugin.video.thecrew:service.py / 8 | external_or_opaque_writer_requires_explicit_participant | 1 | yes | event=ctypes.dlopen;target=libCryptodome_Cipher__raw_ocb.so | Reviewed memory-only load: NULL process image or exact pinned crypto image; all other loads stay blocked. |
| plugin.video.thecrew:service.py / 8 | external_or_opaque_writer_requires_explicit_participant | 1 | yes | event=ctypes.dlopen;target=libCryptodome_Cipher__raw_aes.so | Reviewed memory-only load: NULL process image or exact pinned crypto image; all other loads stay blocked. |
| plugin.video.thecrew:service.py / 8 | external_or_opaque_writer_requires_explicit_participant | 1 | yes | event=ctypes.dlsym;symbol=have_aes_ni | Reviewed crypto symbol; require exact export and actual mapped-image hash. |
| plugin.video.thecrew:service.py / 8 | external_or_opaque_writer_requires_explicit_participant | 1 | yes | event=ctypes.dlopen;target=libCryptodome_Cipher__chacha20.so | Reviewed memory-only load: NULL process image or exact pinned crypto image; all other loads stay blocked. |
| plugin.video.thecrew:service.py / 8 | external_or_opaque_writer_requires_explicit_participant | 1 | yes | event=ctypes.dlopen;target=libCryptodome_Hash__poly1305.so | Reviewed memory-only load: NULL process image or exact pinned crypto image; all other loads stay blocked. |
| slyguy.pluto.tv.provider:default.py / 115 | unraisable_python_cleanup_or_write_failure | 2 | no | (not captured) | Retained advisory; no supplied pending transaction/handle proof. Failed application operation is not proven repaired. |
| slyguy.pluto.tv.provider:default.py / 126 | unraisable_python_cleanup_or_write_failure | 2 | no | (not captured) | Retained advisory; no supplied pending transaction/handle proof. Failed application operation is not proven repaired. |
| slyguy.pluto.tv.provider:default.py / 134 | unraisable_python_cleanup_or_write_failure | 2 | no | (not captured) | Retained advisory; no supplied pending transaction/handle proof. Failed application operation is not proven repaired. |
| slyguy.pluto.tv.provider:default.py / 143 | unraisable_python_cleanup_or_write_failure | 2 | no | (not captured) | Retained advisory; no supplied pending transaction/handle proof. Failed application operation is not proven repaired. |
| slyguy.pluto.tv.provider:default.py / 145 | unraisable_python_cleanup_or_write_failure | 2 | no | (not captured) | Retained advisory; no supplied pending transaction/handle proof. Failed application operation is not proven repaired. |
| slyguy.pluto.tv.provider:default.py / 149 | unraisable_python_cleanup_or_write_failure | 2 | no | (not captured) | Retained advisory; no supplied pending transaction/handle proof. Failed application operation is not proven repaired. |
| script.trakt:default.py / 27 | unraisable_python_cleanup_or_write_failure | 1 | no | (not captured) | Retained advisory; no supplied pending transaction/handle proof. Failed application operation is not proven repaired. |
| script.extendedinfo:service.py / 21 | unraisable_python_cleanup_or_write_failure | 3 | no | (not captured) | Retained advisory; no supplied pending transaction/handle proof. Failed application operation is not proven repaired. |
| python_services / -1 | script_file_identity_or_type_unconfirmed | 1 | yes | path=/data/data/com.projectinfinity.kodi/files/infinity-chooser-weather/snapshot.json.pending | Disposable staging absence, exact producer/path only; present file and parent still sync. |
| python_services / -1 | script_file_identity_or_type_unconfirmed | 1 | yes | path=/dev/null | Null-device durability false positive; descriptor/device identity required. |

SQLite advisories: TMDB Movies has 26 write-failure occurrences and Crew has two. Neither export row contains SQL verb, SQLite code, exception class or statement/transaction identity. Those business operations may have failed; there is insufficient evidence to label them harmless or successfully retried. The export lists no pending Python writers/transactions and no additional failed database-file sync paths, but the overall Python owner did not commit. Existing safeguards continue to reject pending transactions, failed buffered writes, failed filesystem syncs and unobserved native SQLite access. New diagnostics capture exception class, SQLite code and SQL verb, never SQL values/parameters. Closed-handle cleanup improvements are retained. No SQLite exception is globally suppressed or newly whitelisted.

Other advisories (Lyrics, Pluto provider, Trakt, Extended Info) are genuine operation/cleanup diagnostics with no supplied unresolved durable write. Their successful interpreter retirement is not proof that the application operation itself succeeded. Retain them as diagnostics; matching verified recovery is required before Health Center calls their operation resolved.

## Native jobs

| Job | Supplied phase | Actual writes | Candidate disposition |
|---|---|---|---|
| ADDON::CAddonMgr::UpdateLastUsed, job 345 | completed_without_owner_receipt | add-on Last Used SQL update and metadata event | Required native_databases/addon-last-used completion receipt, SQL boolean checked, database seal still required. |
| CTextureCacheJob, job 348 | completed_without_owner_receipt | optional image cache plus authoritative texture DB metadata in completion callback | Required native_databases/texture-cache-metadata receipt from exact callback, checked SQL result, database seal still required. |

Neither job was declared universally nonpersistent. A different unknown job remains a shutdown blocker.

## Every checkpoint owner

| Owner | Supplied result | Supplied error | Candidate verification |
|---|---|---|---|
| native_admission | PENDING | (none) | Successful controlled coordinator case requires this owner finished, clean and durable at the same checkpoint generation. Physical result pending. |
| python_services | FAILED | python_writer:unobserved_diagnostic_child_output | Successful controlled coordinator case requires this owner finished, clean and durable at the same checkpoint generation. Physical result pending. |
| background_jobs | FAILED | unknown_native_job_persistence_contract;10CLambdaJobIZN5ADDON9CAddonMgr14UpdateLastUsedERKNSt6__ndk112basic_stringIcNS2_11char_traitsIcEENS2_9allocatorIcEEEEE3$_6E;16CTextureCacheJob | Successful controlled coordinator case requires this owner finished, clean and durable at the same checkpoint generation. Physical result pending. |
| playback | COMMITTED | (none) | Successful controlled coordinator case requires this owner finished, clean and durable at the same checkpoint generation. Physical result pending. |
| command_center | COMMITTED | (none) | Successful controlled coordinator case requires this owner finished, clean and durable at the same checkpoint generation. Physical result pending. |
| compat | COMMITTED | (none) | Successful controlled coordinator case requires this owner finished, clean and durable at the same checkpoint generation. Physical result pending. |
| kodi_settings | PENDING | (none) | Successful controlled coordinator case requires this owner finished, clean and durable at the same checkpoint generation. Physical result pending. |
| profiles | PENDING | (none) | Successful controlled coordinator case requires this owner finished, clean and durable at the same checkpoint generation. Physical result pending. |
| skin_settings | PENDING | (none) | Successful controlled coordinator case requires this owner finished, clean and durable at the same checkpoint generation. Physical result pending. |
| addon_settings | PENDING | (none) | Successful controlled coordinator case requires this owner finished, clean and durable at the same checkpoint generation. Physical result pending. |
| favourites | PENDING | (none) | Successful controlled coordinator case requires this owner finished, clean and durable at the same checkpoint generation. Physical result pending. |
| peripherals | PENDING | (none) | Successful controlled coordinator case requires this owner finished, clean and durable at the same checkpoint generation. Physical result pending. |
| audio_policy | PENDING | (none) | Successful controlled coordinator case requires this owner finished, clean and durable at the same checkpoint generation. Physical result pending. |
| deferred_dialog_state | PENDING | (none) | Successful controlled coordinator case requires this owner finished, clean and durable at the same checkpoint generation. Physical result pending. |
| xml_files | PENDING | (none) | Successful controlled coordinator case requires this owner finished, clean and durable at the same checkpoint generation. Physical result pending. |
| native_databases | PENDING | (none) | Successful controlled coordinator case requires this owner finished, clean and durable at the same checkpoint generation. Physical result pending. |
| pvr | ALREADY_DURABLE | (none) | Successful controlled coordinator case requires this owner finished, clean and durable at the same checkpoint generation. Physical result pending. |

Pending is not a data-loss verdict. These owners lacked a completed checkpoint proof because the earlier pipeline failed. The repaired coordinator harness exercises all 17 owners and successful authorization, plus unknown-running/unknown-stopped/missing-receipt cases and simultaneous settings/profile/skin failures. Actual pending owners are verified by their existing save paths, XML file/parent syncs, script retirement and native SQLite barrier; there is no new shortcut to ALREADY_DURABLE.

## Shutdown trace and unchanged authority

1. Android Close Infinity goes through InfinityKodiShutdown/InfinityCloseGuardService and the session/PID/owner lease. It starts a checkpoint rather than killing the native process.
2. JNIMainActivity exposes request/status/authorize JNI APIs. InfinityAndroidCheckpoint::Request/Pump closes write admission and retains already accepted work.
3. Playback captures final state before freezing; Command Center and Compatibility commit their resident participant journals. Foreign Python invokers retire with their observers, tracked threads, buffers, child processes and SQLite state checked before native filesystem synchronization.
4. JobManager completes admitted workers and exact callbacks. The job inventory distinguishes outstanding work from stopped-but-unproven contracts. Existing settings, profiles, skin, add-on settings, favorites, peripherals, audio and captured dialog state save through their checked owners.
5. XML/files sync and the real native SQLite registry drains accepted transactions/queues, rejects late writes, seals databases and verifies file durability. Every required owner must be clean and committed/already durable at the same generation.
6. SAFE_TO_TERMINATE is published only after the strict registry checks. Android durably records it, binds its SHA256 proof to the session/PID/owner, and consumes the one-shot authorization before requesting ordinary engine termination.
7. The guard waits for actual process-death/owner-retirement evidence before COMPLETE and normal reopen. A lifecycle callback, timeout, quiet log or process-state live=false does not prove this sequence. The supplied 2103361 receipt never reached authorization.

Android Close/lease/termination code is unchanged by this candidate. Recents recovery, safe system probes, ctypes evidence refinements, idempotent folder handling and closed-SQLite-handle fixes are preserved. No forced process termination, reset, database deletion, provider removal, profile rewrite, skin redesign or account repair was introduced. Command Center 0.3.5.20/Compatibility 0.8.2 source assets remain unchanged. Resume Hub remains local-first and saving does not depend on Trakt authorization.

## Related warnings and historical ANRs

- Trakt authorization/reauthorization and Meta-account warnings are separate account/service concerns unless their work leaves an actual unresolved persistence obligation. The export's Trakt cleanup row is advisory, not an authorization-specific blocking row. No credentials were changed and no saving dependency on Trakt was introduced.
- DistroTV EPG failure is not identified as a DistroTV-specific blocker anywhere in the supplied checkpoint inventory. No causal shutdown claim or DistroTV change is justified by this export.
- Unresolved account/EPG errors remain visible; the Health Center update cannot manufacture service success. Cross-add-on token refresh cannot clear another add-on's error.
- Two historical ANR traces are retained separately. Their producing APK versions are not established. They are not attributed to 2103361 and are not evidence that 2103362 fixed an ANR.

## Tests and evidence limits

All 20 targeted suite groups passed before triggering candidate CI:

- Foundation: Android transaction authority host checks, native barrier, checked real SQLite regression/original reproduction, critical file IO, 15 Resume participant tests.
- Actual CPython native observer: 28 scenarios, including DEVNULL, atomic replace, detailed SQLite advisory, open/pending transactions, SystemExit handling, child threads, layered buffers, failed writes and existing safe probes.
- Python observer regression suite and complete blocking/advisory filesystem ledger.
- Exact 18 APK crypto hashes with tampering, symlinks, alias paths, unknown exports and invalid handles rejected. Host tests do not execute ARM64 crypto code or prove positive ARM64 dlsym mapping.
- Weather exact producer/path classification and real sync worker: absent disposable stage accepted; present stage synced; missing required file, symlink and missing parent rejected.
- Job metadata/lifetime tests, 200 phase races and 10,000 repeated unknown invocations; complete production JobManager with ten completion/failure/cancellation cases.
- Actual Last Used/Texture completion functions with failed SQL and failed callback results; exact versus unexpected callback types.
- Native coordinator: 33 controlled scenarios, all-owner safe path, stopped/running unknown jobs, missing receipt, owner failures, sealed-write rejection and one-shot authorization.
- Real SQLite runtime: 12 cases including busy commit retaining the transaction, sticky SQL error, queued inserts/deletes, accepted work, unsupported closed backend and final seal.
- Actual add-on settings saves, pending GUI owners, critical file saves, dirty owners and captured deferred dialogs.
- Engine identity and package preservation/signing/source gate tests.
- Patched Health Center collector/dashboard: matching recovery, unrelated success rejected, recurrence active, unscoped uncertainty retained, historical evidence retained, failed/complete/tampered checkpoint receipt and byte preservation of all untouched package files.

Additional checks passed: 14 actual Resume Hub behavioral tests; 500 distinct host-process handoffs using the actual Command Center journal, preserving position 417.125/playcount 4 and rejecting a foreign prior owner; exact baseline APK identity comparator and negative protected-payload drift checks. The 500-cycle harness supplies native startup registration and prior-owner death proof. It does not exercise Android/JNI/Fold lifecycle.

The local source reconstruction is a reviewed subset sufficient for these source/runtime host tests. The original complete native parent manifest is unchanged, and the newly edited AddonManager.cpp/TextureCache.cpp preimages match it exactly. CI still must reconstruct and verify the full 9,374-file native parent, compile the actual ARM64 engine and Android shell, preserve permanent signer identity, and compare the final payload to the exact 2103361 APK. A foundation preimage gate initially rejected using already-patched source; it passed with its required exact parent input. No failing check was disabled.

## Required physical acceptance

After the candidate is built, verify at least three ordinary close/reopen cycles on the SM-F976U1. Include idle add-on services, a changed preference, playback progress and Resume Hub history. Keep providers/installed add-ons intact. For each cycle export the full Python/native inventory and confirm: no genuine blocker, every owner committed or safely durable, matching SAFE authorization consumed, actual native PID death, COMPLETE receipt, and reopen without recovery warnings. Compare saved preferences/profiles/history before and after. Exercise the Crew crypto/diagnostic paths and the weather producer. Deliberate failed writes must still refuse authorization. Check Health Center after a failed operation, matching recovery and recurrence. Test Trakt unconfigured/expired without preventing local Resume Hub persistence. Continue to treat DistroTV/Meta-account operation failures as unresolved until independently verified.

Candidate identity: 2103362, 1.0.9-Shutdown-Contracts-RC1. The accepted baseline remains 2103361. The separate Health Center candidate is 2.5.18. Commit/build information will be added to the delivery report; no device acceptance is implied.
