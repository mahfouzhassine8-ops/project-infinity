# Remaining implementation and release gates

## Settings activity versus meaningful changes

The implemented Search separation fixes unrelated Home/progress invalidation for a fresh owned response, and preserves the original native failure status. Cache hits retain the original full freshness guard. Settings/source stamps remain strict.

The timestamp and Nixtoons requirements are **not fixed**. An endpoint-content-only exemption cannot distinguish a harmless rewrite from a configuration change that returns to its original value while the provider is running. The focused counterexample writes a temporary configuration and restores the original bytes; existing stamps reject it. Dropping the stamps or ignoring known fields without a trustworthy mutation history would accept that counterexample. The same ambiguity applies when bookkeeping fields also change. No settings values were read from the phone.

Next smallest action: capture the actual failing request's installed provider identity, original native outcome, cache/fresh status and changed-component/field category, then prove a request-local configuration-mutation contract before exempting bookkeeping. The supplied standalone probe can collect sampled identity/deltas but cannot prove writer ownership or complete mutation history. No connected authorized launch route is exposed. Native settings mutation/ownership modifications would cross the preserved engine boundary and require a separately reviewed exception; do not reopen blocked settings-retirement work. Crew's specific device failure remains unverified and is not assumed to be Nixtoons' history path.

## Direct destinations

Reference publisher source confirms Umbrella's `movieNavigator → Navigator.movies` and `tvNavigator → Navigator.tvshows` routes. It also identifies the current public SportHD reference as `plugin.video.sporthdme`, version0.1.92, `default.py`. These are **public reference inputs, not the phone's installed IDs/versions/source hashes**.

The source helper now verifies the installed destination before dispatch: existing Command Center inventory/source/route checks plus an exact AST check of Umbrella's installed menu branch; for SportHD, existing read-only add-on details and bounded source reads verify enabled identity, publisher, matching manifest version and `default.py` before opening its provider-owned root. Missing/changed providers fail closed, with no alternative provider. Main Movies/TV call the existing helper directly; existing loading notification pairs remain. Playlistbrowser substitution is removed. Nine focused host cases pass, including native route-pin verification, refusal/error paths and exact one-time dispatch. Phone compatibility, authenticated cross-owner imports and actual loading/focus/return remain unverified. No real provider was executed here.

Required next evidence: run those guarded paths against the phone's actual installed Umbrella and SportHD. A different/older SportHD identity is not silently substituted; it needs verified source evidence. Native Favorites already targets `favouritesbrowser`, independently of Library entries, and remains unchanged.

## Favorites

The actual native route is `WINDOW_FAVOURITES → MyFavourites.xml`; its Update uses `favourites://`. `CFavouritesDirectory::GetDirectory` calls `CFavouritesService::GetAll`. The service reads system and current-profile `favourites.xml`; it also respects existing master/media-source locks. The skin's registered/default list ID is50 and uses the native populated container with no separate content override. These paths do not establish why the phone shows only `..`.

No existing user Favorites collection, active profile, load result, lock state or returned native count is available here. Do not infer data loss, rebuild the collection, disable locks or migrate it. Next observation is the current profile identity (private), native count/load status and actual selected window; retain all data unchanged. No Favorites data repair is claimed.

## Locked media-browser image

The user confirms reattachment of the exact locked PNG. This executor still exposes no attachment bytes or file ID; the workspace/repository and accessible Pages do not contain that image. The design branch contains the SHA/specification only. Therefore SHA verification, direct visual inspection and exact locked-design implementation remain blocked. No substitute image was generated or treated as the approved reference.

The independent movie List thumbnail-binding defect has been corrected without changing layout: two slots used studio logos instead of the item's poster. All other metadata/theme/action XML is preserved. This narrow fix is **not** the complete browser design, giant-directory-art correction, all-view visual acceptance or a claim of pixel fidelity.

## Touch contract and protected native input

Existing Android `CInputManager::OnEvent` dispatches media touch before synthetic hover. `CGUIBaseContainer::OnInfinityMediaTouch` handles the active Videos container and designated Home surfaces, but requires a video tag with movie/tvshow/season/episode type and an eligible provider/library/controller path. It excludes ordinary untyped provider rows, many file/folder entries and the native Favorites window. The native Favorites path has a hold handler but is not admitted to the generic first/second-tap media path. Existing typed-media paths also retain a 120ms–5s tap pairing interval. This does not establish the requested universal contract.

Skin XML alone cannot extend the native dispatcher eligibility or replace that pairing rule. Smallest proposed native exception: the Infinity-only Android branches of `xbmc/input/InputManager.cpp::OnEvent` and `xbmc/guilib/GUIBaseContainer.cpp::OnInfinityMediaTouch`, reusing the existing `InfinityTouchPress`, transformed hit testing, native item action/context dispatch and row identity. Include the native Favorites active view and applicable real folder/media rows; retain one-tap modal/direct buttons, Back, original context owners and all Kodi playback/shutdown code. No new tracker, worker or parallel gesture engine. Those production native files are unchanged; no native repair, compilation or Android touch PASS is claimed. A separate explicit protected-engine/source allowlist is needed before this exception is integrated.

## Drawer geometry

The user explicitly resolved the short-window requirement: **preserve rows; scroll in landscape**. Initial Power visibility is a portrait requirement; landscape uses original scrolling. No row-density change, pinning, reordering or automatic scroll is introduced.

The original scrolling grouplist has top132, bottom18 and gap6. Power's original row spans1336–1416 relative to that list; Explore follows at1422. At panel height1572, the usable list is1422 and the agreed placement fits exactly. At smaller percent-constrained heights it does not.

The signed451 skin declares1080×2400 and has **no** native-responsive marker. Its preserved Android `CSkinInfo::GetNativeWindowResolution` adapts the original logical area to the usable window's aspect, quantizing both axes to8. A landscape example can therefore have a logical height near1056; its96%-height drawer exposes only about864 list units. This is a measured source constraint using synthetic window dimensions, not a physical Fold measurement. The revised focused acceptance assertion passes for portrait fit and original landscape scroll ownership. Actual viewport/insets and touch/scroll measurements on the Fold remain NOT RUN. The earlier all-orientation initial-fit failure is retained and superseded by the user's clarification, not reclassified as a previous PASS.

## Release boundary

Actual installed version and last physical acceptance remain UNVERIFIED per the user's clarification. Frozen signed451 is the preservation reference. Signed453 differs in the native engine plus version/signing metadata; it is not silently accepted or integrated. Existing454/455 files are retained as unaccepted UI/recovery artifacts.

No compatible connected Android target, `adb` executable or authorized Kodi control route is exposed. Android, provider-network, rendered Light/Dark, gesture, Fold and install/recovery tests are NOT RUN. No known-broken emulator was restarted. No APK, component ZIP, new authenticated module generation or version reservation was produced. Before packaging: complete the outstanding source requirements, confirm the installed package/certificate/version and accepted base, finalize the full member allowlist, verify the candidate, and prepare an authenticated higher-version forward recovery using the unchanged original signer. Do not reinstall, clear data, downgrade, force-kill, promote or lock anything.
