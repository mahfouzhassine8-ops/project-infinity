# Genuine Kodi ZIP installers — controlled testing, no acceptance/lock

Protected APK2103460 is not modified by the published ZIP bundle. Source and signatures are bound to bbe5197616ecbe1736ed706564a6d22a5f103be2, not later unbuilt Downloads code.

Download: https://github.com/mahfouzhassine8-ops/project-infinity/actions/runs/42183471037/artifacts/13485763569

Outer archive SHA256: dd04ad49d08006433e5c3d4c4b1b57dda2e0454cee25270f56fb6dcb35061ff1

Extract the outer GitHub artifact. It contains four complete Kodi addon installers, SHA256SUMS, the original public key, the original-key-signed ZIP envelope and build evidence. Do not install the outer artifact or a repository source overlay.

Before any testing, ensure the existing native Add-ons -> Install from zip file interface is reachable and retain both recovery ZIPs in an accessible location. Keep existing authentication and permission prompts. Do not clear data or bypass a failed check.

Install through that native interface:

1. script.infinity.commandcenter-0.3.5.61-2103460-corrective.zip
2. skin.infinity.diggz-1.0.5.260-2103460-corrective.zip

Command Center remains0.3.5.61. There is no new app, APK, launcher or player. The actual native module verifier accepts the original-key manifest for78 files/11 entries, and all948 skin protected-file hashes were checked. Kodi ZIP installation itself is not claimed to verify the detached outer envelope; that envelope is independently checked against the established original public key. The existing runtime module authentication is unchanged.

Recovery uses native Add-ons, not a Command Center script:

1. script.infinity.commandcenter-0.3.5.61-2103460-recovery.zip
2. skin.infinity.diggz-1.0.5.261-2103460-recovery.zip

Recovery Command Center content is exactly original2103460. Recovery skin functional contents are exactly original2103460; only3 necessary higher-generation integrity/version files differ. Actual original-Java verification passes after both simulated partial-update restorations, with userdata sentinel intact. The native GUI route is traced against exact460 DEX/native source. Android GUI copying, installation/recovery, permissions and service restart remain NOT RUN. If the native interface cannot be reached, stop and report rather than forcing installation or editing protected files.

## One coordinated physical check — record outcomes, not assumed passes

- Open the drawer: Power is last, all intended entries remain accessible and dimensions/scroll behavior match460.
- Infinity Movies opens the same existing Home movie menu including Continue Playing/Watchlist/Save For Later/Collection; Infinity TV opens the existing Next Episodes/Progress Shows/Continue Playing menu. Check Back/focus.
- Check no white curved LIVE artwork or touch-instruction bar in the previously affected browser/Home/widget contexts. Real art remains present; actual first/second tap and hold behavior remain unchanged.
- Inspect representative provider movie/show/season/episode directories and native lists in Light/Dark, cover/inner, portrait/landscape. Check poster proportions, synopsis, metadata, Cast rows, focus and long-press. This is physical visual acceptance, not established by XML tests.
- Info: Play existing movie; Back returns; Trailer uses existing bridge or actual available trailer; More uses installed ExtendedInfo or available native metadata; Cast displays supplied actors and native list actions. Record unavailable metadata truthfully.
- Search: use the currently working providers, preserve results and legitimate cancellation/configuration refusals. Record the exact existing INFINITY_SEARCH_STATE category/status/count records for Crew and Nixtoons when falsely rejected. Two settings/history acceptance cases remain known FAIL; this bundle does not promise their correction.
- Downloads in this published bundle removes the automatic Android Download-path probe but does not yet provide native folder isolation. Do not mark that requirement passed. Later scoped native integration must separately check genuine Add videos, manual folder creation/edit, retained folders across reopening/profile, ordinary Files preservation, permissions, playback and folder return.
- Repeated real Search stress target is30 completed requests, but stop at a crash and preserve its first failure evidence; no repeated forced crashes. Current native crash remains unresolved. One current460 crash requires faulting native thread stack/offsets, PID/time and loaded libkodi identity/mapping; historical456 summaries lack those. No credentials, settings values, query/media names or private raw logs should be published.
- Do not test unrelated shutdown behavior. No reset, uninstall, data clearing, provider modification, automatic install or release lock.

All physical results are NOT RUN here. Nine-correction completion is not claimed; Search and native Downloads remain explicitly open.
