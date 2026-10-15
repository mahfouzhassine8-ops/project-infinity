# 2103350 direct SQLite observation bridge

Parent: green 2103349 commit `165dbd43c5643d1220487ac7ec5592b706de69e8`.

## Physical Fold evidence

`Infinity-Diagnostics-20261009-072227.zip` proves the 2103349 CPython bytecode-cache repair moved the checkpoint forward. The current first failure is:

`python_writer:sqlite_connection_bypassed_checked_commit_observer`

Writer: `plugin.video.otaku:service.py`.

Playback committed and PVR was already durable. Normal Close remained blocked because a Python service produced a plain SQLite connection outside the checked Connection subclass.

## 2103350 contract

This pass does **not** whitelist Otaku and does not declare an unknown database safe.

The native-owned Python observer now patches all three standard CPython SQLite entry points before add-on module initialization:

- `sqlite3.connect`
- `sqlite3.dbapi2.connect`
- `_sqlite3.connect`

All three are routed through the existing checked `Connection` subclass. The add-on keeps its own SQL, commit, rollback and close semantics. Infinity only observes them and refuses retirement if a transaction is still pending or a commit/close fails.

Direct `_sqlite3` and `sqlite3.dbapi2` committed/closed writes are regression-tested as valid. A direct connection left in a transaction is regression-tested to remain blocked. A connect alias cached before the observer is installed remains fail-closed; the audit hook now records the target database path in the failure detail if such a bypass occurs on-device.

The 2103348 Pillow contract and 2103349 private `__pycache__` contract remain unchanged.

No skin, provider configuration, Resume Hub, Cobra, playback UI, account data, database content, permanent signer or Force Close behavior is changed.
