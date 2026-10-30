# Signed 2103431 fresh-target guard observation

Run [40975572601](https://github.com/mahfouzhassine8-ops/project-infinity/actions/runs/40975572601) used the same unchanged signed 2103431 APK, with QA source `835f08814190767816a1ec3c14d8698745811c70`. The overall result is **FAILURE**, retained as such. Root verified the uploaded archive SHA256 before extraction. `EVIDENCE.json` binds the APK, source, run, artifact and selected copied bytes; the full raw artifact remains available through its link.

Exact installed public APK bytes were confirmed after the 30-second adb install client timeout. The normal Cobra welcome appeared. The actual visible Fullscreen coordinate press then opened the native fullscreen presentation with Return to preview and Multi-View, without a pinned task. This preserves a real Fullscreen PASS within the failed journey, not a pass for all buttons.

The additional final hierarchy exposed the earlier target-observation problem. Before the extra Hero reveal, `022-ui.xml` shows More at `[858,743][1016,911]` and PiP at `[700,743][858,911]`. After that extra reveal, `023-ui.xml` shows More clipped to `[1011,743][1016,911]`, only **five pixels** wide, and PiP at `[853,743][1011,911]`. The previous measured coordinate `[937,827]` is therefore inside PiP in the post-reveal geometry.

The fresh-target guard rejected this unusable More rectangle and raised `Revealed Pro target missing: More`. **No More press was issued in this run.** The final frame remains in Pro; later PiP and menu-reopen checks were not reached. These hierarchies demonstrate why the earlier coordinate, measured before an intervening reveal/layout, could target PiP instead of More. They do not establish a production More callback defect.

The independent current QA correction is source `8146d518eedecb22cd417785f88aa10ce2a9d608`: reveal once, obtain a compressed native hierarchy, scroll the actual strip where needed, obtain the final hierarchy, and press immediately. It retains the 3.5-second observation guard and existing application timeouts. Run `40976739449` was pending when this evidence record was prepared; no outcome is claimed here. No production changes are justified by this QA geometry finding.

This evidence covers an Android 17 emulator with synthetic QA1, not physical Fold acceptance. Infinity was not launched. No shutdown test, user-device installation, reset, uninstall, production change, signing change or lock promotion is represented by this evidence.
