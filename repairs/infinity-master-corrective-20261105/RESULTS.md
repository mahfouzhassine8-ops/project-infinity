# Master corrective source continuation

**Implementation is partial. Mandatory behavior checks still fail. No new APK/component was built, signed, installed, accepted or locked.** Actual installed and last physically accepted versions remain UNVERIFIED, as the user clarified. Frozen signed451 is the preservation reference; unaccepted453/454/455 are retained and not promoted.

Latest continuation: [Search All/direct-provider comparison, bounded diagnostics, Favorites probe and exact unapplied native touch request](CONTINUATION-RESULTS.md). Earlier results below remain preserved; the settings repair is still blocked and no complete implementation/release PASS is claimed.

## Implemented corrections

1. **Shared Search response/cache separation:** result decisions change only in `_query_signature` and `_provider_result`; the continuation adds a bounded rejection trace helper, preserving those decisions. A fresh owned answer survives unrelated Home/widget/Continue Playing updates. Original source/dependency/profile/settings stamps, route validation, token/worker/cancellation ownership and cache limits remain. Cache hits keep the full freshness check; a response is not transplanted into a different cache generation. Native busy/timeout/refusal is no longer relabelled by an unrelated freshness change. Settings-stamp/Nixtoons rejection is deliberately NOT called fixed.
2. **Direct navigation:** existing on-demand Library/navigation helper now checks the installed destination before dispatch. Movies/TV use existing Command Center inventory/source/route guards and verify the installed Umbrella router's exact existing `movieNavigator`/`tvNavigator` branch. Sports verifies the installed reviewed SportHD identity, enabled state, publisher, matching manifest version and entrypoint before opening its root. Main Movies/TV buttons invoke the existing helper directly; no intermediate Infinity menu, duplicate browser/search engine, provider execution/retry or playlistbrowser substitute. Original loading-notification pairs, native Favorites route and indexed Library destinations remain. Phone/provider compatibility and authenticated imports remain pending.
3. **Browse Files:** replace the folder picker with native Videos `files` navigation, which the preserved Kodi source maps to `sources://video/`. This avoids the shared `FileBrowser.xml` hard-coded SELECT ZIP presentation. Original folder history, source configuration, permissions, player and Back behavior remain native. Downloads' existing denied-access Browse option now reaches that browser too.
4. **Agreed drawer height:** exact height change1050/88% →1572/96%, with the original scroll grouplist, Power action/order and Explore retained. No pin/duplicate/footer. The user clarified **preserve rows; scroll in landscape**. Revised host geometry/ownership assertions pass for portrait fit and original landscape scrolling; physical measurements remain pending. No hidden shrinking or automatic scrolling was introduced.
5. **Movie List thumbnail binding:** exactly two normal/focused movie-row textures change from studio icon to the current item's poster. Original geometry, aspectratio=keep, themes, metadata, actions, other views and selection are untouched. Missing posters remain missing rather than using an unrelated directory icon. This is not the complete locked media-browser implementation.

Existing global media-view preference and prior UI source fixes are retained byte-for-byte in the reviewed source overlay except the explicitly listed changes. Their earlier passing host/fixture evidence is reused, not relabelled Android acceptance.

## Focused evidence

