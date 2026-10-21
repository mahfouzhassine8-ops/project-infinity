# Infinity 2103394 — fourth Fold Option B failure and ZIP/runtime shadowing investigation

**Status: confirmed source mismatch + unverified installed runtime. No correction built or Fold acceptance.**

**Baseline:** signed 2103394 source commit `4e4ca79f134ce9b0ac22c66cd13e246a11207de8`, GitHub Action `39539171911`, published release `infinity-2103394-binaries-39539171911`. Preserve it unchanged. Do not touch Cobra, providers, Rails or Essential-First durability. Do not uninstall or clear the Fold's data.

## Physical findings / updated user requirements
- Fourth consecutive physical Fold failure: long-press on the top Umbrella Latest Releases movie and TV posters does not produce approved Option B. Host/CI passes are not device passes.
- **Option B applies ONLY to Normal (8101 movies/8102 TV) and Compact (8801 movies/8802 TV).** The user explicitly excluded Cinema and Two-Pane.
- Separate Compact Home screenshot: top headings overlap; record as an independent visual regression.
- User reports previous behavior where an APK appeared to repair an issue, but updating externally installed component ZIPs made the repair disappear. Diagnose active runtime identity before recommending additional ZIP installations.

## Confirmed cross-component source defect
- `repairs/fold-corrective-2103394/input94.py` and inherited native `OnInfinityOptionBLongPress` dispatch include all eight 810x/860x/870x/880x variants.
- The packaged `script.infinity.uirepair/home_option_b.py` is derived from `repairs/2103390-bugfixes/group3/home_option_b.py` by `ui94.home_option_b()`. This changes index handling and adds traces, **but does not update** `CONTROLS = {8101: 'movies', 8102: 'tvshows'}` nor the `read_native_hold()` argument allowlist `('8101','8102')`. It therefore silently rejects Compact IDs 8801 and 8802 even if native hit/proof succeeds. Correct exact four-ID agreement in both layers; exclude the Cinema/Two-Pane IDs, preserve full proof and media-path validation.
- This does **not** establish the root cause in Normal mode. Real native/gesture stage and Python capture/modal evidence is mandatory. Current traces are sparse and do not identify every rejection.
- The previous normal-mode screenshot confirms UI focus/content, not the complete native-to-Python command or popup lifecycle.

## Signed APK and component ZIP integrity
- `repairs/fold-corrective-2103394/delivery94.py` creates each individual addon ZIP from files inside the **signed final APK** `assets/addons/` and asserts byte equality, non-corruption and matching entry count. The GitHub compile/package/publish workflow succeeded.
- This **establishes release ZIP/APK byte coherence**, not successful install-over nor active runtime identity.
- The 2103394 delivery receipt explicitly says `actual_install_over_tested: false` and `physical_fold_verified: false`. Do not call a ZIP/runtime conflict either proven or excluded.
- Kodi can load add-ons from a user's persisted installation under `special://home/addons` rather than the APK-bundled `special://xbmc/addons`. Cache, retained addon folders, partial updates and mismatched source pins may therefore matter.
- The 2103394 native classifier matches a **complete signed 16-file Command Center source contract**; actual older/different on-disk files are deliberately rejected. Never bypass this integrity protection to mask a mismatch.
- The supplied **pre-2103394** diagnostic `Infinity-Diagnostics-20261020-195112.zip` contains `integration/installed-code.json` recording 2103393 CC 0.3.5.23, skin 1.0.5.230, Health 2.5.20, but does **not** include UI Repair, Watched Bridge or Rails resolved entry hashes. It cannot establish the active 2103394 install or exclude ZIP drift.

## Required runtime / controlled install verification
1. Without uninstalling, resetting profiles or clearing data, collect current installed Kodi IDs/versions, the **actually resolved add-on directory**, and SHA-256 of the active relevant source files (not merely addon.xml) for Command Center 0.3.5.24, UI Repair 0.1.6, Watched Bridge 1.0.5, Skin 1.0.5.231, Health Center 2.5.21, Rails 0.2.7 and the compatibility service. Protect private paths/tokens.
2. Compare each active file to the **signed 2103394 APK member**, the corresponding ZIP entry, `CONTROLLER-PREIMAGES.json` (same CC24 contract in UI Repair and Watched Bridge), native CC24 classifier, and the skin protected manifest. Report `MATCH`, `STALE`, `MISSING`, `DUPLICATE`, `UNKNOWN` with exact source/hash/owner, **never** green without verification.
3. Instrument stage-by-stage bounded Option B touch tracing for Normal and Compact, Movies and TV: touch/gesture, container, hit/select, path/type, focus, native proof/posted, Python entry/proof/capture, index/label identity, `WindowXMLDialog` creation/onInit/shown, user cancel/choice. Retain no URLs/titles in logs and never log secret paths.
4. If safe and with explicit user cooperation, compare behavior **after install-over APK before ZIP**, **after each matching ZIP** and **after Close/reopen**. Avoid unnecessary reinstallation if the current state already shows a mismatch; backup diagnostics and correct proven cause first.
5. Negative controls: mixed/older UI Repair, Watch Bridge and CC source pins must fail closed with an actionable diagnostic, not a silent success. Positive control: actual APK → exact matching ZIP sequence preserves behavior across Close/reopen.
6. Repair Compact header overlap separately, with a narrowly scoped Home layout change; preserve Normal header, content, scrolling and unrelated themes.
7. Run full existing native/source/Android gates, permanently sign new install-over version, publish individual matching ZIPs. **Require actual Fold acceptance** of Option B Normal and Compact, Movies and TV; no final LOCK from host tests.

**No direct modification of the signed 2103394 APK or baseline has been made by this note.**
