# Cobra 2103204 — focused physical-device acceptance

Status: NOT PERFORMED by Codex. Automated rendering is not physical acceptance.
Keep locked 2103203 and its complete rollback. Install the candidate as an
in-place update; do not uninstall, reset the app, or clear private data.

Record device/One UI version, installed version, selected appearance, screen
state, font/display scale, and a redacted screenshot or diagnostic report for
each failure. Do not include provider credentials or full stream URLs.

1. Verify the update keeps sources, favorites, recents, profiles, recordings,
   channel preferences and the existing Sound Assistant listing.
2. Select built-in appearance. Inspect Light, Dark, True OLED Black and Follow
   System. Light canvas is white/blue; Dark and OLED canvas is black/blue.
   Raised surfaces deliberately differ from the canvas. Player menus stay dark
   over video, including while the browsing appearance is Light.
3. Check chooser, Home/entry, all five guide layouts, Movies, Shows, Recordings,
   My List, Settings, TV Sources and Health Center. Inspect populated, loading,
   empty and error states. No moved, missing or added functions.
4. Open source add/edit dialogs, confirmations and file pickers. Confirm all
   labels, inputs, radio choices and buttons remain readable and actionable.
   Android's external file picker remains owned by Android/the selected app.
5. Use normal and enlarged text. On cover, inner screen, portrait, landscape and
   a short split window, check headings, corner controls, input caret, wrapping,
   focus trims and scrolling. No overlap or unreachable controls.
6. Open/close player menus rapidly while video plays; tap during their entry
   animation. Test first/last rows, back/cancel, held touch on the scrubber,
   D-pad focus and system reduced-motion/animation-off settings. A tap acts once
   and focus/animation never blocks scrubbing or survives a closed panel.
7. Compare live playback and source switching on known-good/problem channels.
   Check pause/resume, rewind, live-edge shade, return to live, preview/fullscreen
   handoff and audio/video sync. Theme work must not alter transport behavior.
8. Check every display mode, especially Fold Adaptive, while folding/unfolding,
   rotating and resizing split-screen. No stale video dimensions. Complete-frame
   no-crop fitting still requires bars when source/window aspect ratios differ.
9. With a stream known to supply subtitle cues, toggle a real track and Off;
   check selection, size, screen adaptation, immediate input feedback and
   legibility. A saved language preference is not proof of a supplied track.
10. Enter PiP while playing and paused; test SystemUI play/pause and return by
    PiP tap and app icon. Restore Multi-View panes/order/audio owner; verify
    background playback preferences and no unwanted autoplay on dismissal.
11. Check call-time audio under the existing Samsung configuration. Record
    audible results for cellular/VoIP independently; app focus diagnostics and
    Sound Assistant listing alone do not prove audible call mixing.
12. Install/select an existing custom theme; its colors/fonts/styles remain
    authoritative. Test reset to built-in and restore previous. Emergency
    recovery remains visible/reachable; no source or playback setting changes.
13. Switch appearances and navigate repeatedly for a long session. Watch for
    stale overlays, growing memory, jank, input delay, crashes, audio dropout and
    abnormal battery/heat. Transparency must not interfere with playback.

Pass only after real-device observations satisfy these checks. Retain the
inherited 2103203 acceptance checklist for broader nonvisual coverage.
