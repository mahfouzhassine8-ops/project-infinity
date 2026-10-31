# Existing signed438 Display mode results

All PASS entries below are host results using the actual candidate owner DEX translated to JVM bytecode. Physical Fold/decoder acceptance is PENDING for every row. Geometry data: `evidence/ALL-MODES-GEOMETRY.json` (20 measured cases per mode).

| ID | Existing label | Real live selection / persistence | Geometry | Global default |
|---|---|---|---|---|
| 0 | Best Fit | PASS | PASS (20 cases) | PASS |
| 1 | Crop / Fill | PASS | PASS (20 cases) | PASS |
| 2 | 16:9 | PASS | PASS (20 cases) | PASS |
| 3 | 4:3 | PASS | PASS (20 cases) | PASS |
| 4 | Wide 1.10x | PASS | PASS (20 cases) | PASS |
| 5 | Wide 1.25x | PASS | PASS (20 cases) | PASS |
| 6 | Wide 1.40x | PASS | PASS (20 cases) | PASS |
| 7 | Short + Wide | PASS | PASS (20 cases) | PASS |
| 8 | Zoom 1.25x | PASS | PASS (20 cases) | PASS |
| 9 | Zoom 1.50x | PASS | PASS (20 cases) | PASS |
| 10 | Zoom 2.00x | PASS | PASS (20 cases) | PASS |
| 11 | Custom Width / Height | PASS | PASS (20 cases) | Not exposed in defaults; global fullscreen custom editor PASS |
| 12 | Fold Fit | PASS | PASS (20 cases) | PASS |
| 13 | Fold Fill | PASS | PASS (20 cases) | PASS |

Live order: 12, 13, inherit (-1), 0–11. VOD/global fullscreen: 14 choices. Default settings: 13 choices (Custom is configured in the original fullscreen editor, not this defaults list). Inheritance, channel isolation, custom width/height/reset and global custom saved values PASS. PiP safe-fit/return and missing/late metadata PASS with a controlled player. Actual fullscreen window resize/reopening PASS on four host viewports. No decoder, hardware subtitles/audio, actual Fold hinge or Android PiP session is claimed.

Best Fit (0) retains its existing explicit fullscreen fill/preserve-proportions/center-crop behavior; contain is used by PiP. No sizing math was changed. This existing label/description distinction is disclosed rather than silently reinterpreted.
