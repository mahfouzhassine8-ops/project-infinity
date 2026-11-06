# Verified downloads

- testing_APK: https://github.com/mahfouzhassine8-ops/project-infinity/actions/runs/42204671979/artifacts/13495518701
- matched_ZIPs: https://github.com/mahfouzhassine8-ops/project-infinity/actions/runs/42202256097/artifacts/13495017909
- forward_recovery_APK: https://github.com/mahfouzhassine8-ops/project-infinity/actions/runs/42206367463/artifacts/13496986760

All three are GitHub artifact containers; extract the actual APK or inner Kodi addon ZIPs. These contain full signed installers, not source overlays.

````text
a24ffafd056db23aa9d433552e17d4362cc9dbc9dd568b086d84cabadae8c619  Infinity-2103462-Combined-Original-Signer.apk
c7057f7d2ae1d95e1ee514a1bc1717fb6a8de1cb2d6db1be44e81b2a795c0cab  Infinity-2103463-Combined-Original-Signer.apk
3f9887d18d82d8bdba066e449e7ce25dbe57a59742a7da6d491d72a86be9dea2  script.infinity.commandcenter-0.3.5.61-2103460-corrective.zip
02b4b8bf09ecbd56d9f68f4939e0f9216c01334c4e7ff60e677ab77509265f60  skin.infinity.diggz-1.0.5.262-2103460-corrective.zip
82bf1e352ea109ac263c5c677a483be72260c6d92af705c78ac90216d9f6792c  script.infinity.commandcenter-0.3.5.61-2103460-recovery.zip
6fbb87fe8f3a7f7391e31f1fe0ec0059ad92f6598e09487dedc79c9aa7dd10cf  skin.infinity.diggz-1.0.5.263-2103460-recovery.zip
````

Original certificate SHA256: d7adeb68e9341596a02bd3262b737a0f45fc6e771ed7e60285437e833b58c6d7. Both actual APKs verify v1/v2/v3 with unmodified SDK35.

2103462 changes3 payload members (typed manifest version, update metadata, libkodi);7619 existing payload members unchanged.2103463 changes only2 metadata members;7620 payload members including all47 native libraries unchanged. Both preserve all5 DEX files, all addons/skin/APK resources, Cobra and Preview. Three v1 signature members and APK signing blocks are regenerated. ZIP differences and every changed source are recorded in final-delivery-evidence and SOURCE-INVENTORY; all948 skin protected-file hashes pass.

# Infinity controlled testing updates — not an all-nine completion or acceptance

Signed2103460 remains immutable and recoverable. No application installation, uninstall, data clearing, provider change, baseline promotion or lock was performed. Current installed Fold version remains the user's confirmed2103460; delivery does not imply installation.

## Correct installation set

Use the exact original-key signed2103462 testing APK, Command Center corrective0.3.5.61 ZIP and skin corrective1.0.5.262 ZIP listed below. Keep the higher-version2103463 recovery APK and both recovery ZIPs accessible before beginning. The native changes are required for reliable library-menu root initialization and positive Downloads-folder membership. The APK is deliberately native-only; matching UI/script changes are delivered through the existing addon update path rather than silently overwriting a same-version installed module.

1. Manually update the existing app in place with2103462. Same package and permanent certificate; no uninstall/reset/downgrade.
2. Extract the outer authenticated quick-update artifact. Through existing native Add-ons -> Install from zip file, install the inner Command Center corrective ZIP, then skin1.0.5.262 corrective ZIP. The outer artifact is not a Kodi installer. Follow existing permission/trust prompts and normal addon/skin reload behavior; do not bypass a refusal. The original-key envelope and payload hashes were verified for delivery; the normal Kodi ZIP installer does not itself validate the detached outer envelope. Use the exact matching files and checksums.
3. Check existing module authentication, active Infinity skin and normal navigation. This is physical verification, not assumed from source. If a guard fails, stop and retain the first diagnostic; use the native addon interface for the original-signed recovery ZIPs where reachable.

For recovery, use the higher-version2103463 APK restoring exact functional2103460 and the Command Center recovery ZIP + skin1.0.5.263 recovery ZIP through native Add-ons. Recovery CC contents exactly match2103460; recovery skin differs only in3 authenticated integrity/version files. Do not reinstall a lower APK code, uninstall, clear data or bypass an unresolved save/checkpoint. Physical install-over, service restart and recovery remain NOT RUN here. If native UI is unavailable, stop and obtain supported device evidence; no unsafe forced-exit remedy is claimed. After463 recovery, any later APK retest needs a higher original-signed version.

