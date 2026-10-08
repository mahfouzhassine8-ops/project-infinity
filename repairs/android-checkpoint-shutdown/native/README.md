# Native persistence prerequisite and audit

Status: source preparation and host validation only. This does not activate a
new Normal Close path, implement a complete checkpoint, grant permission to kill
the engine, or claim `SAFE_TO_TERMINATE`.

The exact transformed 2103334 native source, inherited unchanged by diagnostic
2103335, is the preservation parent. The two full-file SHA-256 preimages are
pinned in `preimages.json`. `checked_sqlite.py` refuses any mismatch before
writing and produces a separate two-file overlay. It never edits the parent.
Applying its overlay to a full build must follow independent full-parent
lineage validation; two file hashes alone do not attest the whole engine.

## Implemented prerequisite

- `SqliteDatabase::start_transaction`, `commit_transaction`, and
  `rollback_transaction` check the actual `sqlite3_exec` result and throw the
  existing `DbErrors` type on failure. The existing `CDatabase` catch path can
  therefore observe a failed commit instead of silently returning success.
- `_in_transaction` is refreshed from `sqlite3_get_autocommit` after execution,
  including failure. `BUSY` and deferred-constraint failures retain a live
  transaction; errors after SQLite automatically rolled back clear it.
- Absent/inactive connections reject transaction operations.
- `CDatabase::CommitTransaction` returns false for a null connection.
- Existing successful begin, commit and rollback behavior is retained. There is
  no automatic retry, rollback, deadline, cancellation or termination policy.

Generate the overlay outside the preservation tree:

```sh
python3 repairs/android-checkpoint-shutdown/native/checked_sqlite.py \
  --source-root /absolute/path/to/exact-3334-source \
  --output-root /absolute/path/to/empty-sqlite-overlay
```

Run the host tests against the same exact source:

```sh
python3 repairs/android-checkpoint-shutdown/native/test_checked_sqlite.py \
  --source-root /absolute/path/to/exact-3334-source
```

The test runner extracts the actual transformed production transaction methods
and `CDatabase::CommitTransaction` into a minimal C++ harness. SQLite calls use
the real host SQLite shared library. Only Kodi logging, trace and class-context
dependencies are substituted. If development headers are absent, the harness
declares the stable subset of the SQLite C ABI; it does not implement or mock
SQLite. The test also executes the original production methods to demonstrate
that the regression scenarios fail before the change.

Coverage includes ordinary commit/rollback and reopened-file persistence;
competing-writer `BUSY` begin; nested begin; shared-reader `BUSY` commit followed
by a successful retry preserving the original transaction; deferred foreign-key
failure and repair; actual `SQLITE_FULL` automatic rollback; authorizer-denied
rollback and retry; no-transaction errors; missing/inactive connections; and
preimage/output isolation guards. This is not an Android/native-engine build or
device shutdown test.

## Audit references: unchanged 3334 parent

Paths and line numbers below refer to the exact preimage, not overlay line
numbers. All paths are relative to the native source root.

