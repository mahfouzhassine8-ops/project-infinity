# Actual signed-431 programme presentation baseline

This selected host fixture measures native view writes made by the existing
`cobraRefreshProgrammeLabels` and its final `cobraRefreshModeDetails` call. It
does not construct the production screen, fake a render, start a player or run
an Activity lifecycle method. The baseline uses the accepted 431 DEX translation
already prepared at `/workspace/cobra-evidence/cards431-projection-baseline`.

`SCOPE.json` records the selected cases before execution. The native counter
views always call through to their Android superclass. Text/progress write
histories and final accessibility/state are evidence; fixture `requestLayout`
counts are not device frames or an appearance comparison. Pro is disabled in
the mode-string cases, so those cases make no Pro-Hero rendering claim.

Preparation and execution are separate. Do not compile or execute while the
parent's ABBA timing run is active. After the parent clears CPU use, prepare a
fresh output directory with `prepare.py`, then execute only the test named in
`SCOPE.json`. Preparation verifies all five original DEX pins and hashes the
translated inputs. Results retain the original input receipt and final-state
hashes. A genuine fixture blocker must be reported rather than bypassed by
replacing production behaviour.

No production or delivery files are changed by these sources. No Cards visual
parity, Android runtime acceptance or shutdown result is claimed.

## Selected presentation prototype verification

`CANDIDATE-SCOPE.json` records the subsequent root-selected one-method prototype
before execution. `REGISTER-LIVENESS-REVIEW.md` records the independent review.
`prepare_candidate.py` admits only the pinned DEX, verifies the canonical
accepted-431 method/field boundary, and overlays only its Activity class onto
the exact baseline dependencies. It never produces an APK.

The original twelve-case baseline remains frozen in `results/signed431-baseline`.
The separate `actual431BoundPlayerProgressBaseline` test adds three actual-431
cases without repeating those twelve. The candidate test compares all final
guide/player native view state with those original full-tick results and checks
the actual player-progress continuation. See `results/candidate-presentation-only`
for the fifteen-case outcome, work counts and complete final-state hashes.
