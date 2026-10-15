# 2103354 Save retirement + job contracts

Parent: exact 2103353 line `work/infinity-save-blocker-repair-2103353`.

Runtime authority: physical Fold diagnostic `Infinity-Diagnostics-20261009-222247.zip`.

## What 2103353 proved

The Health Center repair is proven on-device. The previous
`unobserved_directory_relative_deletion` blockers are absent.

The remaining checkpoint failure exposed three concrete areas:

1. CPython's own `uuid.getnode()` network identity probes, observed through SlyGuy.
2. Seven long-running Python service invokers that had not retired by the checkpoint deadline.
3. Stock Kodi background jobs that the generic job ledger had deliberately left unclassified.

Recovered CU LRC Lyrics, TMDb Movies SQLite, and Pluto/SlyGuy cleanup history remain advisory and are not promoted back into blockers.

## Repairs

### Exact CPython uuid child environment

Python 3.11 `uuid._get_command_stdout()` resolves `ip` / `ifconfig`, copies
`os.environ`, and changes only `LC_ALL=C` so command output can be parsed
consistently.

2103354 allows only that exact environment shape for already-approved read-only
child commands. Arbitrary environment overrides, shell execution, cwd changes,
pre-exec hooks, passed descriptors, unapproved executables, and mutation command
forms remain fail-closed.

### Cooperative service retirement for Monitor and legacy services

Checkpoint retirement now signals both generations of Kodi Python service API:

- the existing proven Monitor abort notification;
- the legacy `xbmc.abortRequested()` state through the invoker stop flag.

The checkpoint-only stop path returns immediately. It does not wait for the
ordinary Python stop timeout and cannot enter Kodi's `PyExc_SystemExit`
escalation path.

Interpreter retirement still passes through the persistence observer. Pending
SQLite transactions, buffers, workers, or other unresolved persistence state are
retained and continue to block termination while the checkpoint is active.

### Stock Kodi background-job ownership

The Fold inventory exposed the concrete stock Kodi implementations that were
previously retained as unknown jobs.

2103354 classifies only those observed implementations:

- repository update -> required `native_databases`;
- video library scan -> required `native_databases`;
- application initialization lambda -> required `native_databases`;
- EventSource publish lambda -> required `native_admission`;
- directory provider, weather, recently-added and large-image decode jobs ->
  non-persistent/reconstructible display work.

A functional repository/network failure is not treated by itself as proof of
lost user state; actual persistent database writes remain covered by the native
database barrier.

All unrecognized job implementations remain fail-closed.

The detailed native job blocker inventory is increased from 8 to 32 entries so
a future physical-device failure exposes the remaining bounded set in one run
instead of hiding a tail behind the first eight rows.

## Regression gates

The source tests verify:

- the exact `LC_ALL=C` copied environment is accepted for a reviewed read-only child;
- an extra unreviewed environment entry is rejected;
- Monitor and legacy service retirement signals are both dispatched;
- the checkpoint Python stop branch contains no stopped-event wait and no
  `PyExc_SystemExit` escalation;
- pending observer state remains protected while checkpoint is active;
- the observed stock Kodi job classes map to the intended ownership;
- unrelated unknown jobs remain blockers.

## Preservation

2103354 preserves all previously proven work, including:

- pinned Pillow native import contract;
- private CPython bytecode-cache contract;
- direct SQLite observation bridge;
- full blocker inventory;
- recovered/advisory operation split;
- Health Center directory-relative deletion proof;
- narrow read-only `ip` / `ifconfig` command policy;
- Command Center and compatibility participants;
- normal fail-closed termination authorization;
- permanent signing and protected APK payload.

This remains a physical-Fold test candidate. It is not accepted until device
evidence reaches `checkpoint_saved=true`, every required owner is durable, and
the coordinator reports `SAFE_TO_TERMINATE`.
