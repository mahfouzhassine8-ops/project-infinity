# Actual signed-431 native presentation baseline

One selected Robolectric API35 test passed with **12 cases, zero failures and zero errors**. Source, exact five-DEX translation pins, native setter histories, complete final text/progress/accessibility state and SHA256 bindings are retained beside this review. No production code was changed, no candidate was tested, and no Activity lifecycle, player, network, Android emulator, signing or shutdown operation ran.

The fixture uses actual signed-431 `cobraRefreshProgrammeLabels`, `cobraRefreshModeDetails`, channel/EPG objects and `CobraModeLayout.solve`. Its counter TextViews/ProgressBar count then call the real Android superclass. A controlled Android/ShadowSystem clock plus **actual current/next programme identity assertions** verifies that valid, expired, absent and unmatched programme scenarios really exercise their intended paths.

With both mode-details guard fields present, all ten active cases show **two native `setText` calls each** for the guide Now and Next labels during full refresh; direct invocation of the existing final mode-details writer performs one each. The final guide text, descriptions, progress and accessibility state match exactly in every active case. Valid current programmes receive two progress writes (`500`, `500`) in full refresh versus one in direct mode-details. With no current programme, full refresh changes progress visibility through `INVISIBLE` then `GONE`; the final writer directly selects `GONE`.

When either the mode eyebrow or layout is absent, the preliminary writer remains the sole writer: one Now/Next/progress call in the selected valid case. Any later production optimization must retain this fallback and keep the existing final mode-details call and all player/quick-peek/playing-indicator responsibilities.

Native Next-label `requestLayout` calls are **2 versus 0** in the Cards current-only scenario, but **1 versus 1** with current plus next. This is specific fixture work evidence, not a general layout/frame-rate gain. Other style strings (Mobile, Grid, Compact, Focus) use the same actual methods and real mode layout with Pro disabled; this does not test Pro-Hero rendering or physical appearance.

Two earlier fixture attempts remain preserved honestly: a nonexistent `compute` signature caused a fixture error before production entry; a second JUnit PASS was rejected during review because its host wallclock seeded programmes in the instrumented production clock's future. The final test uses the actual `solve` signature and programme identity preconditions. Those earlier attempts are not valid current-progress proof.

This independent baseline requires no missing Cards reference image and makes no visual-parity, device latency, frame pacing or thermal claim. It supports a bounded investigation of preliminary guide writes overwritten by the existing final writer; it does not itself implement that correction.
