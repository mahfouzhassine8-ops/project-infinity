# COBRA — next development from locked combined 2103427

**User decision:** Infinity 2103427 is perfect and approved/locked; next focus is Cobra.
**Repository:** mahfouzhassine8-ops/project-infinity
**Cobra engineering branch:** work/cobra-only-from-2103427-20261028
**Exact accepted signed-source starting commit:** 782242090483982c39a78f9c4da932a4751bdafc
**Do-not-move approved lock:** lock/infinity-cobra-2103427-user-approved-20261028
**Signed reference:** combined APK versionCode 2103427, original key, GitHub Actions 40769526963, APK SHA256 cd0c8ab5c77067e508baea0ad7d5207b3d6c73775b86387d4099a67cfe4215ca.
**Cobra component shipped in that APK:** bundled-2103420.isolation.1.fold-reflow.2, last-updated label 2103423.
**Infinity component accepted in that APK:** 2103420.isolation.1.performance.2, Command Center 0.3.5.51, Infinity Skin 1.0.5.248.
**Physical reference device:** Samsung Galaxy Fold 8 Ultra / Android 17, with cover/inner and supported rotations and window sizes.

## Non-negotiable boundary

- **Only Cobra is in scope for any subsequently authorized implementation. Infinity is LOCKED, FROZEN, and OUT OF SCOPE.** No Infinity source, modules, Search, Home, Trakt rail separation, provider data, Kodi profiles, watched/progress, Continue, performance, skin, playback, or any already accepted fixes may be changed.
- Choose Your Experience remains visually and behaviorally frozen; version metadata may only change as required by a separately authorized, correctly signed future combined release. No shared Android contract/native ABI/PiP coordinator/shutdown writer, signature, package identity or migration changes without specific new authorization and demonstrated owner safety.
- ONE Android app, one icon, one chooser, one original signing certificate; future Cobra changes use owner-isolated component builds and the existing fail-closed combined release gate. Preserve the original 2103427 APK and source lock. No uninstall, data wipe, cache clearing, downgrade, database migration or repeated diagnostic APK installation.
- Protected Essential-First Close/persistence: no change, and no shutdown test added to feature verification or signing.

## Established Cobra work — inspect current shipped state, DO NOT blindly replay historical patches

1. **Fold/window reflow has a signed prior correction.** Cobra's 2103423 component already includes a measured-window observer for single player and all supported Multi-View counts 2, 3 and 4. Its exact source is in repairs/cobra-all-layout-fold-reflow-20261027 and delivery in repairs/dual-experience-isolation-2103420/DELIVERY.md. Host geometry, layout wiring and original-key signing passed. Physical stream/surface, PiP, audio/fold acceptance must not be inferred from host fixtures. Do not reimplement the original 3-pane defect without evidence it persists in shipped 2103427.
2. **Historical six Cobra-only corrections:** repairs/cobra-clean-restart/DELIVERY-2103372.md records (a) preserving explicit mute on fullscreen Channels tuning only, (b) mini/fullscreen PiP controls and same-player return, (c) Pro-only horizontal fullscreen control strip without arrows/instructions, (d) Pro Sports Stats and exact menu order, (e) Pro Sports broadcast choice overlay with four visible rows and vertical scrolling, and (f) Pro header theme/icon contrast. These were signed/tested historically, but their presence in this newer *combined* Cobra owner payload must be checked member-by-member; do not assume a prior standalone APK became the current component.
3. **Other preserved Cobra contracts:** Pro Sports is Pro-only; no Mobile Sports tab or retired COBRA SPORTS dashboard; keep existing Mobile/Compact/Cards/TV Grid behaviors, channel groups, favorites/recents, live playback, Fit/Fill, 1–4 supported tiles, selection, media audio/stream ID/timeshift/buffering, fullscreen, mini-player, supported PiP, controls, Ambient Off/Subtle/Immersive, Night Cinema amber and no video recoloring.

## Initial engineering scope — audit first, no speculative changes

- Inventory *actual signed 2103427 COBRA.zip and APK* and compare to its exact approved owner-vector; identify every currently shipped Cobra-owned player, Pro UI, Sports and layout entry point. Confirm whether the historical six changes are currently present, partially present or superseded. Identify any genuine gaps using current production code and previously observed user device behavior; do not classify an unverified interaction as a confirmed regression.
- Evaluate currently grounded Cobra priorities: (A) full-window cover/inner/fold/rotation/split/PiP reflow and stable stream/audio identities across all supported tile counts, (B) mini-player/fullscreen PiP and channel-selection mute/audio continuity, (C) Pro Sports Stats/menus/4-row channels/header theme, and (D) loading, responsiveness, caching and smooth frame pacing where measured. Preserve every already-passing behavior and the exact approved UI.
- Any future fix must be specifically mapped to Cobra-owned production members and a reproduced issue. Record before/after evidence, selected focused non-shutdown tests, unchanged Infinity/chooser/shared members, and any missing physical validation. Do not use a generic "optimize everything" rewrite, arbitrary native allocator patch, unrelated timeout increases, or a new global worker/caching system.
- User has not yet described a specific *new* Cobra defect in this turn. This setup document does **not** authorize automatically changing runtime code, launching a signed new version or claiming all Cobra repairs complete. Once the requested Cobra correction is identified, implement it on this existing branch only, using a tightly scoped test and then one combined original-key signed install-over candidate if authorized.

## Release and acceptance

Maintain the lock at 2103427 untouched. No modifications to its source ref. Future next app version must exceed 2103427 and retain the accepted Infinity component byte-for-byte, existing signer, Cobra/chooser ownership checks and data compatibility. Physical Fold verification is the user's final acceptance gate, not a CI claim.
