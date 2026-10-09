# Shared Python / VFS persistence repair 2103344

Test candidate over 2103343 on the isolated checkpoint work branch. No accepted or locked lineage change.

## Evidence and limits

Infinity-Diagnostics-20261008-233410.zip identifies APK 2103343, current PID 4143 and close session a4dce51a-2e82-404c-9bc5-1a3bc4d7be48. The native checkpoint entered playback persistence, then failed with context.seren:service.py missing a persistence receipt. Script evidence independently records python_cleanup_failed_before_save_retirement. SAFE, termination authorization and observed engine death were absent. This establishes an unresolved Python persistence blocker, not that Seren caused every error.

The earlier Kodi_Diagnostics_20261009T025917Z-5d958387.zip (APK 2103342, PID 2778) includes AutoWidget's startup traceback through xbmcvfs.File into the installed observer's vfs_file, raising TypeError: 'str' object cannot be interpreted as an integer. The wrapper closed over a local named original that the subsequent VFS operation loop reused. Consequently file opens could call the final rmdir function. Host tests reproduce the misrouting before the repair. This is a confirmed shared wrapper defect, not an AutoWidget-only patch. The earlier owner-publication failure was separately repaired in 2103343.

## Changes

The VFS File wrapper captures its actual original File constructor at definition time. Reads, omitted modes and append-mode calls retain Kodi's existing argument/mode behavior. This change does not add append support to Kodi's native File API. Write-mode opens still register paths and tracked buffers, and an exception during opening now records a sticky failure. Failed VFS close retains the open handle, leaves it unclosed in observer accounting and blocks finalization; failed writes remain sticky.

Kodi's already-classified SystemExit abort branch now consumes that pending exception on Android before calling onAbort. Previously it left SystemExit pending, which the checkpoint cleanup check could mistake for a new cleanup error. The real CPython harness compiles the actual production abort branch and reproduces the pending exception before the patch. After the patch, committed data can finish interpreter retirement and filesystem sync. A pending SQLite transaction still blocks; a new onAbort RuntimeError still blocks. Neither the ledger nor cleanup's error checks are cleared by this repair. This source defect matches the reported cleanup failure category, but the ZIP lacks the originating exception and therefore cannot prove it caused that particular close.

Script persistence diagnostics now retain the first failing writer's invoker id and add-on/script name separately from the manager's later missing-receipt report. The first failure remains sticky when another writer fails. This avoids interpreting the first completed script as necessarily the originating culprit.

## Validation and preservation

Passed local observer scenarios cover buffered file/SQLite saving, unfinished transaction retention, swallowed write failures, rollback, nested directories, cached aliases, VFS dispatch and VFS open/write/close failures. Real CPython subinterpreter tests cover handled SystemExit, pending transactions during SystemExit, callback errors, interpreter/worker retirement, direct-write bypass refusal and filesystem durability. The production manager lifetime harness, native user-file/protocol writer tests, 30 production coordinator scenarios, package tests and engine-identity tests pass.

The native manifest changes only five overlay hashes: PythonInvoker.cpp, generated observer source, script persistence ledger, checkpoint diagnostic serialization and the candidate engine tag. All 9,374 native parent input hashes remain protected. The Android overlay is unchanged. The reconstructed Infinity checkpoint shutdown, its actual interpreter destruction and filesystem sync gates, Resume Hub / Command Center participation, owner publication repair and selected Kodi 22 StopPlaying lock-order repair remain intact.

Actions must still compile ARM64 and the complete Android shell, verify protected inputs/assets, run inherited/new gates and sign/package the APK. Cache restoration starts with green run 37878314849. Build success is not physical acceptance.

## Device test

Install 2103344 over the current candidate without resetting data. Let the installed services load; open Command Center and Resume Hub. Try Normal Close once. Export the chooser's Infinity diagnostics ZIP, including any failure, before Force Close. After a confirmed close, reopen and verify saved resume position, watched state, settings and favourites. A pass requires a matching SAFE receipt, consumed authorization, observed owner death and preserved data on relaunch. A failure must retain the same truthful refusal and identify its first failing writer. Other add-ons may still expose independent blockers.
