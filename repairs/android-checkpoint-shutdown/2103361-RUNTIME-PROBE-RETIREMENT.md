# 2103361 Runtime Probe Retirement + Failed-Close Recents

Parent: exact final 2103360 commit `0a759a95eac2cfd28f485bff172e2352dd63ef94`.

## Physical Fold evidence

The 2103360 diagnostic session confirmed the weather .pending blocker was gone, but exposed two separate issues:

1. Failed Normal Close recovery showed both the chooser task and the still-owned Kodi task in Samsung Recents.
2. Save proof was blocked by:
   - read-only `uname` child probes from Otaku / The Crew;
   - idempotent VFS mkdirs reported as failures when the directory already existed;
   - SQLite handles that had already been closed through a cached native/base close route;
   - The Crew native `ctypes` library/symbol lookups that still require exact classification.

Five writers remained active at deadline because SQLite finalization preserved uncertainty rather than discarding it.

## Recents correction

The Kodi task remains alive when a checkpoint is pending or failed. It is **not** force-closed.

While chooser recovery owns the visible UI:

- the exact current Kodi AppTask is marked excluded from Recents;
- the chooser is the only visible Infinity Recents card;
- if Kodi later resumes normally with no pending checkpoint, that same task is made visible in Recents again.

This changes task visibility only; it does not change process ownership, checkpoint authorization, or termination.

## Runtime probe correction

### uname

`uname` is accepted only when:

- the Python observer resolves it to the immutable Android `/system/bin/uname`;
- no shell/cwd/preexec/pass-fd escape exists;
- environment is unchanged except the already-reviewed read-only contract;
- command is `uname` alone or one single information flag:
  `-a -m -s -r -v -n -p -i -o`.

The native audit layer independently re-checks that command shape.

### VFS mkdir / mkdirs

A VFS mkdir call returning false is not treated as persistence failure if the translated target is already an actual directory after the call.

The original add-on return value is preserved. Infinity only corrects its own observation.

### SQLite already closed

If a tracked Connection was closed through a cached/original native close method, probing `in_transaction` raises ProgrammingError because the DB is already closed.

That exact state is treated as retired rather than `sqlite_close_failed`.

Pending transactions remain blocking and are never auto-closed.

## Native lookup diagnostics

`ctypes.dlopen`, `ctypes.dlsym`, and `ctypes.dlsym/handle` remain blocking in 2103361.

Their blocker detail now records the bounded library target and symbol when available, so the next Fold receipt can classify The Crew's exact native lookup instead of weakening all ctypes use.

`ctypes.call_function` remains hard fail-closed.

## Acceptance

PASS requires:

- failed Normal Close shows one Infinity recovery card, not chooser + hidden Kodi owner;
- ordinary active Infinity remains visible in Recents;
- weather .pending remains fixed;
- Otaku/The Crew `uname` no longer blocks;
- YouTube pre-existing VFS directory does not falsely block;
- already-closed SQLite handles do not retain Python writers;
- dirty SQLite transactions still block;
- native ctypes lookups either remain as exact detailed blockers or are absent;
- no save owner is declared durable without its existing proof.
