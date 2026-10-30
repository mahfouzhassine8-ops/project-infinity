# Independent review of the presentation prototype

Reviewed before candidate execution: root's `presentation_patch.py`, its pinned
single-Activity DEX `6354ea6cdc1dfde1745b4463d1e8b17e714ac3a6b52119f597b32c18deab746d`
and the complete patched `cobraRefreshProgrammeLabels` method. No blocking
register-liveness or call-order issue was found.

At the original `:goto_5`, `v0` is still the Activity and `v1` still the preview
channel. The new readiness check uses `v2`; the continuation overwrites `v2`
before reading it. `v3` is likewise assigned before every continuation use.

The fast path initializes the constants the skipped preliminary block used to
leave live: `v4 = 1000.0f`, `v7 = "Next  "`, `v9 = ""`, `v10/v11 = 59999L` and
`v12 = " – "`. The downstream player programme, schedule and upcoming branches
define `v5`/`v6` and temporary wide values before reading them. Their later
reuse of `v7..v12` occurs only after the earlier values' last uses. Initializing
`v8` to zero is harmless; downstream wide writes establish their own pairs.

The exact final-writer readiness guard is `mCobraModeEyebrow != null` and
`mCobraModeLayout != null`. When either is missing, execution enters the
unchanged original preliminary path. Quick-peek still runs before this check;
favorite, player-label/progress, playing-indicator and final mode-details calls
keep their original continuation and ordering.

The selected candidate verification must exercise the actual bound player
progress path (`v4`), next/empty strings (`v7`, `v9`), nonintegral minutes-left
rounding (`v10/v11`) and time separator (`v12`). It compares all final native
view state with the original full tick, not player labels left untouched by a
direct mode-details-only call. This review establishes no decoder or physical
performance result.