| Selection | Result and limits |
|---|---|
| New Search correction suite |15 PASS; includes explicit still-blocked settings/Nixtoons counterexamples. Unchanged native/provider/platform boundaries are synthetic. [Final output](results/SEARCH-CANDIDATE.txt).|
| Same Search expectations on signed451 source |Expected FAIL:10 assertion/subtest failures reproduce widget/progress invalidation, masked native failure and empty-result rejection. [Before evidence](results/SEARCH-BASELINE.txt).|
| Native browser/drawer/source preservation |7 PASS against final source. [Output](results/NAVIGATION-DRAWER-FINAL.txt).|
| Direct navigation |10 distinct cases PASS cumulatively: installed-source menu/pin checks, enabled/identity/version/entrypoint refusal, exact one-time target, unchanged loading pairs and canonical Android source-root translation. Public reference AST is parsed, never executed. [First9](results/DIRECT-NAVIGATION.txt), [canonical-root check and affected rechecks](results/SPORTS-CANONICAL-ROOT.txt).|
| Movie art binding |3 PASS cumulatively:2 initial checks plus corrected preservation assertion rerun. [Initial output](results/MEDIA-ART.txt), [final preservation check](results/ART-PRESERVATION.txt).|
| Required behavior before route correction |FAIL:5 methods with7 assertion/subtest failures. [Retained output](results/REQUIRED-BEHAVIOR.txt).|
| Required direct-route assertions after correction |2 PASS. [After output](results/REQUIRED-DIRECT-ROUTES-AFTER.txt).|
| Revised drawer requirement |1 PASS after explicit user clarification: portrait fit, original row sizes and landscape scrolling. [Output](results/DRAWER-CLARIFIED-ACCEPTANCE.txt). Previous all-orientation failure remains retained, superseded rather than falsely relabelled.|
| Remaining mandatory behavior failures |FAIL: settings timestamp and Nixtoons history. The unchanged failures were not rerun after unrelated routing/drawer edits.|
| Android, real network/provider, actual rendered Light/Dark, touch/Fold, installed compatibility and install/recovery |NOT RUN; no connected authorized target.|

There are35 distinct focused host checks for the implemented source paths, plus3 direct-route/drawer requirement assertions. These do not constitute a complete release PASS. Initial two test-assertion errors were retained: Power is inside its original nested row group, and an XML include's recursive serialized body includes the intentionally changed art. Correcting those test assumptions did not change application behavior. No unrelated shutdown suite was run.

## Root causes and integration

- Search incorrectly uses the whole cache-freshness fingerprint as current-response validity. Nixtoons writes ordinary history/timing to settings; Crew can conditionally write initialization/settings state. The source continuation solves the unrelated Home portion and failure masking; safe classification of settings mutations remains a gate. Crew's actual phone cause is unknown.
- Main Movies/TV targeted intermediate Command Center menus. Sports' previous helper accepted playlistbrowser, which is the wrong approved destination. The correction reuses existing helper, source verification and native window activation, with no account/settings writes.
- Browse Files reused a shared dialog whose actual frozen skin label is SELECT ZIP. The new route uses the native video browser and original player, leaving ZIP installation untouched.
- Existing movie List used studio art in its thumbnail slot. Two source bindings are corrected; no new palette, engine, view preference, control tracker, cache or persistent store is added.
- Native Favorites already uses the original current-profile/system collection through `CFavouritesService::GetAll`, including existing locks. No source proves the phone's `..`-only cause. No data rebuild/reset/lock bypass is performed.
- Native touch eligibility is narrower than the requested universal contract. Skin-only changes cannot fix the excluded windows/item types. The exact native dependency and original pairing limit are documented in [remaining gates](REMAINING-GATES.md).

## Preservation and delivery boundary

[BASELINE-COMPARISON.json](BASELINE-COMPARISON.json) binds the exact signed451 and453 APKs and enumerates their six differing members. Native451 isSHA151128c176b6094f28bb3fc716cc07c3985a9aa38f1fe41e1bb1424f0285a47e; native453 is a separate unaccepted candidate. No native replacement is inferred.

[PLANNED-MEMBERS.json](PLANNED-MEMBERS.json) lists all12 proposed source-overlay members with before/after hashes and the47 native/five DEX baseline hashes. This is a **source plan, not an actual candidate APK-member comparison**. Only four existing source files and this repair directory change from the prior packaging/source checkpoint; the Search source is added here as a reviewed overlay. No Cobra, Preview, chooser/Splash, provider package, data/settings, native/playback/shutdown, signing workflow, accepted registry or lock is edited. Mandatory module/skin generations and future signing metadata are not allocated; the source is not installable/authenticated as an update.

Remaining gates are explicit: [REMAINING-GATES.md](REMAINING-GATES.md). The approved PNG was reattached according to the user, but bytes/file reference are still not exposed here. No SHA/image inspection or exact-design acceptance is claimed. The full universal browser, complete touch contract, Favorites attribution and settings invalidation remain incomplete. The user's clarified landscape scrolling behavior is preserved. [Physical acceptance procedure](FOLD-ACCEPTANCE.md) is prepared for the eventual completed and verified candidate, not authorization to install this checkpoint.
