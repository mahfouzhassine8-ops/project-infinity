# Retain the current Cards browser safely

The actual v3 Cobra owner reuses only its currently attached Cards Grid and adapter when source, profile, policy, membership, theme, geometry and navigation context still match. Other modes and visible directory pages follow the original renderer. There is no second page cache, inventory hash, TTL, cached authorization result, new worker or preference write.

The helper rebinds visible rows through the original adapter, refreshes existing metadata and styling, and leaves selection, focus and pending native scroll restoration intact. Revision hooks precede all four existing channel-list publications and cover existing source/collection/hidden/custom-group mutation paths. Recent and favorite changes preserve the ALL Grid while invalidating affected collection projections. Fresh raw policy values are read on admission; wrong-typed values decline reuse and retain the original fallback behavior. Four unchanged theme classes establish immutable-after-construction theme data ([proof](THEME-SOURCE-PROOF.json)).

The exact 12 Activity-method budget, 14 call sites and preimages are in [SOURCE-BUDGET.json](SOURCE-BUDGET.json); [PROPOSAL.md](PROPOSAL.md) records the bounded design. Revisions may be advanced from existing background callbacks without reading views or preferences. UI reuse/install/disposal runs on the UI thread. Shell/browser/Grid detach and mode exit discard the UI-owned state; the global owner index is weak.

| Selected host verification | Result |
| --- | --- |
| Accepted signed 431, real shell return, 240 Channel objects | 1 Grid added and removed; position 80 restored. |
| Actual v3 owner, same return | Same Grid, adapter and all 240 Channel objects; 0 Grid additions/removals; position 80 and 5px offset retained. |
| Mandatory successful native focus request | Same non-null focused view before/after (identity 2113455629); one strengthened test passed separately. |
| Clock advanced 61 minutes | Original visible-row binding updates current programme, selected state and accessibility. |
| Equal-content publication, two renders before first layout | One necessary replacement Grid; second render keeps its pending restoration; position 80 survives. |
| Real recent/favorite mutators | ALL Grid retained; RECENT and FAVORITES reproject; original visible directory reports fresh counts 2/2. |
| Seven policy/membership/source cases | Wrong-typed profiles/source_meta preserve native fallback; restricted profile, hidden item, custom-group removal, source publication and equal quiet publication refresh correctly. |
| Revision hooks on one background QA thread; mode exit | No hook exception/new worker; dirty inventory rejects reuse; Mobile mode discards state and uses original ListView. |

Evidence: [accepted 431](results/accepted431-native-baseline/OUTCOME.json), [five actual-v3 tests](results/verified-native-v3/OUTCOME.json), [non-null focus proof](results/focus-identity-proof/OUTCOME.json), and [review](results/verified-native-v3/REVIEW.md). Each outcome binds the source, selected tests, jars, controlled fixture and raw result files by SHA256.

These are Android-widget work-count and correctness measurements under Robolectric SDK 35, at 941×1672 mdpi, using real shell/layout/render/auth code and controlled valid EPG data. They establish removal of one observed Grid reconstruction, not a latency, FPS, memory, battery or thermal improvement. Provider executor admissions are recorded; worker bodies and Activity lifecycle startup are not executed. No player/decoder, physical Fold, actual fullscreen return, screenshot parity, APK, emulator, CI, signing or shutdown test was performed by this subtask. Cache/source hook coverage is distinct from executing every mutation route.
