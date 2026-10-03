# Infinity 2103295 — Window-Local Input Repair Lock

Status: locked after physical Fold acceptance on 2026-10-03.

Approved artifact: `Infinity-2103295-Window-Local-Input-RC1.apk`  
SHA-256: `dba26141addbacd64f334bcc32633669ffcc3c4677961e7ce3e23f01684416a0`

Locked source commit: `c562d7d1b0a5cb71df90484dc56a3fae6bf17001`  
Successful build and signing run: `37092252001`

Accepted behavior: controls and the drawer remain touchable at their drawn positions after a freeform or split window is moved, including the lower pop-up position that previously produced an input offset.

Locked contents:

- 2103295 window-local input repair
- inherited 2103291 in-place responsive reflow
- inherited 2103292 Resume Hub 2 and Command Center 0.3.5.19
- existing 2103295 skin companion unchanged

The 2103296 Choose Your Experience presentation is not part of this lock. It remains an unlocked forward candidate while its chooser-specific issue is repaired.

Any further work starts from this locked 2103295 artifact and source commit. The original locked APKs and this approved artifact are not modified in place.
