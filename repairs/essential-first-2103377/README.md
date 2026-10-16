# Essential-first shutdown — production repair in progress

**Status: shutdown-only native/Python corrections continue; an actual Java write-boundary gap blocks APK delivery; not locked.**

Continue on `work/infinity-2103377-essential-first-shutdown-only` from the
latest saved source recorded in `PRODUCTION-STATUS.json`. The `5a62f829`
prototype below is historical evidence, not a restart point. The production
path uses the existing script persistence ledger, native coordinator and
database barrier. The prototype
`InfinityEssentialScriptFence.h` remains unwired and its coverage flag remains
false. No third-party add-on or protected feature source is edited.

Latest production correction: `04f9fb1b` (51 native CPython cases, 8 SQLite
cases, 15 coordinator cases). Full ARM64 run `38836846099` passed.
Latest Android run `38837555854` reached 13 of 16 essential receipts and
failed at unverified `/vendor/bin/uname` after 3.4 seconds.
Add-on owner serialization and null-device durability fixes worked. No process
death or successful reopen is claimed. That internal APK was permanently signed from the exact green native build.
The vendor candidate resolves to `toybox_vendor` on a read-only mount; its
command contract remains unverified. All failure assertions were retained. Current source and proof
status are in `PRODUCTION-STATUS.json`; `CHECKPOINT.json` is historical.

The full ARM64 build of `3acc3a9e` passed in run `38819025107`.
The internal Android probe passed permanent signing and unrelated Java
instruction preservation against the locked APK. The fixture correction saved
at `7df06906` restored platform SELinux labels without disabling enforcement.
Probe `38824020906` discovered both unchanged participants and executed actual
Close. Both first-party callbacks completed. Native admission then correctly
refused exit with incomplete repository/installer work and child-command
coverage warnings. This is failure evidence, not process-death acceptance.

A real child-output regression subsequently exposed a protected-file write
capability surviving the old barrier. Production `fork_exec` now transfers
actual output descriptor leases to the existing ledger until OS-confirmed
child death. The protected-file, optional-cache/pipe and numeric-descriptor
cases pass. Unsupported `posix_spawn` file actions remain explicit blockers.
The child-output build passed at `38824257676`. The next correction makes
repository completion diagnostic while retaining its real write leases, and
uses the existing admission guard for synchronous dependency installations.
Actual job-manager and installer bodies verify that late installs do not
mutate data and already-admitted installs retain their required receipts.
Absent command execution is accepted only when every executable candidate is
absent on an actual read-only system mount; writable/unknown paths stay blocked.
The native admission build passed at `38827466985`. A subsequent real child
regression exposed low-level command reentry outside the validated Popen
command. The C entry now verifies actual commands, environment and inherited
descriptors, and leases the exec-error channel as well as stdout/stderr.
These latest corrections still require a full ARM64 build and Android run.
See `PRODUCTION-STATUS.json` and `TEST1-CORRECTIONS.md`. No internal APK has
been delivered, and whole-package death remains unverified.

Android probe `38827602302` subsequently passed the former database admission
stall and reached Kodi, profile, skin and favourite saves. It refused exit in
5.5 seconds because the generic settings ledger serialized a skin placeholder
instead of its existing virtual owner, and because `/dev/null` was treated as
a durable file. The targeted registry/device corrections pass local regression
tests. They still require a full ARM64 build and actual Android acceptance.

Current host verification: 50 actual CPython 3.11.7 runtime cases, 8 actual
SQLite VFS cases, 15 production coordinator cases, 13 production JobManager
cases, 24 production installer cases, and the compiled Android
protocol/guard authorization suite. First-party Command Center and compatibility
Python callbacks run unchanged through the production observer; their Kodi RPC
peers remain host adapters. Actual Android process death and reopening have
not been established. No passing host test is presented as Fold acceptance.

## Exact foundation

- Repository: `mahfouzhassine8-ops/project-infinity`
- Lock: `7d3aca64b34d00520908cf4afd531a4687124525`
- Locked branch: `locked/infinity-2103377-rails-handoff-rc1-20261015`
- Work branch: `work/infinity-2103377-essential-first-shutdown-only`
- Locked APK SHA-256: `de8ce3f122db7bb8b2b3681e7c6ce9caf67cf38888b17ef1f82ff7759fa8a3db`
- Permanent signer SHA-256: `d7adeb68e9341596a02bd3262b737a0f45fc6e771ed7e60285437e833b58c6d7`
- Native evidence: run `38732470818`, source `78826902c0a55a24b488b5b7fc69b378cebc6df8`.
- Signed rollback: run `38733189236`, artifact `11974575677`.

