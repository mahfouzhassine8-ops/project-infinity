# 2103351 Full remaining blocker inventory

Parent: green 2103350 commit `45d0cb704a223a594bfde4a96e2d70aa17c380cf`.

Physical Fold evidence: `Infinity-Diagnostics-20261009-151549.zip`.

The 2103350 direct SQLite bridge moved the first observed blocker again. The next first-failure-only result was `script.cu.lrclyrics:default.py — uncaught_script_failure_before_persistence_receipt`. Chasing that add-on alone would repeat the old one-build-per-blocker loop.

## Objective

Keep the checkpoint fail-closed while making one Normal Close inventory every independent blocker that can safely be evaluated.

A writer/owner-local failure is recorded in a bounded, deduplicated blocker ledger. It does not immediately turn the whole checkpoint into CHECKPOINT_FAILED. Clean writers can still retire and independent native owners can still run. Structural failures that make continued inspection unsafe remain immediate/fatal.

At finalization:

- zero blockers -> SAFE_TO_TERMINATE
- one or more blockers -> CHECKPOINT_FAILED
- authorization remains impossible whenever any blocker exists

## Python writers

The native Python ledger now retains all distinct writer failures, their writer id/name, reason, detail and repeat count while preserving the original first-failure fields for compatibility.

A failed interpreter that actually ends is marked settled-failed, not durable-retired. A different clean interpreter can still produce a valid retirement receipt even after another writer failed. File durability sync may complete for inventory purposes, but PollCommit remains false whenever any blocker exists.

The inventory remains bounded at 128 distinct Python blockers. Overflow itself prevents a safe checkpoint.

## Native required owners

Owner-local failures are accumulated while independent operations continue: skin settings, add-on settings, favourites, peripherals, audio policy, Kodi settings, profiles, XML state, databases and related required owners.

Unsafe structural conditions still stop immediately, including lost engine ownership, invalid resident/compat contracts, inability to establish the native database barrier, and lifecycle teardown conflicts.

At deadline, every still-incomplete required owner is recorded as pending instead of exposing only the last blocking operation.

## Health Center

The checkpoint status now contains a structured `blockers[]` array plus the nested Python writer blocker array. Health Center report.txt prints:

- Passed / durable owners
- Remaining Save Blockers
- all Python writer blockers with writer, reason, detail, count and writer id
- first-failure compatibility fields

No provider or add-on is whitelisted. No real userdata path is ignored.

The 2103348 Pillow contract, 2103349 private CPython bytecode-cache contract, and 2103350 direct SQLite observation bridge remain preserved.

This is a test candidate, not a lock.
