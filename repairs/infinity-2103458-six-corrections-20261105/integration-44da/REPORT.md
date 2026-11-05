# Applied control corrections and consolidated integration status

Continued directly from 44da6e19 on the existing six-correction branch. Signed 2103458 remains the immutable working reference. Two reviewed runtime patches are implemented, not merely proposed. The full six-group correction and successor APK are not complete.

## Implemented source

1. `DialogVideoInfo.xml`: Back 10→9011; Trailer 15→9012; exact associated loading/focus references. Existing PreviousMenu, trailer bridge arguments, conditional Stop, visibility, default focus, theme values and all unrelated controls remain unchanged. SHA-256 `aaba427766b1bff0e4fe5d97641c58b541128bca909c33a5ddef10e9e06fdde9`.
2. `Includes_InfinityMediaLists.xml`: only the three reviewed Up routes for controls 98070/98071/98072 now use visible scrollbar 98066, otherwise list 50. Other actions, gestures and scrolling behavior remain unchanged. SHA-256 `73d33c8dfcb94d6483fc3b2b4356ec64eaede7c7a8cf107134aa2fb49dcedf7c`.

Both files match the exact previously reviewed proposal hashes. Reverse transformations reproduce 44da6e19 bytes. No new native or Python runtime edit was made. The completed drawer removal, height/Power placement and earlier visual corrections remain unchanged.

Historical visual-only checks that require control 10 or byte-identical Up routes describe their earlier checkpoint, not the newly authorized control contract. They were not rewritten to erase history or rerun as unchanged current-source assertions. This integration instead verifies the exact approved ID/navigation delta and reverse-byte preservation, then executes the changed controls. Previous rendering evidence applies to preserved geometry/theme bytes, not untested new dispatch behavior.

## Focused consolidated verification

- **PASS: 23 static checks** covering exact approved transformations, unique control IDs, ordered Details fallback, preserved action bytes, untouched drawer/season changes, Search source, and 11 inspected native-file bindings. Fixture Python compiled successfully.
- **PASS: 58 changed-control checks** in the existing upstream Linux fixture, with explicit responsive-coordinate projection and synthetic metadata. Both Light and Dark exercised three action buttons with overflowing details and one-page fallback, selection retention, Info Back, and one Trailer dispatch without native Extras or duplicate dispatch.
- Trailer used a **test-only receiver in the disposable fixture**. This proves skin dispatch, not actual trailer-provider playback, active-video Stop behavior, or production loading cleanup. Production bridge source was not changed.
- Two earlier campaign attempts remain recorded: the short-window fixture incorrectly assumed a short synopsis meant the entire poster/details group fit; the portrait probe then waited synchronously on modal Info. Only fixture code changed to finish the campaign. The original FAIL and no-result timeout are retained; neither is represented as a production repair.
- Previous unchanged visual, source and negative evidence is retained rather than rerun. Both Search acceptance failures remain **FAIL**. Real 30-search stress, current Android navigation and Fold acceptance remain **NOT RUN**.

See [static results](STATIC-RESULT.json), [campaign notes](CAMPAIGN-NOTES.json), and the complete [final Linux result](../results/540x1260-media-integration-controls-44da-modal-corrected/RESULT.json). No provider playback, application shutdown suite or device installation ran.

## Six-group completion status

| Group | Current status |
| --- | --- |
| Infinity Movies / TV Shows | Packaged direct title-library routes preserved. Actual current skin/window transition remains unverified; no guessed URL/history edits. |
| Drawer | Completed changes preserved exactly. |
| Downloads | Three-file authority acknowledged. Implementation stopped at the explicit reliable-classification gate; no source management/native change. |
| Browser / Info | Prior presentation work retained; approved Back/Trailer and Details behavior patches implemented and tested as above. Universal Android rendering and remaining Info text/accessibility coverage are not marked complete. |
| Search | Consumer/interpreter lifetime findings retained; no safe causal native repair or complete configuration-generation contract established. Both state_changed failures and repeated crash remain unresolved. |

## Preservation and delivery decision

[PRESERVATION.json](PRESERVATION.json) records all four cumulative authorized skin-file hashes versus signed 2103458 and the exact incremental change from 44da6e19. No Cobra, Preview, native engine, provider, playback, shutdown, data, signing infrastructure or recovery-lock modification occurred. No broad refactoring or new production service/worker was added.

No APK was built or signed. This is **not a reported signing-key failure**: the source correction gates remain unresolved. The user authorized stopping Downloads on uncertain classification and required safe Search validation and causal evidence before additional native changes. Packaging now would ship those unresolved defects, not the requested completed integration. There is no successor installability, certificate, package-member or recovery PASS claim.

[BLOCKERS.md](BLOCKERS.md) is the single consolidated dependency report: current source classification; current active-skin/window routing evidence; meaningful-settings mutation tracking plus Crew's actual rejection reason; and native fault/request attribution. Android-only acceptance uncertainty is reported separately and is not itself treated as proof of an unsafe APK or a signing failure. No repeated broad campaign or automatic lock is planned.
