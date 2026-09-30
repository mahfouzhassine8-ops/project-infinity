# Responsive intended behavior, established before candidate observations

| Surface | Intended result | Automated evidence | Physical boundary |
|---|---|---|---|
| Choose Experience popup | Reflow choices ≥55% pane area; fully visible names ≥15.5 px at mdpi, settings ≥48dp, Enter/gear nonoverlap | Actual production Views and Canvas, multi-window harness, 8 actual measured shapes × both appearances | Samsung popup/split actual screenshot review |
| Fullscreen chooser restore | Pixel-identical approved same-size rendering; same controls/action owners | Before/resize/after bitmap comparison + locked golden renders | Samsung fold/insets |
| Cobra sizing helpers | Measured window beats physical display metrics/orientation | Deliberately mismatched display and window | System live-resize callback/insets |
| Live TV modes | Same persistent shell, usable channel viewport, retained route/data/provider objects | Native production guide 5 modes × 5 shapes with populated controlled channel data | Real providers/artwork/player |
| Drawer | Open drawer reflows within current window; Power reachable | Actual drawer stays open during resize | Safe areas/keyboard/OEM |
| Player/Display | Same texture/player/source; no prepare/release/seek; stored transform truthful; Close reachable | Controlled Media3 state, actual TextureView/chrome/sheet at 5 sizes | Decode/audio/timeshift/Samsung WM |
| Infinity .172 native Home/widgets/library/navigation | Intentionally usable at every actual window shape, preserved section/player/provider state | Source/payload preservation only | NOT VERIFIED: actual native Kodi renderer needs physical device |
| Options/Health/Recovery/Multi-View | Header/dismiss/action access; independent tile owners; no loss on resize | Existing intended-outcome suites retained and expanded where feasible | Real native/OS actions and every current screen |

No-crash, callback existence or stored preference alone is not acceptance. Automated candidate must never be called device-passed, locked or complete end-to-end physical verification.
