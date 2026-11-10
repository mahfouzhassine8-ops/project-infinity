# Essential-First coordinator correction — source candidate

Owner directive: 7dfe1f92. Source correction implemented and independently reviewed; full device shutdown repair remains unproved. No APK was built or signed.

## Actual change

One production file/function changes relative to the exact signed80 native source: `xbmc/platform/android/activity/InfinityAndroidCheckpoint.cpp::Pump()`, stage 6. See `native/SOURCE-DIFF.patch` and the complete task-specific candidate overlay.

Signed80 already excludes `python_services` from essential owners and treats its nonfatal status as diagnostic. That working policy is preserved. The confirmed defect is later: successful database sealing and previously captured deferred state were not marked complete until after global protected-write sealing. An unrelated opaque-writer rejection returned first, leaving those independent receipts PENDING.

The candidate records the independently proved receipts first. Database completion requires an actual successful database seal and no database-owner error. Deferred completion also requires no deferred-owner error and completed, clean, error-free, generation-matched settings/XML receipts. Those dependencies follow the actual settings/game/calibration dialog save paths.

The final protected seal still runs, fails fatally on unknown effects, and grants no authorization. No audit reason is waived. Python observer, writer retirement, alias/descriptor/transaction rules, timeout, native admission, owner lease, termination code and generic failed-checkpoint handling are unchanged. The retained native source tree is unchanged; this is a separate candidate overlay, not a deployed update.

## Focused verification

The exact cases were recorded in `IMPLEMENTATION-PLAN.md` before execution. The harness compiles the full production coordinator, actual persistence ledger, protected-write fence, database barrier and CVariant. Earlier owner receipts and service/JNI/settings adapters are controlled test boundaries. It does not execute the old scenario matrix.

| Observation | Result |
|---|---|
| Unchanged baseline, retired opaque writer | Original pending database/deferred receipts reproduced; final authorization refused. This reproduces a defect, not a successful Close. |
| Candidate, bounded native cache-metadata lease and unfinished optional service | PASS: independent receipts and final proof complete, optional status remains unfinished, one-shot authorization succeeds. |
| Candidate, retired opaque writer | PASS: independent receipts complete; protected sealing and authorization remain refused. |
| Candidate, invalid second database seal | PASS: database/deferred completion and authorization refused. |
| Candidate, failed deferred save | PASS: deferred completion and authorization refused; independent database receipt retained. |
| Candidate, failed settings save | PASS: dependent deferred completion and authorization refused; independent database receipt retained. |

A disposable essential marker retained its bytes. This is not evidence about all owner data. The first host compilation exposed one missing method in the historical peer adapter; the test boundary was updated and the selected cases then ran successfully. Production was not changed to satisfy that harness omission.

GPT-6.1 reviewed native sequencing, dependency guards and test limitations. Astra independently reviewed the source diff for preservation. Both found no blocker in this narrowly scoped patch. Host results bind the baseline/candidate/peer hashes in `HOST-RECEIPT-RESULTS.json`.

## Still blocked; no fabricated successful Close

This patch corrects save receipt accounting. It does not classify the owner's four historical metadata/native-library observations. The native positive test uses an existing bounded C++ metadata lease, not the CPython audit-only path. A universal Python metadata lifetime adapter is NOT IMPLEMENTED here. The owner's unknown library remains unverified; its code/image identity and persistence/resource effects cannot be established from the supplied extracts or packaged baseline.

Minimum remaining source evidence is the exact optional service code/version and associated native image/source or a verifiable supported interface/lifetime contract. Do not clear its ledger, infer safety from optional status or retirement, or add an add-on-ID exemption. No broad diagnostic project, repeated export or physical Close test is requested by this checkpoint.

ARM64 compilation/linkage, the owner's positive/negative Android shutdown cases, actual owning-process death, data-preserving reopen, installation and recovery are NOT RUN. No version is reserved, signed artifact issued, or production shutdown success claimed. The incomplete-Home cause remains separate and unproved; its source is unchanged.

## Preservation

Only the new candidate coordinator overlay contains a production delta. Command Center's signed80 performance worker, Home/readiness logic, Search, tracking, providers, playback, Java/DEX, layouts, user data and all Cobra code remain untouched. Final protected-write and authorization routines are identical to signed80. Signed 2103481 and networking 2103478/79 remain frozen; IPv4/IPv6 work remains separate and temporarily hidden.
