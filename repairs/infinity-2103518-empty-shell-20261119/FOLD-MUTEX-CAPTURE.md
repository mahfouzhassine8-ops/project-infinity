# One Fold capture for startup and the older movie

Diagnostic QA 2103520 failed both features in the owner's Fold test.
Use that existing installation and profile to retrieve the evidence.

The combined stream retains startup milestones, ledger ownership and the
old-save decision codes. It drops raw Kodi log lines,
route URLs, media IDs, titles, saved positions and credentials. The original
Continue Playing filter validates the route codes.

## Retrieve the completed test first

With the authorized Fold USB connection, check the retained Android log before
opening Infinity again. This reads the log buffer without clearing it or
repeating the test.

```sh
umask 077
adb logcat -d -v threadtime Kodi:I InfinityPersistenceMutex:I '*:S' |
  python3 repairs/infinity-2103518-empty-shell-20261119/filter_fold_trace.py \
  > infinity-fold-qa-retained.txt
```

If Android has rotated the retained log, an existing private `kodi.log` or
`kodi.old.log` from the same session may still contain the old-save decision.
Run it through
[the Continue Playing filter](../infinity-2103514-targeted-20261118/filter_continue_trace.py)
and share the filtered output. The mutex probe writes its records to Android
logcat.

## Capture a recurrence if the retained log has rotated

Before opening the app, start this on the Mac with the authorized Fold USB
connection. Run it from the repository checkout, or keep the two filters in
their original relative folders. Use a new destination file.

```sh
umask 077
adb logcat -v threadtime -T 1 Kodi:I InfinityPersistenceMutex:I '*:S' |
  python3 repairs/infinity-2103518-empty-shell-20261119/filter_fold_trace.py \
  > infinity-fold-qa.txt
```

Open Infinity normally. If the empty shell occurs, keep the capture running
while it is visible. Otherwise select a previously failing older movie and
pick the same Resume or Play from Beginning action used when it failed. Allow
the route decision and chooser to appear. Stop the terminal capture and share
only the filtered file. A naturally successful startup still leaves the
intermittent incident unresolved. The diagnostic samples lock attempts
pending for at least 100 ms during the first 20 minutes of the process
trace. It needs neither root nor an app-data export.

A `phase=waiting` row associates a pending lock attempt with the last stable
owner publication for that mutex. Owner zero means the sample had no stable
owner. `phase=completed` reports acquisition and release timestamps and the
wait interval for a slow attempt or long hold. Use the Android PID and native
thread ID to join these events to the same process's interpreter milestones.
The site numbers are 1 for the persistence ledger, 2 for protected writes, and
3 for the Python persistence observer. The line fields refer to the exact
patched native source. A loss, observer start failure, or finite capture
window limits what a missing event can establish.
