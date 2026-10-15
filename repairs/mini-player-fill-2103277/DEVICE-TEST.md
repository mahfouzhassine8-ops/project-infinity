Cobra 2103277 — Mini-player Fill, Touch-up & Stability RC1
Candidate only. Locked 2103276 remains the rollback; do not lock until Fold acceptance.

Test Mobile, TV Grid, Compact, Cards, Pro in Light and OLED/Dark.
Use actual 16:9, 4:3, portrait, odd-aspect and previously pillarboxed/letterboxed channels.
All embedded video must fill its rectangle with minimum centered crop and no distortion.
Encoded black borders within the actual picture are not aspect-fitting bars; report these separately.
Check source-matching ambient edges, no tint on video, aligned controls/captions/progress/Now Playing,
existing corner clipping and glass focus states, no edge bleed or overlap.
Stress rapid channel switches; pause/resume; fullscreen/PiP/background return;
fold/unfold; rotation; split screen; Samsung pop-up; narrow/wide repeated live resize.
Require no stale ambient, flashes, freezes, lost controls, crashes or resize-induced player restarts.
Verify fullscreen display options unchanged, timeshift/rewind, audio/subtitles/provider continuity,
Multi-View and Sports preserved. Several minutes of moving video, no abnormal heat or frame loss.
Automated geometry/UI/lifecycle checks cannot establish decoder/device stress acceptance.
