# Recorded Display geometry — exact baseline vs candidate

Measurements are from the real production TextureView inside verified native Android window bounds. Source metadata is controlled; decoded video remains unverified. These observations do not independently establish product acceptance.

| Mode | 1920x1080 source / 800x600 pane: baseline picture | Candidate picture | Utilization before → after | Proportional crop before → after | Physical |
| --- | --- | --- | --- | --- | --- |
| Fold Fit | [-16.0, 66.0, 816.0, 534.0] | [-16.0, 66.0, 816.0, 534.0] | 78.0% → 78.0% | 3.8% → 3.8% | UNVERIFIED |
| Fold Fill | [-133.3, 0.0, 933.3, 600.0] | [-133.3, 0.0, 933.3, 600.0] | 100.0% → 100.0% | 25.0% → 25.0% | UNVERIFIED |
| Inherit Default | [0.0, 75.0, 800.0, 525.0] | [-133.3, 0.0, 933.3, 600.0] | 75.0% → 100.0% | 0.0% → 25.0% | UNVERIFIED |
| Best Fit | [0.0, 75.0, 800.0, 525.0] | [-133.3, 0.0, 933.3, 600.0] | 75.0% → 100.0% | 0.0% → 25.0% | UNVERIFIED |
| Crop / Fill | [-133.3, 0.0, 933.3, 600.0] | [-133.3, 0.0, 933.3, 600.0] | 100.0% → 100.0% | 25.0% → 25.0% | UNVERIFIED |
| 16:9 | [0.0, 75.0, 800.0, 525.0] | [0.0, 75.0, 800.0, 525.0] | 75.0% → 75.0% | 0.0% → 0.0% | UNVERIFIED |
| 4:3 | [0.0, 0.0, 800.0, 600.0] | [0.0, 0.0, 800.0, 600.0] | 100.0% → 100.0% | 0.0% → 0.0% | UNVERIFIED |
| Wide 1.10x | [-40.0, 75.0, 840.0, 525.0] | [-40.0, 75.0, 840.0, 525.0] | 75.0% → 75.0% | 9.1% → 9.1% | UNVERIFIED |
| Wide 1.25x | [-100.0, 75.0, 900.0, 525.0] | [-100.0, 75.0, 900.0, 525.0] | 75.0% → 75.0% | 20.0% → 20.0% | UNVERIFIED |
| Wide 1.40x | [-160.0, 75.0, 960.0, 525.0] | [-160.0, 75.0, 960.0, 525.0] | 75.0% → 75.0% | 28.6% → 28.6% | UNVERIFIED |
| Short + Wide | [-96.0, 111.0, 896.0, 489.0] | [-96.0, 111.0, 896.0, 489.0] | 63.0% → 63.0% | 19.4% → 19.4% | UNVERIFIED |
| Zoom 1.25x | [-100.0, 18.8, 900.0, 581.2] | [-100.0, 18.8, 900.0, 581.2] | 93.8% → 93.8% | 20.0% → 20.0% | UNVERIFIED |
| Zoom 1.50x | [-200.0, -37.5, 1000.0, 637.5] | [-200.0, -37.5, 1000.0, 637.5] | 100.0% → 100.0% | 40.7% → 40.7% | UNVERIFIED |
| Zoom 2.00x | [-400.0, -150.0, 1200.0, 750.0] | [-400.0, -150.0, 1200.0, 750.0] | 100.0% → 100.0% | 66.7% → 66.7% | UNVERIFIED |
| Custom Width / Height | [0.0, 75.0, 800.0, 525.0] | [0.0, 75.0, 800.0, 525.0] | 75.0% → 75.0% | 0.0% → 0.0% | UNVERIFIED |

Bounds are left, top, right, bottom in pane pixels. Negative/outside bounds are clipped by the pane. Utilization is picture intersection area / pane area. Crop is geometric intersection / transformed picture; this cannot detect bars encoded in the source or establish the actual decoder crop.

Full 240-pair record: Display-observed-before-after.csv. Fixed aspects/Wide/Short/Custom intentionally reshape the picture, so proportional crop alone does not describe distortion. Inherit uses the fixture default; separate transition tests change the actual global control. Custom starts at saved 100% values; reset/isolation are separate tests.
