# Cobra 2103165 — Inner-display insets, PiP launcher return, player-contract audit

## Protected base

This candidate starts **forward from the locked/passed Cobra 2103164 Playback Stability baseline**:

- branch/tag: `locked-cobra-2103164-playback-stability-passed`
- commit: `d9819b9823ff281f874daaa2bf91fdac1613aeb1`
- successful Actions run: `35338917341`

The locked branch is not edited or moved. Candidate 14 remains protected as well. Kodi C/C++, renderer/native libraries, skin/assets/resources and signer are outside this repair.

## Reported device symptoms

1. On the Fold inner display, Cobra browsing/TV Grid can remain in a globally fullscreen window even though there is no reason to hide Android's status bar. After Fold/PiP/window transitions this can leave stale inset/layout state and visually waste the top of the display.
2. After entering Android PiP and later returning by launching Infinity, the old fullscreen video surface can be restored by itself instead of returning to Cobra's general browsing view.
3. The video player must remain consistent with the player UI already approved/locked; this repair must not redesign transport controls, spacing, drawer, lock behavior, progress/program presentation, aspect controls, or Multi-View entry.

## 2103165 corrections

### Surface-scoped system-bar ownership

Cobra is no longer globally `FLAG_FULLSCREEN` from Activity creation. General Cobra browsing/preview surfaces explicitly show the Android status bar and request fresh window insets/layout. Fullscreen video and Multi-View alone hide the status bar. The policy is re-applied on resume, focus restoration, configuration/Fold changes, PiP changes, player open/close and Multi-View open/close.

Only the status bar is controlled here. Navigation-bar policy is not redesigned.

### PiP return routing

PiP lifecycle/playback ownership remains the locked 2103164 implementation. The new routing distinction is navigation-only:

- **Native PiP expansion/tap:** no launcher intent -> keep the approved fullscreen player/session.
- **Launching Infinity / explicit Cobra browse return while PiP/fullscreen exists:** consume that navigation intent and return to Cobra browsing rather than resurrecting an orphaned fullscreen surface.

This does not create a second player and does not move fullscreen playback into the mini-player background-audio path.

### Player consistency guard

Before any edit, the patch hashes and protects these current locked player methods:

- `cobraBuildPlayerChrome`
- `showCobraPlayerDrawer`
- `showPlayerSettingsDrawer`
- `showTrackChooser`
- `lockCobraPlayer`
- `toggleCobraPlayerPlayPause`
- `cobraPreviewPanel`

The patch also requires the approved player contract markers to still exist: refined player chrome, Previous/Next, Lock controls, central play/pause tag, program progress, Channels, Display, Multi-View, More, and the locked 2103164 More/Display anchor tags. Those protected methods must remain byte-identical. `openPlayerOverlay` may gain only the system-bar ownership hook; its previous body is otherwise normalized and compared exactly.

## Acceptance gates

CI reconstructs the exact source chain, applies the locked 2103164 Playback Stability recipe, then applies only this 2103165 delta. It packages/signs the Android shell without rebuilding Kodi native code.

Before publishing the APK, CI must:

- verify the exact locked 2103164 APK from run 35338917341;
- preserve permanent signer and version identity;
- compare every protected `lib/`, `assets/`, `res/` entry and `resources.arsc` against locked 2103164 and Candidate 14;
- rerun all 46 inherited UI/Health/theme tests;
- rerun the 16 locked Candidate 14 tests;
- rerun all 26 locked 2103164 playback-stability tests;
- pass 6 new 2103165 status-bar/PiP-return tests;
- prove all protected player methods remained unchanged.

Automated success does not claim physical Samsung Fold acceptance. The final device check is the user's real inner display: browse status bar/insets, fullscreen player, PiP via Home, PiP expansion, app-icon return from PiP, fold/unfold, More/Display sheets, and player controls.