The coordinator was reconstructed from the preserved source transformations,
checking each published intermediate SHA-256. Its final hash matches the green
native evidence: `13b492e2fd4b1885fa2127ebf1ea8bd2ed31fd3cbf35ebe82d3a3044383fa04b`.
The host harness also verifies the exact compiled-source hashes of `CVariant`.

## Reproduced blockers

1. **Native database sealing does not fence Python SQLite.** A real Python
   SQLite connection held an uncommitted transaction. The existing C++ native
   barrier, loaded into the same host process, reported ready and sealed. The
   Python transaction then committed successfully and its row was read back.
   This is a negative control showing the coverage gap, not a successful exit.
2. **An existing writable descriptor can outlive the native seal.** A raw file
   descriptor opened before sealing changed a protected-file fixture after the
   barrier reported sealed. The changed bytes were fsynced and read back.
3. **The shipped Python observer misses SQLite ATTACH destinations.** A
   connection whose main database was private attached a shared database,
   inserted history there, and committed. The actual unchanged observer
   reported no failure and tracked only the primary database. This disproves
   classifying a writer as optional solely from its recorded primary path.

These findings do not establish that the locked application incorrectly
authorized a real close: its original all-interpreter retirement gate remains
active. They establish why removing that gate without replacement is unsafe.

## Historical checkpoint at 5a62f829 (retained negative controls)

`stage_experiment.py` accepts only the exact locked coordinator hash. In a
scratch source subset it changes stage 4 and final native authorization to
depend on a separate essential-write proof, retains the first-party response
checks and native database barrier, and retains all 17 diagnostic owner rows.
The optional Python row is not manufactured as saved. Essential authorization
uses 16 owner rows plus the independent essential-write proof. The existing
deadline, generation, owner identity, PID, one-shot authorization, and legacy
teardown veto remain in place. The experiment does not call the optional
retirement pump or add an optional wait/join/escalation.

The fence prototype tracks observed writers and resources, refuses unknown
capabilities and unretired shared-data writers, retains reused-invoker path
obligations, and distinguishes optional private data from protected paths.
Symlink/hardlink ambiguity and overlapping cache roots fail closed.

**The prototype is deliberately unwired.** `hookCoverageComplete` defaults to
false, no production caller changes it, and shutdown refuses with
`essential_write_hook_coverage_unverified`. Host tests set that field only as
an explicit controlled boundary to test sequencing. That field must not simply
be flipped for a build. A complete native interception implementation and
independent coverage tests must replace the unwired boundary first.

The native experiment is not paired with an updated Android validator. The
active Java validator still correctly enforces the old all-17 contract. No
mixed native/Java candidate has been packaged or authorized.

## Verification actually completed

- 16 compiled host fence/negative-control cases produced their expected
  observations, including the unfenced file and SQLite failures above.
- 12 cases compiled and executed the modified real coordinator with explicit
  Kodi peer adapters. They exercise blocked/failed optional workers, missing
  and failed first-party responses, settings/profile failures, protected
  writers, active native transactions, lease loss, deadline expiry and the
  default unwired-production refusal.
- The separate unchanged-observer test reproduced the SQLite ATTACH gap.

This is **not** 29 fixed device failures. Success cases use controlled save
adapters and a simulated hook-coverage boundary. No real first-party Python
save callback, Android process death, data-preserving Android reopen, complete
ARM64 build, permanent signing, or Fold acceptance was verified in this work.
The prior 274-test suite was not rerun and is not claimed as newly passing.

## Current production path

`apply_runtime.py` verifies exact locked preimages before patching only shutdown
sequencing, native POSIX writes and directories, SQLite registration and the
existing Python observer. Every unrelated locked source hash stays in the
preservation manifest. `native_ci.py` reuses the complete original compiler.

`runtime/` is the active overlay for this work branch. The earlier prototype
and its historical evidence above are retained for reproducibility; they do
not grant production authorization. The active Android validators use the
same essential-first policy, 17 diagnostic rows and 16 mandatory essential
owners as native code. Native SAFE is never represented as process-death proof.

Final promotion or lock requires explicit user approval. Continuing the repair,
verification and safe test packaging is already authorized.


Latest marker correction retains a real negative control for a filename that
collided with the old nonpersistent string. The existing ledger now uses a
non-filename NUL target, and all 51 actual CPython cases pass. Full native
compilation remains required for this change. Owner/device build 38831553869
passed; Android probe 38831677450 is being retried after an emulator archive
download failure before app execution. The Java buffered-write gap remains a
release blocker regardless of the process probe result.


Final verified checkpoint for this repair increment: native `04f9fb1b` passed
full ARM64 build `38836846099`; internal Android run `38837555854` signed the
matched APK but failed Close on the vendor executable proof. Its evidence is
in `android-probe9-result.json`. The Java post-seal write counterexample still
reproduces on the same production headers. Whole-package death and data-safe
reopening remain unverified. No APK has been delivered, promoted or locked.
