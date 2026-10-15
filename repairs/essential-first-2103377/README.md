# Essential-first shutdown — disabled implementation checkpoint

**Status: NOT COMPLETE. NOT AN APK CANDIDATE. NOT LOCKED.**

The user-authorized implementation is blocked on proving the essential-write
fence with optional Python workers alive. No active runtime overlay, workflow,
third-party add-on, installed APK, skin, Rails component, or locked branch has
been changed by this checkpoint. These new files are an isolated experiment.

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

## Experimental implementation

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

## Necessary continuation within the authorized shutdown scope

1. Implement a native resource fence covering already-open Python descriptors,
   buffered writes, SQLite primary/ATTACH/URI and transaction paths, and native
   VFS/namespace mutations. Audit registration alone is not enforcement.
   Cover any excluded/stop-only interpreter that can still touch shared data.
2. Permit existing first-party callbacks and required database jobs to finish;
   then prevent post-verification protected mutation through process death.
   Keep ambiguous or shared-data operations essential. Preserve optional
   failure diagnostics without claiming their data is recoverable.
3. Update native and active Android validators together with an exact versioned
   essential-owner contract. Retain the full 17-owner diagnostic inventory and
   existing owner-lease death confirmation protocol. Verify the guard service
   distinguishes essential-verified process exit from all-owner graceful exit.
4. Reconstruct the full locked source, apply only the shutdown delta, run real
   callback/failure/concurrency and native/Java agreement tests, compile ARM64,
   and sign only after all applicable gates pass. Preserve the signed rollback.
5. Obtain actual Android death and reopening evidence, then Fold acceptance
   for quick close and ordinary mixed use, app switching, screensaver, progress
   persistence and Rails regressions. No arbitrary viewing-duration gate.

No additional permission is required to continue this already-authorized scope.
Final promotion/lock still requires the user's explicit approval.
