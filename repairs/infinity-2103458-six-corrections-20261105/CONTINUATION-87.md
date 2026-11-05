# Source-only continuation from 87efb5ec

Signed 2103458 remains the immutable working reference, not physical acceptance. No APK, native build, signing, installation, promotion or lock was performed. The historical diagnostic capture is 2103456; the current device installation and active 2103458 skin/modules remain unverified.

## Implemented presentation corrections

Only three runtime XML files changed since 87efb5ec, under the existing skin overlay:

- `DialogVideoInfo.xml`: episode-aware existing artwork binding; retain proportional scaling, align artwork to its original upper-left anchor, and attach the existing rim to the rendered image instead of leaving an independent tall empty frame. Preserve all IDs, native mappings, actions, metadata, visibility and loading behavior.
- `Includes_InfinityMediaLists.xml`: use a real episode thumbnail only after the existing poster/season/show-poster priority. A mutually exclusive short thumbnail frame avoids reserving a full poster height for that landscape image. No generic directory-icon fallback. The Info-only variable preserves the existing PosterThumb fallback for other content.
- `Variables.xml`: the existing season plot variable ignored available item synopsis whenever Container.ShowPlot was empty. Add one Videos/seasons-only fallback to supplied ListItem.Plot, preserving collection precedence and every existing nonempty ShowPlot/other-content branch.

The completed drawer row removal, extended height and Power placement are byte-identical to 87efb5ec. Including that previous correction, the proposed source overlay has four runtime differences against signed 2103458. POLISH-PRESERVATION.json records every path and before/after SHA-256; the three exact continuation diffs are adjacent. No behavioral Back/Trailer change was applied.

## Back/Trailer proposal, awaiting separate approval

INFO-CONTROL-REVIEW.md and the inert INFO-CONTROL-PROPOSAL.patch specify one target file: DialogVideoInfo.xml. Back10 conflicts with native OnGetArt; Trailer15 conflicts with native OnManageVideoExtras. Proposed IDs9011/9012 avoid these native reserved controls. Preserve PreviousMenu and the exact existing trailer bridge, conditional Stop, visibility, loading notifications and ownership references. Do not substitute native Trailer11, which could introduce a second playback path. Static XML/reference/reverse-byte checks pass; proposed behavioral execution is NOT RUN. The review contains the required focused regression plan. No native modification is proposed.

## Focused verification and retained failures

- PASS: 7 artwork cases, 5 Info preservation/geometry cases, 3 season-plot cases. Before-failure and after-pass logs are retained. Tests were selected in SCOPE.json before execution.
- PASS, limited Linux runtime evidence: actual upstream Kodi with the existing full skin, synthetic movies/shows/seasons/episodes, explicit responsive projection and existing Light/Dark variables. Final source-bound fixtures passed 38 checks each at 540x1260, 564x540 and 540x564; existing-scrollbar fixtures passed 47 each at 1260x540 and 564x540. These include selection, image captures, Info/Cast access where applicable and native Back restoration. They do not execute real providers, trailers or movie playback. FINAL-EVIDENCE-BINDING.json binds the three current XML hashes to these results.
- FAIL retained: action-row Up targets textbox98064, but native GUITextBox cannot receive focus. Two detail-focus fixtures fail. Independently focusing existing scrollbar98066 succeeds and moves the details group; this does not repair or waive the Up failure. Any action-routing correction requires a separately scoped behavioral proposal.
- WITHDRAWN: a final synopsis-height experiment passed host assertions but failed to establish the complete synopsis endpoint using both PageDown and supported Down input. Original max30% was restored byte-exactly, returning List XML to the already-tested SHA e2c7be2ccbf7d4b493bff260863d96c6dffc8daf3fe5ef99bf4271462c7cc449. PLOT-EXTENT logs and failed runtime results remain as historical evidence only, not verification of the final candidate.
- NOT RUN: actual Android 2103458 runtime, physical Fold, real provider rendering, all supported view modes, real touch/fold transitions or complete visual acceptance. Short-window title/cast truncation and full synopsis accessibility remain incomplete. Synthetic screenshots are not a pixel-equivalence or device-acceptance claim.

No unrelated shutdown or playback suite was run. Only disposable fixture processes were disposed of; no real profile/data was touched.

## Navigation, Downloads and Search

Infinity Movies/TV Shows already target full native titles URLs in the signed drawer. Alias replacement alone is not an evidenced fix. The current active skin, XML, modules and actual directory/history outcome require a current resolved-source export. Use existing Health Center Crash Center Export Infinity / active-skin details; do not add a diagnostic subsystem. A read-only review also found the legacy skin_upgrade.py handles only181-to182 and rejects unexpected243/256 parents before writes, so that code does not establish a current rollback cause. Existing Back/history behavior remains unchanged.

Downloads remains blocked at the existing native-filtering dependency. No shared source controls, sources, storage permissions or providers were modified. DOWNLOADS-BOUNDARY.md remains authoritative.

The bounded historical archive scan contains no request-specific INFINITY_SEARCH_STATE/aggregate_result_rejected/state_changed record and no kodi.log or other .log member. This absence cannot establish that rejection/crashes did not occur. Nixtoons' settings-history self-invalidation remains established but uncorrected; Crew still needs its own changed-component trace. Both state_changed acceptance cases remain FAIL. End-state equality cannot safely replace meaningful change detection without addressing temporary change/reversion. Source identity, cancellation, request ownership and settings/security checks remain unchanged.

The two historical signal11 summaries have no failing native stack or reliable failing-owner attribution in this archive. The crash is not claimed fixed or reproduced in2103458. Real30-search Android stress is NOT RUN. Existing reason-only Search tracing and supported current incident/Android evidence are the smallest next evidence steps; no new simulation was substituted for them.

## Preservation and release boundary

Source guard passes: only the three listed runtime files plus scoped review/test/evidence files differ from87efb5ec. Drawer, Search, providers, native engine, Preview, Cobra, playback, shutdown, signing infrastructure, real settings/data and recovery locks have no edits. The original signed archive remains the retained reference. There is no new APK, so a candidate APK-member comparison is NOT RUN rather than claimed PASS.

Before packaging: complete or explicitly disposition the open functional/visual requirements, obtain current runtime identity and real Search evidence, separately approve any Back/Trailer or Downloads behavioral change, then perform full signed-payload preservation, version, signer and forward-recovery gates. Nothing in this report authorizes packaging or marks the six-group correction complete.

The exact successful47-check probe is retained as media_probe.scrollbar-verified.py (SHA8c8140675e0e69aad0ae98df6a555e71012fd79bb348a3136e46c1071975949e). The current media_probe.py retains the additional failing endpoint assertion for investigation; it must not be mistaken for the earlier passing probe. No failed assertion was removed from its evidence.
