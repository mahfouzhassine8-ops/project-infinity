# 2103352 Python retirement batch

Parent: exact green 2103351 head `7b3a91f1176fcbae57efb4c151190c52f944573d`.

Runtime authority: Fold diagnostic `Infinity-Diagnostics-20261009-175306.zip`.

2103351 successfully changed the checkpoint from first-failure reporting into a bounded blocker inventory. That single close exposed nine failed/settled Python writers plus six still-active writers instead of stopping at CU LRC Lyrics.

## Confirmed 2103351 evidence

Already durable in the tested session:

- playback: COMMITTED
- command_center: COMMITTED
- compat: COMMITTED
- pvr: ALREADY_DURABLE
- 72 Python writers retired cleanly

The remaining Python batch included CU LRC Lyrics, Account Manager, TMDb Movies, SlyGuy, Pluto/SlyGuy provider and ExtendedInfo, while POV, The Crew, TMDb Helper, Umbrella, Trakt and infinity_continuity were still active at the 25-second deadline.

The later settings/favourites/database deadline rows are not treated as confirmed failures; Python retirement prevented the checkpoint from reaching them.

## Repairs

### Cooperative service retirement

`BeginAndroidCheckpoint()` still sends the existing Monitor abort notification, and now also calls `CLanguageInvokerThread::Release()` for noncanonical pending scripts.

Release only exits the reusable invoker wait after script bytecode returns. It does not call Python Stop, does not inject SystemExit, does not join the GUI thread and does not bypass persistence finalization.

The canonical Command Center resident is not released.

### Recovered operation history vs unresolved save failure

The native writer ledger keeps every observed diagnostic but separates:

- blocking persistence failures, which still prevent SAFE_TO_TERMINATE;
- recovered/advisory operation history, which can receive a durable retirement only after the interpreter actually ends and the observer proves there is no pending SQLite transaction, unflushed handle or other hard persistence uncertainty.

The recovered categories are limited to script/SQLite/cleanup errors for which final retirement can independently prove all observed persistent resources are settled. Pending transactions, observer bypasses, file durability failures, unclassified native persistence, unsupported child processes and all other hard uncertainty remain fail-closed.

Health Center reports blocking and advisory entries separately.

### Read-only Android property probes

The child-process policy remains fail-closed. It adds only a narrow read-only contract for Android `getprop` capability/property reads:

- executable must resolve to `/system/bin/getprop`;
- no shell, env override, cwd, preexec or passed file descriptors;
- zero or one property-key argument;
- property key is length bounded and restricted to alphanumeric plus `._-`.

Arbitrary subprocesses remain blockers.

If an unapproved child still occurs, diagnostics record only executable identity and argc, never command arguments, URLs, credentials or environment contents.

## Preservation

2103352 preserves:

- 2103348 pinned Pillow native import contract;
- 2103349 private CPython bytecode-cache contract;
- 2103350 direct SQLite observation bridge;
- 2103351 full blocker inventory;
- normal checkpoint fail-closed termination authorization;
- permanent signer and protected APK payload.

This remains a test candidate. Physical Fold diagnostics remain the runtime authority.
