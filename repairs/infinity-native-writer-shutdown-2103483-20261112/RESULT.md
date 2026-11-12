# 2103483 Core shutdown investigation

Baseline: owner lock2021a76c; exact signed83 APK
`0c597a2976d9667796a4baac18ed9b624960e22399c94c9f62b1a52393d43236`.
Status: **native effect/completion proof blocked; no production patch or successor**.

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
search, not proof that the Fold lacks the user-installed service. The next
necessary source evidence remains the installed service code/manifests and its
actual native image bytes. The November11 diagnostic summary supplies neither;
another shutdown attempt would not substitute. Production remains unchanged.
