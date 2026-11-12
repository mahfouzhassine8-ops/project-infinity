# 2103483 Core shutdown investigation

Baseline: owner lock2021a76c; exact signed83 APK
`0c597a2976d9667796a4baac18ed9b624960e22399c94c9f62b1a52393d43236`.
Current status: **installed identity resolved; two unshipped source corrections and10 host cases PASS; native effect/completion proof remains blocked; no successor**. Earlier evidence limits below are historical and superseded where stated in the final update.

## Current evidence and reuse

The owner's November11 summary reports19:18:12 failure of native_admission and
python_services, with the other15 owners complete. This is accepted as an
owner-reported observation. The subsequently supplied private November11 Page corroborates the reported
checkpoint fields. It expressly has no attached raw ZIP or Core source/image
bytes. Its summary is accessible; original byte/CRC verification has not been
repeated here. No new capture or phone test has been requested.

The original audit-ratio reproduction, fail-closed ledger cases, Core source
attribution, old loader prototype and signed83 startup/ARM64 evidence are reused.
The prototype remains uninstalled. Those results do not establish same-profile
shutdown, process death, relaunch or protection of all owner data.

New static analysis authenticated the published Core1.0.1 ARM64 image against
the pinned publisher manifest. Its SHA-256 is
`c4a8a8d1e046cab6a42934b8fba31246efb21a002a90beb2bffa555623a383a9`.
The prior published service source blobeb680f26 hashes to
`69273756ac1dcab82c0c4de3de5cf4e2571b618e1e2f02eef06a3d2618817d4e`.
Neither fingerprint is attributed to installed Fold bytes.

## Confirmed rejection mechanism

The actual83 native source map independently matches these retained headers:

* `InfinityPythonPersistence.h::Audit()` classifies chmod/utime/setxattr as
  unclassified native persistence operations. Records are made before the
  original operation; metadata records do not bind the operation's actual
  target, return, exception or completed persistence effect.
* The same audit path treats an unapproved ctypes image load as an opaque
  capability. A load attempt is not proof of image activation or absence of
  native side effects.
* `InfinityScriptPersistence.h::Fail()` retains a hard blocker.
  `Retired()` removes a settled interpreter from the active map but gives it
  no durable retirement receipt when that blocker exists.
* `InfinityProtectedWrites.h::EssentialWritesLocked()` rejects that opaque or
  unclassified blocker. These reasons cannot inherit the bounded optional-file
  exemptions. Zero active writers does not certify completed protected effects.

This explains the checkpoint rejection without alleging a new83 regression or
demonstrating actual protected-data mutation. The confirmed mechanism survives
the earlier independent-save receipt correction, so completed essential owners
do not resolve this separate native obligation.

## Loading and native completion boundary

The published loader calls copy2, an additional chmod, then CDLL. The previously
reproduced copy2 audit events explain the observed1:1:2:1 metadata/load ratio.
The published Android directory selection reads the full process cmdline;
Infinity's engine process contains`:kodi`, while Android's private app directory
belongs to the package without that suffix. The service can then fall back to
special://temp on external storage. The original November11 morning logs
explicitly show that external target rejected by the Android linker namespace.
This is evidence for failed loading in that captured interval, not proof that
every attempt in the newer shutdown session failed before all native effects.

The published ARM64 `is_core_service_running` export reads byte0x35a1c0.
The388-byte `stop_core_service` export clears that same flag on its return path
and returns1. It also synchronizes, changes shared cancellation/pointer state,
updates reference counts and calls other routines. This inspection does not
prove those callees join workers, nor prove the absence of a join or that a
worker survives. Neither the flag nor return1 independently certifies drained
workers, known file/descriptor effects or durability. Thread/I/O imports alone
also prove neither persistence nor safety.

The Python service calls stop_core_service and discards its result. It supplies
no observed native resource inventory or durable checkpoint participant receipt.
The publisher's PhantomFlare source repository is currently inaccessible via
authenticated GitHub, so this investigation has not established its exact stop
implementation contract from source. Metadata-only adaptation or a corrected
load directory would leave the native completion obligation unresolved and may
activate an engine that previously failed to load.

## Exact remaining requirements

1. Actual installed service source and native image identity, correlated with
   the newer checkpoint. Publisher versions alone do not meet this requirement.
2. Bounded metadata operation-to-target and completion evidence, including
   aliases/descriptors and protected effects. Successful Python retirement does
   not supply this missing information.
3. Either a verified absence of protected native effects, or a supported native
   stop/drain/effect contract that an Infinity-owned adapter can bind to real
   resources and final durability. An arbitrary service-ID exemption, failed-load
   exception string, runningfalse flag, timeout or retired interpreter cannot
   replace it.

GPT6.1 independently reviewed the targeted reference and agrees that a safe
production admission exemption/retirement adapter is not justified yet. The
review explicitly rejects an inference that stop only clears a flag or never
joins a worker.

## Verification and preservation

`inspect_reference_contract.py` completed read-only hash/manifest/source-map/ELF
checks; exact output is `REFERENCE-CONTRACT-RESULT.json`. This is static analysis,
not a lifecycle PASS. Original passing host suites were not rerun. No Core image
was executed on the host, no service was disabled, no persistence blocker was
waived, and no owner files or databases were changed.

