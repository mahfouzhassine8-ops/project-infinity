# Infinity 2103377 — startup/shutdown and Android Recents (isolated work)

**Status: source-only partial corrective implementation. Not an installable APK or production lock.**

Parent: exact locked APK 2103376 commit `808b4acc4d1a6aa1cbc8bc4a1848de88b81103e6`.
Protected Skin 1.0.5.211 and all other locked baselines remain unchanged.

## Implemented workstream: closed-task reentry

The original Main is an Android `singleInstance` task. After an authenticated,
durably committed normal Close, the `:kodi` process is killed but Main's
stale Android Recent Apps task may remain. Direct recreation of that Main
may bypass Splash's saved Choose Your Experience preference.

The **only two existing source files changed** on this isolated work branch:
- `repairs/android-checkpoint-shutdown/runtime/android/overlay/tools/android/packaging/xbmc/src/InfinityCloseNativeLease.java.in`
- `repairs/android-checkpoint-shutdown/runtime/android/overlay/tools/android/packaging/xbmc/src/InfinityCloseGuardService.java.in`

The engine endpoint passes `owner.getTaskId()` as an authenticated-session
extra. The coordinator attempts to retire precisely the matching Main-rooted
task **only after** original `confirmedComplete()`, durable `COMPLETE`
receipt, consumed termination authority, and observed old owner death.
It skips and records unknown task IDs, changed owner, wrong root or unavailable
task manager instead of touching an unrelated/current task.

This deliberately removes only a successfully **closed** stale Main task.
Normal Home/background resumes, active main tasks, failed checkpoints and
Force Close are unchanged.

Source-only tests: `python3 -m unittest discover -s repairs/shutdown-recents-2103377 -p 'test_*.py' -v`.
These assert source ordering/preservation; they do **not** certify Android
compilation, Recents behavior on Samsung, or end-to-end correctness.

## Shutdown blocker — NOT declared fixed

`Infinity-Diagnostics-20261012-213246.zip` records
`plugin.video.playlistbrowser:service.py` still in read-side Kodi VFS
`main.py/read_text` during shutdown. Its interpreter cannot be marked
retired while execution remains active. A previous attempt returned after
the 25-second checkpoint deadline, explaining the global checkpoint timeout.

**Do not remove Playlist Browser or disregard all its persistence:**
real playlist source configuration/settings/favorites must be preserved;
temporary playlist/EPG downloads are reconstructible, but their completed
write, rename and retirement need explicit proof. A read frame alone does
not certify that the entire add-on/service is nonpersistent or safe to kill.

The current diagnostic ZIP contains **no byte-exact copy** of the user's
installed Playlist Browser `addon.xml`, `main.py`, or `service.py`, nor a
redacted backend/operation identity. Pinned public source is a reference,
not proof of what is installed on the Fold.

**Next gate:** acquire exact installed add-on source identity and safe
redacted VFS operation details. Patch only proven abort/timeout/cancellation
path with tests for in-progress temp writes and durable user source settings.
Do not weaken `python_services`, `native_admission` or the global
`SAFE_TO_TERMINATE` criterion just to produce green.

## Before building any APK

1. Verify two Java edits compile against exact pinned Android source.
2. Rerun **all 207 approved Android regressions unchanged** and add lifecycle
   tests: failed shutdown, Home/background, wrong task, replaced process,
   successful Close → Ask Every Time, successful Close → saved specific mode,
   Recents, launcher, deep links and Fold multi-window.
3. Obtain and implement proven Playlist Browser cancellation requirements
   without disabling any service or dropping unsaved user state.
4. Prepare a **new, permanently signed versionCode 2103377 candidate** with
   unchanged signer and verified runtime preservation. Do not use the old
   2103376 version code for edited bytes.
5. Physical Galaxy Fold testing and explicit approval required before a new
   lock. Current green source tests are not enough to package or claim success.

No existing baseline branch, APK, installed add-on, or Skin 211 ZIP is altered.
