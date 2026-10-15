# Infinity 2103288 — Evidence-First Health Center RC1

This is a diagnostic-only update based on the accepted 2103285 native FD repair. It intentionally does **not** include the rejected 2103286 chooser resize and does **not** promote the speculative 2103287 resize repair.

## Install
Install the APK directly over the current Infinity app. Do not uninstall, clear data, run Start Fresh, or change the skin first.

## Responsive/Fold evidence test
1. Open Choose Your Experience → Infinity gear/settings → Infinity Health Center.
2. Tap **Start Responsive/Fold Trace**.
3. Enter Infinity/Kodi.
4. Reproduce the problem exactly:
   - portrait → landscape-left → landscape-right
   - Fold open → closed → open
   - if convenient, split-screen or resize once
   - pause briefly after each transition so the window can settle
5. Return to Infinity Health Center.
6. Tap **Stop & export Responsive/Fold Trace**.
7. Save the generated ZIP and send that ZIP back for diagnosis.

## What the ZIP records
- actual Android activity window bounds
- decor and Kodi SurfaceView dimensions
- Android configuration dp size, density, rotation, system insets
- PiP and multi-window state
- Infinity native bridge requested and committed geometry
- surface/engine readiness and generation/sequence values
- only allowlisted Kodi log lines about resize, native geometry, Infinity layout and skin-file/profile loading
- a conservative ownership summary

It does not upload anything, read account credentials, reset settings, alter providers, change playback, modify the installed skin, or automatically repair anything.

A missing log event is not treated as proof that an event never happened. Physical Galaxy Fold evidence is authoritative for the next repair decision.
