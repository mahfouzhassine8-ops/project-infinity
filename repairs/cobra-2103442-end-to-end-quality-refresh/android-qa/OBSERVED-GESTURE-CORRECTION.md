# Public-input harness correction after run 41281620906

This run failed on accepted 2103442 before installing the candidate. At
06:46:25.009 Android's InputDispatcher reports the system swipe-up monitor
stealing the injected gesture. The resumed activity is then Nexus Launcher.
Cobra PID 6651 remains alive; the fatal exception belongs to QA PID 7282.

The driver started each list swipe at `list.bottom - 30`. TV Grid's list extends
to the screen's bottom gesture region, so that coordinate initiated Android Home.
The captured TV Grid image shows real decoded loopback playback and guide content
immediately before the swipe. This is not candidate crash evidence.

The QA-only change intersects the observed list and window bounds, then swipes
between the interior three-quarter and one-quarter positions. It records those
actual bounds and endpoints. Screenshot capture now precedes the strict package
assertion, so a future wrong foreground can be seen rather than losing its image.
No app byte, input ownership assertion, timeout, production gesture or system
navigation setting changes. The corrected driver compiles successfully.

The original artifact and failure remain available:
https://github.com/mahfouzhassine8-ops/project-infinity/actions/runs/41281620906/artifacts/13074265331

Its baseline also emitted repeated layout warnings. Those logs do not establish
an application crash or the responsible callback; no speculative player-layout
patch was made. UI-observer overhead remains included in reported observations.
The next comparison must reuse the exact signed 2103443 APK.
