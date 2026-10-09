# Fold 2103338 Normal Close: startup persistence rejection

Evidence: `Infinity-Diagnostics-20261008-211437.zip`, reported app version
`1.0.9-Join-Target-Diagnostic-RC1 (2103338)`, Samsung SM-F976U1,
Android 17 / API 37. User opened Infinity and used Normal Close without playback.

## Observed in the matching session

- PID 25382, owner `74de59c6-d21b-4253-9bb0-8fdfe794dd8c`, session
  `d7b86b5a-5e55-4510-9a7e-48a069c43d6e`.
- Receipt entered CHECKPOINT_FAILED after 52 ms, error `xml_files:open_directory`.
- Native startup owner was registered but not published. Generation was zero:
  the persistence request was rejected before the normal checkpoint began.
- No SAFE_TO_TERMINATE, termination request, consumed authorization, or observed
  engine death was recorded for this session.
- All rows in `shutdown/native.jsonl` and `shutdown/critical.jsonl` belong to
  historical PID 23003, engine `infinity-shutdown-2103334-v1`. Those records must
  not be used to attribute this failure to a Python script or thread join.
- Prior PID 12418 also recorded the same directory-opening error. This export
  supplies neither the failed directory component nor its errno.

## Source repair and limits

OpenParent opened root and every ancestor with O_RDONLY. An app may have search
permission through an ancestor without permission to read/list it. The corrected
helper traverses pinned O_PATH/O_DIRECTORY/O_NOFOLLOW handles, then opens the held
final parent through `.` with O_RDONLY. Atomic rename, file fsync, final-directory
fsync, metadata preservation, symlink rejection and all close/error checks remain
required. Final-parent denial still blocks acknowledgement.

This is a demonstrated source permission defect and a plausible explanation for
the recorded stage, not a phone-verified errno diagnosis. The corrected receipt
includes the errno if a file checkpoint still fails. A controlled syscall test
denies ancestor reads and verifies both replacement and unchanged-file durability;
it also denies the final parent and verifies failure without modifying the file.

The chooser gear previously treated CHECKPOINT_FAILED as pending animation. It now
stops its busy animation on failure while retaining the process/relaunch gate.

Candidate 2103341 retains the checkpoint shutdown, saving participants, invoker
diagnostics and selected Kodi commit 843ed46fc638b0623fd0d25e865e16f676f61273 already
integrated in 2103340. No accepted or rollback ref is changed. Phone acceptance and
the historical Python-join root cause remain unproven.