Production delta from the locked83 checkpoint: **zero**. New task files contain
only scope, inspection code, sanitized results and this accounting. No APK,
registry, signature or protected artifact changed. Cobra, skin, providers,
Search, tracking, settings and all user data remain untouched.

New correction ARM64 build/link: **NOT_RUN**. Same-profile Android shutdown,
process termination, relaunch and retained-data acceptance: **NOT_RUN** because
there is no complete justified correction to exercise. A baseline Close without
the implicated native service would not verify this failure, so none was used
to manufacture a success. No successor was signed.

## Existing-artifact search follow-up

Read-only search found no named Core members in181 readable retained archives
and195 nested source/component bundles, including eleven large owner bundles
whose central directories were read through bounded streams. One local partial
82 ZIP is unreadable; authenticated original82 and83 member-preservation results
already cover its provenance, so it was not downloaded again. No Core identity
was located in the existing installed-source inventories. The four earlier Fold
exports cover Command Center, Umbrella, POV and Trakt, not this service.

The only located Core library is the previously authenticated publisher
reference. Search limits and counts are in `EXISTING-ARTIFACT-SEARCH.json`; the
full local artifact-path inventory stays private. This is a named-package/member
search, not proof that the Fold lacks the user-installed service. The minimum next identity evidence is a read-only installed manifest/source
fingerprint and actual native-library SHA-256. If these match authenticated
reference bytes already held, no duplicate source/library transfer is needed.
Unknown hashes require the corresponding code/image bytes before effect
analysis. The November11 summary supplies neither installed identity nor this
completion contract; another shutdown attempt would not substitute. Production
remains unchanged.

## Installed1.0.2 targeted correction update

The owner supplied ADB-collected installed SHA-256 identities. Service1.0.2
`2e1b79adc352129696ccfa48a3b5b16f85ebf812026fdd26c3e55d67f34b43b3`
exactly matches the publisher source already held. Native1.0.1
`c4a8a8d1e046cab6a42934b8fba31246efb21a002a90beb2bffa555623a383a9`
exactly matches the previously authenticated and inspected ARM64 image.
**Installed identity is no longer a blocker; no new source export is required.**
The native image has not been activated during this engineering task.

A hash-bound, unshipped source patch now changes only two service functions:

* start_engine maps the exact Infinity engine process name to its Android
  package directory. Other process/package identities remain unchanged.
* run_kodi_service reports the native stop return or exception class and
  explicitly states that native completion is unverified. It no longer prints
  an unconditional clean-stop assertion. This is reporting correctness, not a
  new native stop/drain implementation or a durability receipt.

Metadata copying, retries, source resolution, native API calls, subprocess
handling, other service functions and all Infinity audit/final-seal rules are
unchanged. The patch is not an installer and has not been deployed or included
in an APK. Changing the path could activate a previously blocked engine, so
activation remains prohibited until its completion contract is proven.

Actions43142422868 passed10 explicitly selected host cases on CPython3.11.7
(source1c3486fb). These reproduce the original exact-process path failure;
exercise corrected/foreign identities and failed load; check stop result/error
and no-handle reporting; enforce only two changed AST function bodies; reject
unknown source; and prevent output overwrite. Native callables/filesystem
boundaries are test doubles. No actual Core image, Kodi, Android or owner data
is executed by these cases. Original earlier tests were not rerun.

The prior morning extracts contain233 distinct namespace-rejected attempts
(229+4). Those actual failures did not load the target image. They do not prove
that no worker started in another attempt or later session. In1.0.2 the
start_engine body is AST-identical to the prior reference; the release added
Linux architecture handling and failed-start backoff. The current source hash
does not identify the source used during every historical morning attempt.

The actual metadata audit still lacks each target/result/completion pair.
copy2 can return while some unsupported xattr operations were caught internally;
the explicit chmod catches its own exception; the audit fires before each
operation. Neither an audit row nor a copied-library message proves that every
metadata effect succeeded or completed durably. No historical blocker is cleared.

**Remaining engineering prerequisite:** implementation matching this native
Core1.0.1 image for start/stop and all controlled worker/callback/persistence
owners, or a verified native drain API/effect contract. It must establish closed
work admission, completed native work, bounded actual protected effects and no
protected writes after its completion receipt. The publisher repository offers
the image and Python wrapper, but no matching Rust implementation was found;
authenticated access to its referenced PhantomFlare repository returns404. The
existing running flag/stop return cannot substitute. Existing restart code also
uses an unchecked stop and fixed sleep; no arbitrary delay was added as proof.

The passing unchanged83 ARM64 build is retained. A new compile of unchanged
Kodi source would not prove this third-party library's completion semantics.
New correction ARM64/Android shutdown, actual process termination, same-profile
relaunch and retained owner-data acceptance remain NOT_RUN. No successor was
signed. All protected83 APK payloads, Cobra, providers, Search, skin, tracking,
settings and owner data remain untouched. Exact results and source hashes are
in `TARGETED-CORRECTION-RESULT.json` and `HOST-SOURCE-RESULT.json`.
