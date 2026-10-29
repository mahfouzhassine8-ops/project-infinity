# Consolidated P0 follow-up — 2103430

The complete 46-line player-button brief and 48-line approved launcher-icon brief were read before this implementation. This continues the existing Cobra branch and preserves the signed 2103429 improvements. The user-approved 2103427 lock remains the recovery baseline.

## Button correction

Signed 2103429 reproduces the physical report through production-view coordinate dispatch: Fullscreen → PiP, PiP → PiP, More → Fullscreen. The original Pro dispatcher uses hidden-preview indices `[0,1,2,3,5,4]`, but preview construction can move More before Pro activation. Original listeners remain attached to their views; the positional lookup reaches the wrong action.

The correction gives the original preview Fullscreen view a stable tag and replaces only the Pro dispatcher's positional lookup for Fullscreen/More with identity lookup. Existing native guards, original callbacks, menus, player/PiP paths, visible Pro order and non-Pro More-last remain intact. Dispatch does not reorder the retained row, so leaving Pro preserves non-Pro ordering.

Selected verification is actual production Hero/Action/HorizontalScrollView coordinate or remote key dispatch, with terminal fullscreen/menu/platform-PiP boundaries explicitly recorded as host spies. The signed29 negative case must retain its genuine route-assertion FAIL with no fixture errors; the next candidate must pass that same case, six focused interaction cases, and three adjacent retained-order/Pro-Sports checks. Exact selected names are in SCOPE.json and tests/SELECTION.json. Previous layout/logo/reflow evidence remains preserved; unrelated suites are not selected.

## Launcher resources

Only existing launcher IDs `0x7f080000` and `0x7f080001` change their day/night mappings. Five light legacy density images and two adaptive XML files are added. The modern light adaptive foreground uses the original monochrome alpha with black tint on white. Original colored and monochrome alpha channels are identical. Legacy variants use the same mask resampled to the original density and preserve the original tile alpha. Original dark images and adaptive XML bytes are unchanged and selected by new night configurations.

The resource table remains under its original MINIMAL_ANDROID_CONTRACT owner. Its narrowly reviewed resource exception preserves all shared classes/DEX, native libraries, manifest/launcher identities, settings schema, unrelated resource entries and protected lifecycle contract. It is not a shared-runtime or Infinity-feature change. The release gate re-derives the exact table/seven-resource transformation from pinned original inputs before any key read. Nine focused offline icon tests and 22 owner/release controls passed locally; CI and actual Android rendering remain required before delivery claims.

Normal Android resource selection is automatic. A launcher's bitmap cache and user-enabled monochrome palettes can control refresh/colors; Samsung Finder, suggestions and physical Fold behavior require user acceptance. No component toggling, alias, duplicate icon, startup hook or separately installed CobraTV change is introduced.

## Build and acceptance

One next combined original-key APK will contain both corrections. Its sole signer remains gated by exact tested owner bundles, anti-rollback, source/integrity checks, unchanged Infinity2103427 ZIP and resource-only shared-owner review. No experimental signed APK, shutdown change/test, user-device operation or accepted-lock promotion is authorized by this follow-up.

The selected final Android17 journey observes actual system day/night resource paths and launcher frames, then normal-UI Pro Fullscreen/More/PiP presses and return. Emulator observations cannot establish physical Fold acceptance. Final source/run/checksums and exact outcomes will be recorded after signing and verification.
