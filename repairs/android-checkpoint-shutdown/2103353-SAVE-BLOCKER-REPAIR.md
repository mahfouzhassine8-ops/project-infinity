# 2103353 Save blocker repair

Parent: exact 2103352 head `028c38300bf649788892a0ac424a16aa43d2526e`.

Runtime authority: Fold diagnostic `Infinity-Diagnostics-20261009-200955.zip`.

2103352 successfully exposed the remaining blocking Python set in one checkpoint attempt instead of stopping at the first failure. The tested blocker inventory contains two concrete problem areas:

- `script.kodihealthcenter:service.py`: two `unobserved_directory_relative_deletion` events.
- `script.module.slyguy:service.py`: read-only Android network probes through `/system/bin/ip` and `/system/bin/ifconfig`, plus the corresponding native child-process observations.

The TMDb Movies SQLite failures, CU LRC Lyrics failure and Pluto/SlyGuy cleanup history remain advisory/recovered operation history and are not changed by this candidate.

## Repairs

### Health Center directory-relative deletion proof

CPython's `os.remove` / `os.rmdir` audit events can carry a `dir_fd`. 2103352 deliberately failed closed because the native observer only knew the relative pathname.

2103353 resolves that pathname through the actual live directory descriptor under `/proc/self/fd/<fd>`, requires the descriptor to still identify a directory, combines it with the relative pathname and sends the resolved namespace path through the existing durability ledger.

If the descriptor cannot be proven, the original `unobserved_directory_relative_deletion` blocker remains. No arbitrary relative operation is treated as durable merely because an add-on requested it.

### SlyGuy read-only Android network probes

The child-process policy remains fail closed. 2103353 adds only these read-only contracts:

- `/system/bin/ip` with exactly one display-only noun: `addr`, `address`, `link`, `route`, `neigh` or `rule`.
- `/system/bin/ifconfig` with no argument or exactly one bounded interface/display argument.

The existing Python observer still rejects shell execution, environment overrides, cwd overrides, pre-exec callbacks, passed file descriptors and other opaque launch forms before granting the native read-only scope.

Mutation forms such as `ip link set ...` or `ifconfig wlan0 down` remain blockers.

## Regression coverage

The native observer test now proves:

- a real `dir_fd`-relative file delete and directory removal can retire durably;
- the narrow `ip route` and read-only `ifconfig` forms are accepted;
- `ip set`, `ip link set ...` and `ifconfig wlan0 down` remain rejected;
- all inherited SQLite, buffered I/O, child-process and retirement failure cases remain fail closed.

## Preservation

2103353 preserves:

- 2103348 pinned Pillow native import contract;
- 2103349 private CPython bytecode-cache contract;
- 2103350 direct SQLite observation bridge;
- 2103351 full blocker inventory;
- 2103352 cooperative Python retirement and recovered/advisory split;
- Command Center and compatibility participants;
- normal checkpoint termination authorization;
- permanent signing and protected APK payload.

This remains a Fold test candidate. Success requires physical-device proof of `checkpoint_saved=true`, durable required owners and `SAFE_TO_TERMINATE`.
