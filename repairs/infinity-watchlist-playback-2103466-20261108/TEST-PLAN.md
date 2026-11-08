# Focused Phase B verification plan — NOT RUN

Phase A runs no implementation, host behavioral or application tests. The following
cases are planned, not authorized/executed by this document. Record exact selected
cases before execution under the repository focused-testing policy. Reuse valid
baseline evidence instead of a full regression sweep.

| Case | Required evidence and expected result |
| --- | --- |
| Locked saving/navigation | Preserve Search→long press→Infinity Trakt→Add/Remove Watchlist→Infinity Movies/TV Watchlist; same rows, routes and folders. Saving/listing/selecting/cancelling makes no `items`/`watched` entry or player occurrence. |
| Failed/nonstarted launch | Resolver cancel/error, successful resolution without AV start and unrelated playback cannot admit new Watchlist proof or create history. |
| Movie partial/resume | Actual AV start followed by the existing partial threshold produces one existing-store row. Watchlist direct click, popup Resume, Information Play and recovery read the same current offset and original saved destination; saved snapshot/membership unchanged. |
| Exact episode | Play a saved show→season→episode and a directly saved episode. Preserve reviewed show IDs and exact S/E. Save S1E1 and give S1E5 newer progress: S1E1 must never resume S1E5. |
| Threshold boundaries | Preserve duration120s, position30s AND1%,95%/ended completion and existing-row rewind semantics. The120s duration condition applies to new partial entries, not completion: preserve baseline ended/95% completion even for short content and natural end with unknown duration. Never-started content creates no history. Do not add a duration gate to completion or invent a watched percentage. |
| Player lifecycle events | Real start, periodic sample, seek, pause/resume, stop, end/error; repeat callbacks and stop/end order. One occurrence records/completes once, no late resurrection; released clock preserves last sample. |
| Replay | A completed movie/episode launches at zero; real new AV start owns a new occurrence; later qualified progress/completion remains valid without duplicate saved entries. |
| Provenance isolation | Ordinary Movies/TV launch of the very same saved title, another title, stale receipt, back/cancel, cached directory, delayed result, changed profile/experience and reused stream URL do not acquire the new saved-flow proof. Existing baseline recording still works. |
| Identity conflicts | Similar names/remakes, different namespaces, conflicting secondary IDs, multiple seasons, missing proof, changed provider emitter or episode-scoped-only ID never merge or become verified parent IDs by guess. |
| Resume visibility | Hidden/completed state wins over older matching aliases. Render a saved row, change its progress, then directly select it: the reviewed direct-click dispatch must use the current offset, not the rendered snapshot. Popup-only revalidation is insufficient. Preserve exact episode selection. Reject negative/nonfinite/invalid offsets. |
| Progress Shows | Only actual admitted episode playback supplies proven series grouping. Show/season browsing and Watchlist saving create no episode progress. Existing regular projection stays unchanged. |
| Next Episodes | Use verified catalogue for next episode and season transition; final episode has no invented next. Specials retain existing grouping rules. Missing/filtered/incomplete/unavailable catalogue withholds successor without blocking playback. This fallback is not full next-up acceptance. |
| Completion/manual state | Existing watched/unwatched actions, hidden markers, occurrence completion, already watched replay and pending library sync retain semantics. Provider-only entries do not acquire fake Kodi DB IDs or new provider/account writes. |
| Persistence reload | Inspect the existing store after real partial/completed playback and reload it in a fresh service/application process. Correct identity/offset/next proof and unchanged Watchlist survive. No new database, migration or owner data collection. |
| Preservation | Compare all changed files to exact466 source hashes; every other APK member remains identical except required version/module-signature/package metadata. Cobra/skin/DEX/Search/providers/authentication/player/lifecycle components remain protected. |
| ARM64 if native scope authorized | Compile the real changed Android ARM64 observation path, fully link the native engine and verify expected symbols/dependencies and unchanged unrelated native source. Execute exact selected navigation/AV-start cases on the signed successor; a host or link PASS is not device acceptance. |
| Signing/install/recovery | After authorized implementation passes: current registry, original signer, complete module manifest authentication, in-place update and forward recovery preserving disposable profile sentinel. No uninstall/data clear/downgrade/key substitute. |

Host cases should exercise actual existing production functions with controlled
player/receipt/catalogue boundaries, including negative admission and duplicate
completion. Do not test a mirror implementation. Use Android only for the missing
real AV-start/event-order, selected-item lineage, resume-offset, persistence and
installation boundaries; do not repeat unrelated Search suites or playback matrix.

The owner explicitly requested application-restart persistence for this feature.
Select that narrow reload check after Phase B authorization. It does not authorize
Normal Close, Essential-First or any shutdown/durability/lifecycle test, nor changes
to checkpoint/shutdown code. No shutdown workflow dependency or old broad main
runner is allowed.

Final owner Fold journey, once engineering gates pass: save one never-played title
(no progress); play/partially stop/resume the exact saved TV episode; complete it
and verify the catalogue-proven next; play/resume a saved movie; verify returning
to Watchlist, regular Movies/TV and existing Search. Preservation evidence covers
Cobra and unrelated components. Keep this one coherent acceptance test; no blind
reinstall, provider cache purge or account/settings reset.
