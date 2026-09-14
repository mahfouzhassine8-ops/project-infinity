# Infinity two-experience APK — Live shell contract

Status: implementation branch / device acceptance required.

## Product boundary

One Android package exposes two intentionally separate user experiences:

1. **Infinity** — the accepted Kodi/Infinity shell for Movies, Shows, Add-ons and existing Kodi functionality. Its accepted player and skin contracts are protected.
2. **Infinity Live** — an isolated Live-TV-first experience backed by the Infinity-owned Media3/ExoPlayer runtime.

Infinity remains the default launch experience. Infinity Live is entered explicitly through a Switch Experience / Live TV handoff and provides a deterministic Return to Infinity action. No mandatory chooser is shown on normal app launch.

## Infinity Live feature target

The supplied CobraTV build is a behavior/UX reference only. No Cobra code, assets, package identity, credentials, or proprietary implementation may be copied or bundled. Infinity Live independently implements the concepts selected for the product:

- Live-first channel browsing
- full-screen channel playback
- guide / EPG
- Favorites
- M3U/M3U8 + XMLTV source management
- supported user-authorized stream-service/provider login flows
- previous / next channel
- touch-first and D-pad/remote controls
- MultiView with independent ExoPlayer video surfaces
- explicit audio-owner selection in MultiView
- responsive Fold / cover / inner-screen layouts
- clean Return to Infinity handoff

## Runtime ownership

Normal Live playback and MultiView belong to the Infinity Live Media3 runtime. Movies/Shows remain on Kodi CApplicationPlayer. A Live session owns its ExoPlayer surface, audio focus and navigation state until the user exits Live; incidental Activity pause/configuration handoffs must not silently tear it down. Destroy/explicit exit must release all players, surfaces and audio focus and clear active-session state.

## Isolation acceptance gates

A candidate is not accepted merely because Media3 libraries exist in the APK. Device acceptance must demonstrate:

- selecting an ordinary Live channel creates an ExoPlayer-backed video surface;
- picture and audio remain attached to the visible Infinity Live experience;
- reopening Live never produces a stale "already open" state after a legitimate exit;
- touch chrome exposes Guide, Favorite, channel navigation, MultiView and Return to Infinity;
- MultiView renders all requested feeds and changes the audible tile without recreating Infinity;
- returning to Infinity releases Live resources and restores Infinity focus/navigation;
- Movies/Shows still use the protected Kodi/Infinity player path.

This branch must remain additive and reversible until all gates pass on device.
