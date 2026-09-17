# Cobra drawer: View → existing five-mode chooser

Status: source-only, isolated follow-on to locked 2103157. No APK is built,
installed, promoted, released, or locked by this change or its source-check workflow.

The drawer's VIEW MODES heading and five direct mode buttons are replaced with
one **View** row. Its subtitle identifies the current layout and a chevron signals
that it opens a chooser. Activating it closes the drawer and opens the existing
illustrated chooser for Mobile, TV Grid, Compact, Cards, and Focus. The existing
selected-mode marking, mode callbacks, sheet dismiss behavior, and all other
source bytes are preserved. The new row uses the existing focusable/clickable
Cobra sheet-row component and wrap-content height rather than a fixed 50dp row.

## Immutable evidence

Repository baseline commit: `7d95f8dd1696e340bde82cb73ce4e04a0bc2ac98`.
Passing baseline Actions run: `35200244871`.
Evidence artifact: `10488040953`, SHA-256
`bdb4d9317b8062eebaba6644dbd4c130e829ccad21c9713fb9539e303d59bd06`.
Activity SHA-256: `b5d25a639b0c2eb09cf2503b5af40f4d9c5ed4545db9406e8bc7413ef0aa2943`.
Baseline APK artifact: `10488085731`; APK SHA-256
`3e8cda1e8587080802dca1129b5e05c12f881f69efae8f5221103c67948658e3`.
The original locked branch and historical build recipes must remain unchanged.

## Run the source gate

Use `audit157/host/InfinityLiveActivity.java.in` from the exact evidence artifact:

```sh
python3 repairs/cobra-drawer-view/tests/run.py --baseline /path/to/InfinityLiveActivity.java.in
python3 repairs/cobra-drawer-view/apply.py \
  --input /path/to/InfinityLiveActivity.java.in \
  --output /new/path/candidate/InfinityLiveActivity.java.in \
  --rollback /new/path/source-rollback
```

The input is never modified. The output is a separate generated Activity, diff,
and truthful source receipt. The exact input Activity and checksum are preserved
before writing the candidate. This is a **source rollback**, not a device-data
backup or a complete installed-APK rollback package.

Eight local tests passed against the artifact's hash-verified generated Activity.
They include 1,520 executable Java host assertions covering all 50 combinations
of five starting/target modes and two palette branches, plus ten cancel cases.
Production row, chooser, and switch code is executed with UI doubles. These are
NOT Android/Robolectric view tests, physical D-pad tests, playback/decoder tests,
or final visual acceptance. An exact byte comparison protects everything outside
the removed drawer section, including native/player/EPG/diagnostics behavior.

## Future candidate integration (not performed here)

Apply this delta AFTER reconstructing and verifying exact 2103157, and BEFORE
promoting the next candidate's source receipts/version and compiling Android Java.
Record the output hash in that candidate's Activity receipt; do not bypass any
source, JNI, native/assets, signing, or packaging gate. The existing 2103157 build
workflow is deliberately not modified or dispatched and will not apply this new
module automatically. Other simultaneous Health Center/preferences/recovery work
requires a reviewed rebase; the preimage guard must not simply be disabled.

Before delivery, run actual Android view tests for one collapsed View entry,
all five choices, selected marking, Back/scrim cancellation, touch/D-pad focus,
Light/Dark/OLED, large text and narrow/landscape windows. Check playback continuity
on device. Retain the complete matched baseline APK/UI/source rollback in the
future candidate workflow. This commit implements only the drawer request, not
the larger Health Center, per-channel preferences, recovery, or branding plan.
