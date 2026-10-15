# Checkpoint blocker diagnostics 2103342

Candidate only. Preserve the reconstructed checkpoint shutdown, the selected Kodi 22 StopPlaying graphics/frame-move lock repair, installed participants, user data and permanent signer. No locked or accepted lineage changes.

## Evidence

Infinity-Diagnostics-20261008-215849.zip reports installed candidate 2103341. PID 23498's Close failed after 47 ms with xml_files:read_metadata_errno_61 and startup_owner_published=false. The preceding PID 22881 Close failed with python_services:foreign_invoker_finished_without_persistence_receipt. Neither receipt authorizes termination. The native-crash tombstone identifies PID 22881 / TID 23093, Thread-3, SIGSEGV, but its captured stack is restore_and_reraise in libinfinitycrash; it does not identify the original fault. Historical native trace rows from 2103334 do not establish what current processes did.

## Changes

- Metadata read failures identify flistxattr size/names/parse or fgetxattr size/value, the attribute name, and the checkpoint file basename. Attribute values and full profile paths are not logged. ENODATA remains a failure; no metadata, fsync or termination gate is bypassed.
- Foreign invoker completion failures retain the invoker ID, add-on ID and script basename. Writer accounting and persistence receipt requirements remain unchanged.
- Health Center exports the original bounded, app-private infinity-native-diagnostics/native-crash-last.txt when present; missing and noncanonical files have explicit availability records. Historical crash evidence is not automatically attributed to the installed version.
- Candidate identity is 2103342, Checkpoint-Blocker-Diagnostics-RC1. Native dependencies/compiler cache restore from passed run 37870441821. Android compiles the complete changed exporter and new version; native code compiles against the protected reconstructed inputs.

## Validation

Production POSIX helper failure-injection tests cover ENODATA at attribute size and value reads, preserved original bytes/inode, no rename or success receipt, and identified syscall/attribute. Production script admission/completion/removal tests verify identified failure and retained unresolved writer obligations. Robolectric exporter checks cover exact original evidence, absent evidence and symlink rejection; these run in the Android shell job alongside inherited exporter tests. Full native/preservation/build gates run in GitHub Actions.

## Device test

Install over 2103341 without clearing data. Open Infinity and let services load, request one Normal Close, then export Health Center diagnostics from the chooser. Export before another installation. The expected diagnostic result names the blocker; this candidate does not claim the phone failure is repaired. A pass requires matched saving confirmation, termination authorization, observed engine death and a successful reopen.
