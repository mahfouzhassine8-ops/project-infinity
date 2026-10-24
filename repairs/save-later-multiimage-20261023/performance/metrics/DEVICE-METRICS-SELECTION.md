# Selected read-only Android17 observations

The 2026-10-24 performance addendum authorizes comparable measurements for
Search, Home loading, scrolling, rotation, Option B and idle resource use.
`android_metrics.py` is opt-in, requires a named API37 ADB device and an already
running Infinity process, and never installs, launches, navigates, terminates or
resets the app. Physical observation additionally requires the exact Fold model
and the explicit `--physical-fold-observation` option. No sign-in is involved.

Use equivalent reference/candidate content, orientation, display mode, power
mode and cache condition. Independently select and execute the desired feature
action while the 1–30 second observation window is open. Each phase writes a
new file. The tool deliberately does not clear graphics statistics or caches.

Selected before host execution: `python3 -m unittest -v test_android_metrics`
from this directory. These parser/admission tests use synthetic records only.
They verify interval selection, malformed/pending frames, PID reuse, unit
conversion and API37 admission. They are not application or device tests.

HWUI framestats only measure Android UI rendering (including Search). They do
not establish Kodi/OpenGL FPS. Native SurfaceFlinger samples remain raw evidence
until their layer identity, buffer coverage and presentation fields are checked.
Missing/permission-restricted data is UNAVAILABLE or NOT_OBSERVED, never PASS.
Load/touch latency requires separate real action/readiness/presentation markers;
this observational tool does not invent those timings from elapsed capture time.

No Android/device observation has been run by preparing this helper. No Normal
Close, Essential-First, shutdown, reopen or non-API37 scenario is selected.
