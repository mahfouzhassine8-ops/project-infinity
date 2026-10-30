# Signed 2103431 host observation timing guard

Run [40976739449](https://github.com/mahfouzhassine8-ops/project-infinity/actions/runs/40976739449) used the unchanged signed 2103431 APK and QA source `8146d518eedecb22cd417785f88aa10ce2a9d608`. Its overall result is **FAILURE**, not a button PASS. Root verified the archive SHA256 before extraction. `EVIDENCE.json` provides exact APK/source/artifact bindings and copied-file hashes; the full raw artifact remains available through its link.

The normal Cobra welcome appeared after the installed public APK hash matched the signed APK. The synthetic source and Pro mode were entered through normal UI. The final observation guard stopped at the **first Fullscreen target**, before issuing a Fullscreen, More or PiP press. `ERROR.txt` identifies `strip_press('Fullscreen')` and the assertion `elapsed < 3.5`.

`015-ui.xml` contains an enabled visible Fullscreen target at `[695,806][853,974]` in the actual native hierarchy. The guard nevertheless rejected pressing it because the host-driven compressed `uiautomator dump` and separate `cat` observation exceeded the 3.5-second freshness allowance following reveal. The existing control-strip visibility window is four seconds. The exact elapsed value was not recorded; the failed assertion establishes at least 3.5 seconds. No application timeout or guard was increased to conceal the failure.

This outcome concerns observation overhead and safely prevented using an expired target. It neither proves nor disproves Fullscreen/More/PiP production mapping. Actual native Fullscreen observations remain separately preserved from runs `40973858059` and `40975572601`. The six passing host tests exercise actual production-view coordinate/key dispatch with explicit terminal spies for fullscreen, menu and system PiP; they are separate evidence and cannot convert this Android run to PASS.

A bounded native on-device UI Automator approach was under read-only investigation when this record was prepared, to measure and press public UI targets without the separate host dump/cat delay. No subsequent result or new CI run is claimed here. Production code and the signed APK remain unchanged.

This was an Android 17 emulator with synthetic QA1, not physical Fold acceptance. Infinity was not launched. No shutdown test, user-device installation, reset, uninstall, production change, signing change or lock promotion is represented by this evidence.
