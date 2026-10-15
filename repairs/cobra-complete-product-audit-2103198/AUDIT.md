# Cobra 2103198 — Complete End-to-End Product Audit, Polish & Stability Pass

Parent: exact successful 2103197 surgical original-player-menu candidate at commit `b5fa21731a1662cc7206ac6dc45cb6d6682612cd`.

## Protected contracts

This pass treats the working 2103197 runtime as the product baseline. It must preserve playback behavior, provider/network selection, local timeshift ownership, buffering policy, TS parser flags, the exact Kodi native engine, resources/assets, signer, TV Sources route, five view modes, Fold Adaptive, original player menu, four-button player toolbar, theme runtime, PiP/background lifecycle, status-bar ownership, Health Center, diagnostics, and source-management behavior.

## Confirmed audit defects addressed

- 2103197 `ACCEPTANCE.json` incorrectly reported the removed TiviMate-style player hub and Recent Channels strip as enabled even though the source audit and runtime tests correctly proved they were absent.
- The 2103197 patch success message claimed those removed surfaces were kept.
- The source receipt carried stale parent-commit metadata that did not match its stated 2103194 parent.
- The packaged `DEVICE-TEST.md` was inherited from a much older lifecycle RC and referred to obsolete build/version details.
- The merged Android manifest contained two identical `RECEIVE_BOOT_COMPLETED` permission declarations, producing a manifest-merger warning.

2103198 canonicalizes the current parent/acceptance metadata, ships a current device checklist, and removes exactly one of the duplicate boot-permission declarations. No Cobra Java runtime method is changed by the 2103198 patch.

## Automated gates

The workflow reconstructs the exact historical stack through 2103197, applies only the 2103198 cleanup, rebuilds/signs the Android layer without rebuilding native Kodi, verifies the permanent signer, compares native/assets/resources byte-for-byte against 2103197, reruns every inherited Android/UI/playback/timeshift/network/source/Fold test, and adds product-level cross-surface gates for settings, source manager, player menu, toolbar, Health Center, background mode, Fold Adaptive, refresh policy, status-bar restoration, and playback guard invariants.

Physical Fold/GPU/provider/hardware-decoder acceptance remains a separate device gate and is never inferred from Robolectric or source checks.
