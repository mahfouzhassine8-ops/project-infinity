# Authorized touch source candidate

**Source-only candidate. No APK packaging, signing, installation, promotion or lock. Android/Fold execution NOT RUN. The master corrective release remains incomplete.**

Branch: `work/infinity-native-touch-from-2103451-20261105`, forked from55c993e3. [Applied delta and hashes](APPLIED-SOURCE-DELTA.json). The exact reviewed patch SHA256 remains `d6b61065f4158520e045985f6834327e80c163fed805cebd0c5b27c3179c1563`.

## Exact functional changes

- `xbmc/input/InputManager.cpp::OnEvent`: the existing Infinity Android pre-hover media path now admits the active native Favorites view and four original Home Favorites containers. Other pointer, key, mouse, modal, skin, screensaver and direct-button paths stay unchanged.
- `xbmc/guilib/GUIBaseContainer.cpp`: only `OnInfinityMediaTouch`, `OnInfinityFavouritesLongPress`, `OnInfinityOptionBLongPress`, the Resume hold branch of `OnInfinityUiTouch`, `OnMessage` and `Reset` change. Reuse the existing controller for first-tap selection, second-tap original activation and existing context actions. Preserve title/context ownership, transformed hit testing, source/identity guards and one-tap parent/Back/direct buttons. Disarm on real focus transfer/rebind/legacy holds while retaining same-control refocus. No new class member, header, virtual slot, tracker, worker, keymap or native API.

No changes beyond the reviewed two-file patch were made to native source. `SetFocus`, the existing controller implementation and all other native files remain byte-identical to frozen451. No playback, codecs, settings, checkpoint/shutdown, providers, Preview, Cobra or signing implementation changes.

## Frozen input and preservation

The initial full-source gate rejected the existing restored workspace because it still contained five earlier staged P0 changes. Both touch files were correct, but the whole tree was not frozen451. Kept that P0 workspace untouched. The isolated copy restored those five files to their separately hash-verified original451 preimages, then matched every one of the9,411 frozen source-map entries **before** applying the touch patch. This restoration is not a new shutdown change or a modification to any accepted engine.

After applying: exactly2 native files differ and9,409 protected native files match frozen451. The final source hashes are `23a07619efc01a728e572689e93c5010dd6f6e7354c229617b1b076ad62cbb25` for InputManager.cpp and `cb0e262c9cb58c56f6655955b6dc2999a2608523be9de582dabd82d3a0dfe0ae` for GUIBaseContainer.cpp.

[Source preservation](SOURCE-PRESERVATION.json) also verifies all65 parent master-correction source/evidence files unchanged from55c993e3. Repository differences outside the native source snapshot are only this repair's tests, fixtures, receipts, documentation and one new read-only compile-only workflow. No existing producer/signing workflow, lock, accepted registry, provider, app source, user file or baseline artifact was changed. This is source preservation, **not** an actual candidate APK-member comparison.

## Focused verification