| Owner/path | Evidence | Required integration work |
| --- | --- | --- |
| `xbmc/dbwrappers/sqlitedataset.cpp:549`, `:558`, `:568`; `xbmc/dbwrappers/Database.cpp:763` | SQLite transaction status was ignored; a null native DB commit reported success. | This overlay fixes those specific false-success reports. Callers still need to consume failures. |
| `xbmc/dbwrappers/Database.cpp:359`, `:430`, `:478`; `xbmc/DatabaseManager.h` | Multiple-execute, insert and delete SQL can remain queued in memory. DatabaseManager tracks schema readiness, not live writers. | Register actual writer owners/connections; drain already-accepted required work; acknowledge only checked commits. Do not commit a foreign owner's transaction from a coordinator thread. |
| `xbmc/application/Application.cpp:2137`, `:2182`, `:1964`; `xbmc/platform/android/activity/XBMCApp.cpp:547`, `:597` | Current close invokes script preparation, activity finish, native Stop/Cleanup, and application-thread joining. | Add a separate checkpoint transaction. Do not invoke this destructor chain as its completion condition. |
| `xbmc/utils/JobManager.cpp:212` | BeginShutdown cancels active jobs and deletes all queued jobs. | Add distinct quiesce admission, retain accepted persistence jobs, and drain their results. Never reuse cancellation of every queued job as proof of persistence. |
| `xbmc/interfaces/generic/ScriptInvocationManager.cpp:76`; `xbmc/interfaces/python/XBPython.cpp:586` | First rejects new launches only; second broadcasts abort and starts shutdown grace. | Dedicated writer/save acknowledgments for Infinity services. Existing scripts, private Python sqlite3 connections and direct file writes bypass the native DB wrapper. Unknown active required writers must fail the checkpoint. |
| `xbmc/cores/VideoPlayer/VideoPlayer.cpp:2530`, `:654`; `xbmc/cores/paplayer/PAPlayer.cpp:1154` | Final video settings/resume callbacks run as queued jobs; VideoPlayer destructor waits for them. PAPlayer submits its callback directly to JobManager. | Preserve the persistence executor, add final-save acknowledgments, gate new/auto-next playback, and avoid treating player CloseFile as save completion. |
| `xbmc/application/ApplicationPlayerCallback.cpp:94`, `:285`; `xbmc/utils/SaveFileStateJob.cpp:32` | Playback state and per-file settings APIs are void; database failures/commit results are lost. | Propagate checked results through bookmark, playcount and per-file settings writes. A stopped player alone cannot acknowledge them. |
| `xbmc/application/Application.cpp:3079` | Stopped GUI message leads to Python OnPlayBackStopped after native player callbacks. | Keep message processing available and let Resume Hub checkpoint after its final stop callback. Suppress newly queued playback. |
| `xbmc/settings/Settings.cpp:150`, `:157`, `:173`; `:560` | Core settings include registered display/media/skin/uptime/view subsettings. | Snapshot dirty generations under owner serialization, then use checked durable file persistence. |
| `xbmc/profiles/ProfileManager.cpp:128`, `:225`; `xbmc/settings/lib/SettingsManager.cpp:178` | Profile-save callback discards its result and runs during settings serialization, before the main settings file write. | Separate checked profile acknowledgment; do not infer success from the outer settings return. |
| `xbmc/addons/Skin.cpp:1100`, `:1127`, `:1132`; `xbmc/addons/Addon.cpp:375` | Skin serialization logs failures but returns true; its 500-ms save timer can run later. CAddon may return true after serialization failure and notifies add-ons/Python after saving. | Freeze/drain the timer, propagate serialization/write errors, and prevent post-save notifications from redirtying acknowledged state. |
| `xbmc/favourites/FavouritesService.cpp:170`, `:194` | Immediate persistence exists, but Save discards Persist failure and returns true. | Track dirty/failed or in-flight edits, retry through a checked owner acknowledgment. |
| `xbmc/settings/MediaSourceSettings.cpp:108`; `xbmc/playlists/PlayListM3U.cpp:216` and sibling formats | Sources normally save on edit; several playlist saves are void. | Preserve accepted writes and propagate errors where required. Do not invent shutdown saves for transient data with no prior persistence contract. |
| `xbmc/peripherals/devices/Peripheral.cpp:86`, `:517` | Destructor saves peripheral settings; its void writer discards save result and clears changed flags. | Extract checked dirty persistence independent of object destruction. |
| `xbmc/pvr/epg/EpgContainer.cpp:239`, `:444`; channel/group Persist methods | Thread exit saves dirty EPG; PersistAll discards queued-write commit results. | Classify reconstructible EPG cache separately from critical user channel/group/search/timer state; checkpoint critical owners with correct locks and returned results. |
| `xbmc/utils/XBMCTinyXML.cpp:106`; `xbmc/platform/posix/filesystem/PosixFile.cpp:221` | XML overwrites its destination; flush is void and ignores fsync failure. | Checked atomic critical-file save, checked flush/rename/directory durability; no blanket file flush can save unsent memory state. |
| `xbmc/platform/android/activity/JNIMainActivity.cpp:38` | Existing Infinity native registration point. | Add asynchronous session/PID/token-bound checkpoint request/status bridge, separate from TMSG_QUIT and lifecycle destruction. |

## Remaining release blockers

1. An Android coordinator must own the entire session and engine identity;
   lifecycle callbacks and legacy cleanup cannot independently declare success.
2. Quiesce must close nonessential work admission while retaining the owners and
   executors that finish required persistence. Native, Python and Android writers
   need an explicit participant/generation contract.
3. Playback, settings, skin, profile, favorites, queued DB writes, peripheral
   settings, and relevant PVR state need checked acknowledgment paths. This
   SQLite prerequisite intentionally does not claim to provide them.
4. Infinity Resume Hub/session/Command Center owners must flush their real dirty
   state, including final playback callbacks. They are outside this native xbmc
   source and need their own audited barrier integration.
5. Handle read-only profiles, remote MySQL/UPnP/PVR state, provider-owned writes,
   absent owners and unknown active writers explicitly. A generic SQLite WAL
   checkpoint, fsync sweep, idle counter, timer or exception-free wrapper is not
   sufficient evidence that they saved their state.
6. Existing CDatabase BeginTransaction/RollbackTransaction wrappers still swallow
   exceptions, and many callers ignore CommitTransaction's bool. The complete
   checkpoint must use checked contracts all the way to its acknowledgment.
7. Only after every required participant reports a durable generation and new
   writes remain gated may the coordinator accept SAFE_TO_TERMINATE and request
   engine-process death. Timeout/save failure produces CHECKPOINT_FAILED with
   explicit user recovery. It must not silently become force close.

No route activation or APK build is included in this narrow prerequisite.