## Nine requirements

1. Power is the drawer's absolute final action. Existing dimensions, entries and Power action are retained.
2. Infinity Movies uses the existing Home Movies menu, including its original collections. Actual XML -> Python dispatcher -> helper -> native parameters checked. Existing direct-entry guard now includes only the exact CC Home menu URL, avoiding retention of a child via return. No global history reset.
3. Infinity TV uses the existing Home TV menu through the same scoped native handling. Other Movies/TV routes are preserved.
4. White LIVE graphic suppressed at its exact existing resource reference in shared skin selectors and21 Home/widget textures; touch guide and its unused120px space removed. Actual native gestures are unchanged.
5. Downloads uses Kodi's real Files window. Initially only genuine Add videos; no Android Download-path probe. Folders explicitly added there persist by canonical native location, including ordinary source renames. Edits use exact selected source matching. All source definitions and ordinary Files are preserved; failed preference/source saves remain failures. Membership reuses existing per-profile skin settings, no parallel source DB or worker.
6. Native repeated-Search crash remains UNRESOLVED. Historical456 summaries contain no faulting stack establishing its cause in460 or the testing candidate. No native Search/player/checkpoint/settings-retirement change was made.
7. Search cache/UI invalidation corrected using at most one original owned request after discarding stale cache. Meaningful configuration/source/profile/cancel/ownership safeguards remain. Two required settings/history false-positive tests still FAIL. Crew's actual writer remains unconfirmed; no provider is classed as unable to search and no working results are intentionally suppressed or replaced.
8. Shared browser/Info presentation refinements, real artwork, released guide space and Cast proportions are included, using existing theme/view/layout resources. Complete Light/Dark/all-view/Fold rendered acceptance remains NOT RUN, not a pixel-match claim.
9. Info Cast control moved away from native control5 to9013; native list50 retained. Play/Back actions preserved; original Trailer/ExtendedInfo routes retained with actual available-trailer/native-metadata fallback where optional helpers are absent. Actual Android control interaction remains pending.

## Verification boundaries

PASS: actual final full ARM64 build;9411 mapped native inputs with9407 unchanged and exactly4 scoped files; all71211 original strong exports/dependencies/SONAME retained plus exactly2 reviewed source-dialog APIs. Actual C++ host boundaries44 checks; native direct-entry conditional8 cases; Python helper8 checks; actual drawer dispatch2 cases; unchanged UI-health functions accept prepared skin. Before-failure cases and superseded preparation evidence are retained.

PASS: Search6 focused cache cases and8 retained security/config/cancel/profile guards. FAIL:2 mandatory settings/history acceptance cases. NOT RUN: real Android30-search stress, actual decoding/control interactions, Fold/orientation/theme rendering, native ZIP installation/service restart and physical recovery. No unrelated shutdown suite ran.

PASS: original signed module verification78 files/11 entries, signed ZIP envelope and948 skin integrity hashes; full downloaded artifact sizes/SHA/CRC; exact APK-member and original-certificate verification. Existing original Java installer recovery audit uses final real signed ZIPs and disposable filesystem transports:6 cases pass or correctly refuse incomplete generations. It does not execute Android GUI copying.

## One coordinated Fold session

Check Power order; both library menus on initial and repeat entry after navigating into a child, Back and focus; two Downloads entry points, Add videos, manual folder selection, reopen/rename/edit, ordinary Files and playback return; no white graphic/guide; movie/show/season/episode metadata and artwork in relevant views; Info Play/Trailer/Cast/More/Back; existing first/second tap and hold; Light/Dark and cover/inner portrait/landscape. Follow the existing data-saving protections throughout.

Search stress target30 actual consecutive requests; stop at the first failure. Preserve the existing INFINITY_SEARCH_STATE category/status/count/timestamp records for Crew/Nixtoons, without settings values, credentials, query/media paths. A crash additionally needs the faulting native thread backtrace/offsets, PID/time and loaded libkodi identity/mapping bound to the tested package/engine. Health Center first; if it lacks that trace, a same-event Android bug report via legitimate authorized USB/Wireless debugging is required. No repeated upload of the historical archive or device-version confirmation is requested. Raw diagnostics remain private.

Search is the precise remaining blocker to all-nine completion. Device-only acceptance remains the user's. Nothing is automatically installed, accepted, promoted or locked.
