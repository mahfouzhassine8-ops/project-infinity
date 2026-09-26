# Infinity shipping audit RC1 — partial source audit, not release approval

The current continuation is documented in [followup/README.md](followup/README.md). Native 2103254 remains the user-selected audit candidate, not a new stable promotion. Cobra and the protected original/rollback branches remain unchanged.

Current component candidates are Health Center 2.5.17, Authorization & Accounts 0.5.2, and dialog-only skin source delta 1.0.5.168. The native identity correction is staged source only: no native build, replacement APK or FD_SET crash fix has been produced by this audit.

The current independently runnable test set is 113 offline regressions (55 retained plus 58 follow-up). The preceding 60-test suite overlaps these and must NOT be added to the count. An earlier local 82-check report was not recovered in this continuation; it is not used as current acceptance evidence. Local static validation separately parsed 557 XML and compiled 15 Python files; it does not establish device rendering or real provider functionality.

## Native finding

The 06:42Z diagnostic retains exactly the same Android FD_SET abort seen in the 05:35Z export: 2026-09-26T05:28:17.334Z, PID 31571. This is historical relative to the later export, not proof of a fix or a pre-2103254 event. Current collector version is not an exit-event version. The trace contains 1,340 open FDs, including 1,073 ZipArchive-owned descriptors referring to different APK paths, not repeated copies of one APK. Resource retention is a lead, not a proven culprit. The original failing stack is obscured by recorder re-raise; the compared libkodi files have no usable Build ID. Exact native attribution/root cause and physical-device stress remain release blockers.

## Preservation

Exact source commit: 84f293d753b863a06c9366d9575b459a9e2992d9.
APK SHA-256: c526f740f258c48e3a208ccac6659f22995d077ff6a5097fc3d4d6617a51625e.
Packaged libkodi SHA-256: c7976ce0adb45b9264f2092a27111be4e05bde4220be2b26b1ea0e2cc74f1e2d.
The protected 2103229 rollback is not overwritten. Audit sources and tests live only on infinity-2103254-shipping-audit-rc1. No user-data/credential wipe, add-on removal, unrelated layout changes, or Cobra native/player modifications are authorized.

## Source formats

The original payload is retained for regression and known legacy repair fixtures. The follow-up payload contains the current guarded source deltas and current tests. Both are bounded base64/XZ UTF-8 JSON source maps, verified before extraction. Complete component sources are reproducible with apply_deltas.py and the exact owned baseline ZIPs; the script writes only a NEW review directory. No fonts, raw device diagnostics, or user credentials are published here. The skin source delta is NOT a Kodi-installable full skin.

## Acceptance still required

This work does not claim every screen/control, Android lifecycle, playback/provider flow, widget/weather performance, native resource stress or shutdown path has been exercised. Full native stability, actual Trakt server refresh/history, real UI rendering/touch/remote traversal, integrated packaging and signed APK verification when applicable, and physical-device launch/exit/playback/export tests remain open. A green source workflow is not a completed end-to-end shipping audit.
