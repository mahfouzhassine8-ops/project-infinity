# 2103480 private diagnostic evidence review

This continues a11d4872; it does not restart source tracing. GPT-6.1 reviewed the observed writer operations and their provenance. Astra independently correlated the startup and checkpoint sessions. Codex verified the extracted-file hashes and compared the installed inventory with the exact signed 2103480 APK. No production edit or application execution was performed.

## Evidence admitted

All nineteen private readable files were obtained, totaling 3,300,638 bytes. Every transferred file matches its file-reader source-byte SHA-256; all eighteen indexed extracts also match the index's byte counts and hashes. Index SHA-256: `d0c6e170c2acd42366d645119acd44983e46ab1700cc04b2bd4d610dc404c8b0`.

The two contiguous report parts reconstruct 1,547,807 bytes, SHA-256 `434b0bf46e931b09a74ee48423f636ce95a982255d3508c2ca533ba8ce1c9160`. The private index reports original archive SHA-256 `19ae7b0d8c544a78fa43f00711bdc502adfc5c9d268785c585eccdf87dfae81f` and passing ZIP CRC. The original archive itself was not downloaded or independently CRC-checked here. These checks establish extract/transport integrity, not a new archive signature.

The native files are selected complete events from two 8 MiB captures that end mid-event. They are not complete native traces. Event absence in these selections cannot prove retirement, operation success, or continued execution. Raw files, owner identifiers, local paths, account data and diagnostic URLs remain private and are not committed.

## Shutdown: confirmed rejection, unsafe to waive

The latest receipt is CHECKPOINT_FAILED after 2,032 ms. Its native admission error is attributed to one nonparticipant optional service. Four sticky blocking entries record these audit observations:

| Event | Observed count | Existing classification |
|---|---:|---|
| `os.utime` | 170 | unclassified native persistence operation |
| `os.setxattr` | 170 | unclassified native persistence operation |
| `os.chmod` | 340 | unclassified native persistence operation |
| `ctypes.dlopen` | 170 | external/opaque writer requires explicit participant |

The library-load detail names a service-associated library in Kodi's temporary tree. An audit event precedes the operation; this is not proof of successful loading, metadata mutation, or non-persistence. The metadata details retain event names but not the actual targets, arguments or returns. No image hash, loaded-image/symbol evidence or completed resource-retirement proof is supplied.

The installed inventory samples seven named add-ons and omits this service/library. Neither the exact signed 2103480 APK's member names (including its five nested ZIPs) nor existing workspace filenames supplied its code or native-image provenance. This does not prove an arbitrarily named/obfuscated payload is absent. Aggregate tracked-path counts do not establish the required operation-to-target relationship.

The receipt confirms thirteen essential owners COMMITTED/ALREADY_DURABLE (eleven/two); native admission FAILED; native databases and deferred dialog state remained PENDING. Zero active native writers, sealed admission and complete inventory did not produce sealed/durable essential writes. No checkpoint was saved, termination authorization consumed or process death confirmed. Coordinator generation 0 and native/essential-write generation 1 are distinct fields; do not collapse them.

The exact source chain from the first checkpoint explains this result: audit failure is sticky; retirement of a writer with a sticky blocking failure does not clear that blocker or grant a durable retirement receipt; sealing rejects unknown/opaque effects. Normal verified retirement is a separate supported path. This does not establish that the service is harmless or that the gate is erroneous. No generic metadata/native-library exemption, add-on whitelist, forced exit, timeout increase, or failed-session reset is justified.

**Remaining operation contract:** service code/version/hash; metadata target/descriptor identity and aliases, arguments, result/exception and protected effects; exact library bytes/hash and actual load/symbol/resource lifecycle. Without these, changing classification could permit termination with unproved persistence. No additional owner export/test is requested in this checkpoint.

## Startup: earlier recovery history is not this Home incident

Receipt, process state and Android/native checkpoint records identify the same latest owner/process/session. Command Center was executing at checkpoint request and subsequently reports its essential owner COMMITTED. The source-level retained-session/parked-loop mechanism remains possible, but there is no direct post-failure resident-loop/session observation proving it occurred here.

All six recorded `recoveryAvailable` launcher events belong to an earlier launcher session, before the latest engine process began. The latest `freshMain` precedes that process's recorded birth. A later post-failure chooser session records composition/focus/resume without a recorded launch handoff. These are separate intervals, not proof of Home failure after the latest Close.

For the latest process, Home timing records show requests n6/n7/n8/n9 with one/zero/three/five items respectively. The zero-item request completed and bound; n8/n9 reached first-card presentation. Using paired native monotonic timestamps, the last recorded presentation occurred approximately 49.26 seconds before checkpoint request. None of these rows measures post-failure Home. Android guard history is substantially older and is not attributed to this incident.

**Remaining causal contract:** timestamped identity of the actually incomplete sections; associated launch/owner/generation; resident request/session state after failure; and the active skin body/manifest identity. Existing elapsed-time readiness and retained-session source findings are not a reproduced owner failure. Resetting the checkpoint, forcing widget READY, or modifying navigation is not supported by this evidence.

## Actual installed identity comparison

The selected input remains exact signed APK 2103480, SHA-256 `9cbb4c5f89a214924b6890463aa5842f85b18ff445d04d855e441fa61f4578c2`. Existing original-signature/module checks are reused.

| Installed sample | Comparison with signed 2103480 |
|---|---|
| Command Center 0.3.5.78 | All six inventoried files match, including the performance-corrected `service.py`. This is a six-file sample, not a fresh full module-manifest verification. |
| Active skin 1.0.5.268 | Only `addon.xml` is inventoried; its hash differs from packaged 1.0.5.273. Layout/body/manifest identity is unproved. |
| Health Center | Inventoried `default.py`, `service.py`, `khc_lifecycle.py` match; `addon.xml` differs. |
| Compatibility service 0.8.2 | `addon.xml` differs; its inventoried `runtime_service.py` has no corresponding member in this APK. |

These deployed-source differences are factual identity discrepancies. They do not establish a startup cause and do not authorize blind replacement, provider updates, user-data changes or a downgrade.

## Decision and preservation

Evidence access is RESOLVED. Safe shutdown classification and incomplete-Home causality remain BLOCKED by the specific missing observations above. Both reviewers reject speculative production patches. Historical failures remain failures; no new host/Android/phone test, build, version reservation, signature or release is claimed.

Production diff from a11d4872: zero. The signed 2103480 input, two-file performance correction, essential-save gates, user data, Search, tracking, playback, layouts, shared lifecycle and Cobra remain untouched. Signed 2103481 and networking 2103478/2103479 remain frozen. The IPv4/IPv6 selector remains temporarily hidden with its separate work preserved. No new APK is prepared from an unsupported fix.
