# Persistence owner audit on the recovered 2103334/2103335 parent

This audit distinguishes actual save paths from their required checkpoint
adapters. It does not claim that every application write has been instrumented.
Native paths below are relative to the recovered engine tree. Android paths are
relative to tools/android/packaging/xbmc/src. Python paths are relative to the
full script.infinity.commandcenter 0.3.5.19 add-on.

| Owner/state | Current implementation | Required checkpoint work |
|---|---|---|
| Kodi settings, media/display defaults, volume, uptime | settings/Settings.cpp, application/ApplicationSettingsHandling.cpp | Freeze mutation/serialization, preserve dirty revision; checked atomic output. CFile::Flush currently returns void. |
| Profile/master-code state | profiles/ProfileManager.cpp OnSettingsSaved/Save | Callback discards save result and runs before main settings output; needs separate checked outcome. |
| Skin settings | addons/Skin.cpp SettingsToXML and 500 ms update timer | Drain/fence timer, propagate serialization failure and prevent a subsequent settings callback from dirtying state. |
| Add-on settings | addons/Addon.cpp SaveSettings | Defaults success=true; failed SettingsToXML can still report true. ReloadSettings/OnSettingsChanged create more work. |
| Playback resume/watched/playcount | application/ApplicationPlayerCallback.cpp; utils/SaveFileStateJob.cpp | Void APIs and discarded commits. A stopped player is not a save acknowledgment. Track final semantic operation and report errors. |
| Playback video/audio/subtitle settings | StoreVideoSettings; video/VideoDatabase.cpp | Void setters can hide SQL errors. Enlist before final state is declared safe. |
| Favorites | favourites/FavouritesService.cpp Save/Persist | Save discards Persist outcome. Retain/retry dirty changes after failures. |
| Sources and explicitly saved playlists | settings/MediaSourceSettings.cpp; playlists/* | Usually saved at mutation time; drain accepted requests and propagate errors. Do not invent persistence for transient queues. |
| Peripheral settings | peripherals/devices/Peripheral.cpp destructor/PersistSettings | Destructor-dependent save is real. Current code discards save status and clears changed settings despite failure. |
| PVR/EPG | pvr/epg/EpgContainer.cpp and channel/group owners | Thread exit performs pending EPG save; classify reconstructible cache separately from user channel/group/search/timer changes and checkpoint required owners. |
| Resume Hub/history/watchlist/ratings/lists/source memory | resume_hub.py load/save, service.py persist_continue, plugin.py mutate | Shared OS gate needed around whole load-modify-save. Service RLock does not cover other Python interpreters. |
| Playback preference memory | service.py persist/_save_playback | Capture while player clock/state remains available; durable checked save. |
| Infinity session | experience.py capture_session/shutdown | Independent checkpoint path required; must not wait for global Monitor abort. |
| Watchdog clean-stop marker | service.py clean_stop | Mark clean only after all required persistence, bound to the same session. Preserve truthful crash/force classification. |
| Kodi-library watched mirror | resume_hub.py sync_kodi_playcount | Currently best effort. Required mapped-library updates must report failure; provider-only entries need explicit not-applicable classification. |
| Accepted info-dialog ratings | music/dialogs/GUIDialogSongInfo.cpp, GUIDialogMusicInfo.cpp; video/dialogs/GUIDialogVideoInfo.cpp | Values can remain in dialog memory until window deinit. Capture only changed accepted ratings, resolve their actual library identity, and check write/readback before the database barrier seals. |
| Calibration edits | settings/windows/GUIWindowSettingsScreenCalibration.cpp; settings/DisplaySettings.cpp | Live resolution/control values must reach the serializable calibration collection. Verify every changed supported resolution and XML field; a settings-file save alone can serialize stale calibration state. |
| Delayed accepted settings values | settings/dialogs/GUIDialogSettingsBase.cpp | A control value can wait for a timer/deinit. Apply the exact accepted assignment without replaying a toggle, action or interactive chooser. Preserve failed obligations. |
| Game video defaults | games/dialogs/osd/DialogGameVideoSelect.cpp | Active dialog values are copied to persistent defaults on deinit. Capture dirty accepted defaults explicitly, check the save, and avoid copying unrelated later game state during retry. |

## SQLite and queued writes

`dbwrappers/sqlitedataset.cpp` start_transaction, commit_transaction and
rollback_transaction discard sqlite3_exec results and update their transaction
flag as though successful. `dbwrappers/Database.cpp` CommitTransaction can also
return true for a missing connection. Consequently the existing outer success
value is not proof of a completed transaction.

CDatabase also owns queued inserts, deletes and multiple-query buffers in memory.
CDatabaseManager manages schema/version state; it is not a live connection or
writer registry. A zero SQLite transaction count would miss those queues.

An application checkpoint must let each owner complete its semantic operation.
It must not blindly COMMIT another owner's incomplete operation. Committed WAL
content must remain available for normal recovery; do not delete WAL files or
require global SQLite teardown merely to call the application checkpoint done.

## Playback ordering

VideoPlayer::OnExit queues StoreVideoSettings and OnPlayerCloseFile through its
outbound job queue. PAPlayer queues its final callback through JobManager.
Application later delivers GUI_MSG_PLAYBACK_STOPPED to Python. The new path
must keep these required executors alive, then await checked outcomes.

The inherited JobManager::BeginShutdown deletes queued work. It is unsuitable
as the new persistence quiesce operation. Likewise stopping new Python launches
does not prevent existing Python threads or native extensions from writing.

Resume Hub's forced progress save returns early if Kodi has already released
the player clock. Capture final position before stopping and reconcile any
completion/watched callback before its final participant result.

## Critical files and Command Center

XBMCTinyXML::SaveFile overwrites destinations directly; CPosixFile::Flush calls
fsync without checking its result. Critical checkpoint output requires a checked
same-directory temporary write, file flush, replacement and directory flush.

The full Command Center common.py atomic_json implementation does check a file
flush/fsync and uses a unique temporary plus os.replace. It does not flush the
parent directory or hold a shared read-modify-write gate. Its read_json catches
errors and returns defaults; a checkpoint must never treat an unreadable store
as an empty successful save. Snapshot/restore copy paths and direct setSetting
paths also require classification and fencing.

## Uncovered owners cannot be treated as clean

Third-party Python sqlite3/file writes and binary add-on private state bypass
Kodi's native database and file wrappers. A generic native flush cannot prove
their application memory is saved. Each required writer needs an explicit
participant contract or a defensible noncritical classification. Otherwise the
transaction must remain CHECKPOINT_FAILED with user recovery available.

## Job and installed-code coverage

An outstanding-job count is not a persistence contract. Network probes and
in-memory notifications may remain alive after the barrier; accepted required
writers still need their checked owner outcomes. A successful generic job return
does not prove private file output or callback state is durable. Unknown native
jobs require a retained obligation even after their completion, just as unknown
Python invocations do. See `runtime-tests/NATIVE_JOB_CONTRACT_AUDIT.md` and
`runtime-tests/NATIVE_LAMBDA_CONTRACT_AUDIT.md` for source-bound classifications.

The available device trace identifies historical add-on launches but not exact
installed source/dependency hashes. `runtime-tests/INSTALLED_OWNER_COVERAGE.md`
records the resulting coverage gap. No missing source, completed interpreter,
empty client map or returned worker join grants permission to terminate.
