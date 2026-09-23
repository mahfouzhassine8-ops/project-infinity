# Final manual-ownership regression follow-up

The initial 225-case candidate passed run 35822519495. A final source review also identified two manual paths that bypassed Multi-View's reversible fullscreen ownership. These require three further red/green tests before the final candidate is published.

1. Manual Restart live playback treated a promoted tile as an independent single player. It replaced mPlayer but left the tile registry pointing to the released old player, so Return to Multi-View could no longer match ownership. The correction returns ownership to the grid, invokes the existing one-tile retry, then promotes that same tile again. Saved preferences and healthy peers stay intact.
2. Last Channel / explicit playback recall took the ordinary playChannel route, which calls releaseMulti(). For a promoted Multi-View tile, explicit channel selection now reuses an existing peer or replaces only the selected tile using the existing preservation-aware method, then restores fullscreen. This preserves the controls instead of disabling or removing them. Ordinary single-player behavior is unchanged.

The follow-up is an exact two-method patch after the verified first-stage 230 source. All bytes outside those methods must remain identical; the original complete source inventory and receipts are extended, not discarded. Final changed-member inventory is 16, with only the Activity and version Gradle changed in the generated shell. No native rebuild or UI redesign.

Final automation inventory: 220 baseline cases (nine required defect assertions, all others passing), then 228 candidate cases (zero failures/skips). Counts are requirements, not claims of success until RESULT.json and ACCEPTANCE.json record the actual final run.

Additional device checks: from a Multi-View tile promoted fullscreen, use Restart live playback; then Return to Multi-View. Repeat with Last Channel / Recents selecting an already open peer and a new channel. Healthy streams must remain running and the full grid must remain recoverable. These manual operations intentionally may restart/replace the selected stream; Fit/Fill, Enlarge and ordinary fullscreen transitions must not.
