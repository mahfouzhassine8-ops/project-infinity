# Baseline-first decision

Input: original-signed2103477, APK SHA256
`93eb081cd6a86ff9cf1cb9aa75bc6d9087cd9c982fb46e0a9baa12c12aa9af22`.
CC75 complete80-file manifest `63110023bf70f4ec32b0ab4750b3c1293a4976aa58cdfd1afbcd55027758b371`;
Skin270; Cobra3445. Reuse signed provenance receipt af727772 and retained stockAPI36 qualification.
Branch33e666a0 differs from functional source80f9c78e only by this owner's handoff.
Sources for inspection are read directly from the frozen signed77 APK; older reference directories are not substituted.

Already implemented: bounded/sliced projection copies, batched ListItem submission, selected-provider inventory
filtering, state/source-aware Search cache invalidation, full/reduced/off motion policy, bounded selected-item
cyan loading observation and drawer fallback. Historical host projection timings are not current Android timings.
The rejected loading designs and networking/proxy/native-family changes are not imported.

Current measured bottlenecks: **NOT RUN**. No production patch is justified yet.

| Area | Minimal hypothesis / decision | First selected measurement |
| --- | --- | --- |
| Rendering / refresh | Android already queries modes and uses Choreographer. Portrait mode-list gating and dirty-animation costs are hypotheses, not proven defects. No forced120Hz or speculative EGL/lock edit. | Existing native SurfaceView presentation intervals, separate display inventory/Hz, idle versus native Home/Hub focus motion; retain query coverage limits. |
| Loading | Observer threshold180ms shares an existing resident loop with a500ms wait and other protected work. Do not globally accelerate that loop or weaken its authenticated retired-window survival guard. | Real resident's publication/cleanup timing for explicitly controlled diagnostic preparation; ready, failed and native Back/context cancellation. This is not provider time or first visible frame. |
| UI/motion | Preserve all geometry, themes and existing optional-motion gates. | Native Home/System Hub focus transitions and screenshots; no decorative/layout patch. |
| Stability/resources | No current leak, ANR or source-supported race established. | Same PID/start-tick checks, CPU/FD/thread/status/PSS snapshots and crash evidence over the selected interactions. No global leak proof. |

First named workflow selection: **infinity77-performance-baseline** in existing feature-only workflow393886994.
Exactly one fresh normal signed77 start, no retry; same-process background/foreground return; Home idle and
horizontal focus movement; System Hub vertical focus movement; four controlled loading preparations; bounded
resource and native-presentation snapshots. No explicit provider invocation/benchmark, Cobra activation/test, playback,
shutdown/Normal Close, data clear, source mutation, build or signing in this first probe.

SurfaceFlinger actual-present rings are partial samples, not whole-action FPS/jank or input-to-photon latency.
Java gfxinfo is not native Kodi FPS. Software-emulated display Hz is not physical Fold refresh capability.
First drawn artwork/frame, true touch latency, thermal/battery, actual Fold geometry/high-refresh behavior,
real provider/tracking/playback preservation smoke and mode/theme matrix remain **NOT RUN** in this first selection.
No emulator result grants physical-device acceptance.
Normal startup/Home may autonomously refresh artwork/widgets; this probe does not establish zero network traffic.
Loading observations include diagnostic20ms sampling overhead. Only matching-token publication measures local
owner timing; untagged global cues remain unattributed. Missing eligible frame controls mean local timing is NOT_AVAILABLE.

The complete signed loading observer is preserved, including service.py's exact source/line/authentication
guard against a retired Window. Any later observer edit must reconcile that guard without broad exception handling.
Shared Java/native display, scheduler, input, lifecycle or renderer changes stop unless Infinity ownership and
Cobra noninterference are proven. This broad audit scope is not blanket authority to change shared components.

Stage1 measurements will determine the next minimal patch and affected checks. No version is reserved and
no installer will be offered until the required source, Android, original-key and forward-recovery gates pass.