| Check | Result and limit |
|---|---|
| Actual media-touch method and dispatcher, host |59 assertions:30 contract failures on pinned baseline,0 on candidate. [Before/after output](GESTURE-INTEGRATION-HOST.txt), [source/compiler binding](HOST-GESTURE-BINDING.json). Compiles the actual method/block with explicit mock Kodi/graphics/context boundaries; not Android gestures.|
| Negative/regression cases |Typed/untyped provider rows, seasons/episodes, native/Home Favorites, file/folder, transformed hit, changed selection, context owner, hold-release, parent Back, wrong view/window/skin, modal, disabled/hidden/gesture, pointer count, screensaver, failed focus and direct buttons included.|
| Existing controller/focus/legacy holds |Reuse the prior6 scope/helper checks and16 controller/focus/hold cases, bound to the exact same approved after-bytes. No unnecessary rerun.|
| Compile-only policy |6 distinct host cases PASS cumulatively;4 original checks plus new configuration-cutoff and prerequisite checks, with affected policy rechecked. [Original4](COMPILE-POLICY-HOST.txt), [new/affected3](COMPILE-RECIPE-AFTER.txt).|
| Compile-recipe counterexample |[Required cutoff test fails before](COMPILE-RECIPE-BEFORE.txt) and passes after the test-recipe correction. No native source change.|
| ARM64 actual translation units |**PASS**, [run41981486304](https://github.com/mahfouzhassine8-ops/project-infinity/actions/runs/41981486304), source6c0453ce2f87bacefc08712db927c859c88b9ede. Both real files compile with original NDK21.4.7075529 and actual native headers; ELF64/AArch64/REL object checks pass. [Compile receipt](CI-COMPILE-RESULT.json). No ARM64 engine link or application run.|
| Actual CI artifact and preservation |**PASS**: artifact13393888704,423,100bytes, SHA256b471d1648129f20f0e961bb2fd0e91cf24a29e8e1271e5fab1aa1ee130f31b37. Archive bytes downloaded through the supported connector download, CRC/SHA verified locally; full9411 map, exact two source pins, allowlisted original prerequisites and current configure recipe verified. Actual prerequisite build targets: crossguid, libandroidjni, spdlog. [Receipt](CI-ARTIFACT-VERIFIED.json).|
| Full native engine link |**NOT RUN** in the successful corrected recipe; asserted absent. No APK/signing/application output.|
| Android/Fold input, real rendering/context/focus |**NOT RUN**, no supported connected target. [Focused physical procedure](ANDROID-VERIFICATION.md); this does not authorize installing a candidate.|

The initial baseline host fixture reached an unsafe test-vector read after an expected missing activation. Its failed output is retained under INITIAL-*; only that test expectation was guarded. All30 baseline contract failures remain visible in the corrected comparison. Empty compile logs mean no compiler diagnostics, not an Android PASS. Two evidence-text files have only trailing whitespace normalized for repository hygiene; failure content is retained.

The first Actions run41979324652 is **CANCELLED**, not PASS. The inherited native-check precondition builds broad targets, including kodi; source review found this and the run was stopped. [Status](CI-FIRST-RUN.json) and [bounded log excerpt](CI-FIRST-RUN-EXCERPT.txt) are retained. The retry cuts before that precheck, validates the original CMake prerequisite closure and compiles only the two selected object commands. No APK/signing/application step existed in either workflow. Do not infer a final engine/object preservation result from the cancelled run.

The successful run's object SHA256 values are `2544153a938825f975d831faf9f877c916264cb9b4e422eda0bc1d665203a103` (InputManager,3,775,848bytes) and `27da00ba26d90fe3b76c5557d0eab4d57ba8d11ef3b6ea30d8883cb1e50b053c` (GUIBaseContainer,3,207,984bytes). These are relocatable compiler outputs, not a replacement libkodi.so or installable package. The retained artifact contains the verified receipts and full source map; it does not distribute an engine. Standard generated tools/depends configuration paths are enumerated in the compile receipt; all reviewed native inputs remain unchanged after compilation. No additional native source dependency was required.

The initial local artifact-check expectation incorrectly required all four allowable prerequisite targets. The actual recipe allows each only when present; this run's codemodel plan contains three. [Recorded expectation correction](ARTIFACT-CHECK-INITIAL.txt). Correcting that validation assumption changed no source or compiled bytes and required no repeated build.

## Independent remaining work

- **Search: two required acceptance tests still FAIL**, unchanged and not waived: identical settings rewrite and Nixtoons history self-invalidation. All existing safeguards and bounded reason trace remain. No settings observer, provider patch or stale-result exemption was added under this touch authorization. The Crew's precise device state delta still needs observation; direct-provider success establishes capability. The prior recording's bytes remain unavailable; no playback inspection is claimed.
- **Favorites:** read-only probe and prior11 host cases remain preserved. No connected device/authorized launch route means actual profile/native/UI counts and the missing-items cause remain UNCONFIRMED. No user data was read or changed.
- **Approved browser:** exact PNG bytes/file reference remain unavailable. Expected SHA2566786b5cadb7153bb0036a651dcfba889a58f2a5acd79a759a798302e2d70c0ad is retained. No substitute design, SHA verification or full-browser implementation is claimed. Previous authorized artwork, navigation, Library, global view and drawer changes stay preserved.

No further native-source dependency has been modified. Any additional required native file remains a separate authorization boundary. Settings-owner retirement, Scudo, Continue Playing, Home loading and all unrelated scopes remain untouched. No shutdown behavior suite or application test was run by this source candidate.
