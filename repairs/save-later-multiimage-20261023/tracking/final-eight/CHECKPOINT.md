# Eight-correction continuation from 2030627

Source baseline: signed run 40045714305 / bc60843572d184e9a528170b88662c6fe04c0f3c. Checkpoint 2030627852ee5779baed54f89a76db2fd5b6ed76 and its passing installer evidence are retained. This checkpoint records implementation and host verification, not Android/Fold acceptance.

| Item | Implementation and evidence | Remaining gate |
| --- | --- | --- |
| 1. Native crashes / CPU / memory | BLOCKED: both Fold tombstones confirm failure but crashing stacks terminate in restore_and_reraise; original fault stack absent, Scudo report truncated. No invented native fix. CRASH-EVIDENCE.json retained. | Original-stack correlation / further physical diagnostics |
| 2. Clock after rotation | Fixed the auto label's nested percentage maximum: reflow was applying 26% inside its already 26%-wide group. Exact native axis implementation reproduces shrink and verifies correction at five sizes. Only one skin attribute changes. | Actual Android rotation and Fold playback/rotate/stop/Home |
| 3. Universal Continue identity | One projection for verified movies and parent-series IDs; original progress key reused, provider-alias progress/time updated without rewriting saved routes. All episode records remain. Namespace conflicts and ambiguous bridges stay separate. Host PASS. | Android Home rail and playback |
| 4. Movies/TV tap and hold | Existing first-select/second-open state machine retained. Only local CC video-list hold dispatch opens its selected-key popup; other media/provider paths unchanged. Host source-boundary PASS. | Actual Android gestures and focus/scroll |
| 5. Applicable actions | Shared owner generates Play/Resume, watched, Watchlist, Favorites, Collection/custom list, Information, visible Continue removal. No Save for Later in these popups. Cancel/stale-selection guards verified. | Android popup interactions |
| 6. Unified updates/removal | Visible suppression is separate from items/history/membership/provider memory. Current playback cannot undo removal; new playback can restore a card. Default tracking writes retain records beyond old pruning limits. Host PASS. | Android selected actions and replay |
| 7. Command Center participant | Retain verified CC32 receipt correction. Exact CC31/32/33 admission, all nineteen CC33 pins, reciprocal bridge/UI pins, and individual tamper rejection checked. | DEX assembly and actual API37 applied receipt |
| 8. POV6.10.22 | Existing production capability verifier rejects six changed source shapes. Added separate reviewed 6.10.22 contract; existing three contracts byte-semantically preserved. Actual provider source remains untouched. Host capability PASS for movies/TV; no live-provider claim. | Actual Android provider route |

Coordinated strict versions: CC0.3.5.33, Watched Bridge1.0.14, UI Repair0.1.16, skin1.0.5.240. Original CC32 source inventory remains admitted. Working TrackIt implementation files and route-selection functions are unchanged. Provider-contract addition is isolated to item8's demonstrated rejection.

Selected host evidence: FEATURE-HOST.json, BINDINGS-LAYOUT-HOST.json, POV-COMPATIBILITY.json; six workflow scope/isolation checks PASS. No shutdown suite, app Close, reopen acceptance, or Android15 executed. No Cobra changes. Native touch patch changes only the local && video branch; clock fix is skin-only. Compilation, permanent signing, package/DEX preservation and separately selected Android17 verification remain necessary. Physical Fold acceptance NOT RUN; no final lock.
