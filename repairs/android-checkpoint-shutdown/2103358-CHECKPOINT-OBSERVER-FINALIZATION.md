# 2103358 Checkpoint Observer Finalization

Parent: exact green 2103357 commit `29210b5e2db47bc18341eb5a4bdd2df41b4ca42a`.

## Physical Fold evidence

2103357 reduced the Normal Close Python retirement problem from seven lingering writers to one.

The only remaining writer in the 2026-10-10 Fold diagnostics was:

`plugin.video.redlight:service.py`

The checkpoint receipt showed:

- `active_writers: 1`
- `retired_writers: 84`
- `pending_writer: plugin.video.redlight:service.py`
- blocking reason `checked_python_observer_finalization_failed`
- secondary reason `python_observer_retirement_failed`

The prior noisy/error items remained advisory and were not the save blocker.

## Objective

Preserve 2103357 retirement escalation and remove only a checkpoint-generated termination exception from the persistence observer finalization path.

## Rule

A checkpoint-escalated invoker is identified by its exact native invocation ID.

Only for that exact invoker:

1. if `SystemExit` is still pending immediately before observer finalization, consume it;
2. if observer `finish()` itself is interrupted by `SystemExit`, consume it and retry `finish()` exactly once;
3. no other Python exception is consumed;
4. a failed retry remains a blocking persistence failure.

## Persistence remains authoritative

This repair does **not** make forced retirement equal successful persistence.

The following still block Normal Close:

- open SQLite transactions;
- failed commit/rollback;
- unflushed or uncloseable writable buffers;
- unretired Python worker threads;
- unsupported/unobserved persistence paths;
- any observer exception other than the checkpoint-owned `SystemExit`;
- a failed one-time observer retry.

A checkpoint-escalated service still cannot use forced shutdown as evidence for `restored_after_probation`.

## Host regression

The native observer suite adds two explicit cases:

- `checkpoint-late-system-exit`: clean state + late checkpoint SystemExit must finalize successfully;
- `checkpoint-late-system-exit-pending`: late checkpoint SystemExit + dirty SQLite transaction must still fail closed.

## Physical Fold acceptance

Install 2103358, allow normal add-on startup, then use Normal Close.

PASS requires:

- the previous six writers remain retired as in 2103357;
- Redlight no longer fails merely from the checkpoint-owned SystemExit;
- if Redlight is genuinely clean, Python services reach durable retirement;
- if Redlight owns dirty state, the checkpoint still fails with the real persistence reason;
- no UI-thread shutdown join;
- Command Center / compat protection remains intact;
- quarantine/probation behavior remains unchanged.

Physical diagnostics remain final authority.
