# Infinity / Cobra 2103269 — responsive window audit and repair candidate

**AUTOMATED TEST CANDIDATE — PASS. NOT DEVICE-PASSED. NOT LOCKED.**

The requested full physical end-to-end audit remains open: no physical Samsung Fold, native Kodi renderer or update-over-install execution was available. In particular, native Infinity .172 Home/widgets/library screens have NOT received a rendered product pass.

## Starting points and preservation

Locked 2103267 remains unchanged at `292351efa4e0840c1f01b343a81e62b8905ba3f0`. Its APK SHA-256 is `686d606534906358d35934bf6430972279efeab387731b4178d2dfbd2fe12070`.

2103269 extends the separately preserved, UNLOCKED 2103268 Display/player candidate, source `46de646cc8a87c4dfafe2e7bf9b1776c011cadeb`, APK SHA-256 `de03a34643a4693162c2cd46912b826b4a77aaafbb4491ce46d1d33bf1f6d4e8`. 2103268 is not promoted to a locked baseline by this pass. Its approved forward repairs are retained; no older APK/engine/provider code was restored.

Exact tested source commit: `3804ae1a680606e15b931fa33537644b0dc21e20`.
Android run: https://github.com/mahfouzhassine8-ops/project-infinity/actions/runs/36741769377

## Independent failures reproduced before repair

The same intended-outcome tests were run against exact 2103268 before applying repairs. All three failed with product assertions, rather than compiler/setup errors:

1. Constrained chooser cards occupied less than the pre-established 55% window-area usability floor: the original fixed-coordinate portrait composition was shrunk, not reflowed.
2. A 320px measured window was reported as 1200px after deliberately leaving full-display metrics larger. Shared sizing helpers used the wrong dimensions.
3. A player action occupied `Rect(16, 200 - 128, 252)` in a `480×240` window: its bottom escaped the pane by 12px.

Drawer width was also found to be computed only at opening. The repaired open drawer is tested while resizing from 800px to 320px, without closing/reconstructing it.

## Repairs

- Choose Your Experience detects multi-window and lays out the EXISTING cards/actions at actual measured bounds. Narrow/tall panes stack the two cards; other constrained shapes place them side by side. Decorative floor/large branding is suppressed, heading space follows readable text, and settings/entry targets stay independent and reachable.
- Responsive source marks retain their proportions and receive intentional rounded framing. No art asset is edited, regenerated or replaced. Compact card content is balanced vertically rather than concentrating tiny content at its top.
- Fullscreen chooser geometry retains the original rendering path. Returning from multi-window restores pixel-identical same-size images; all 20 locked protected chooser/settings/Health/recovery renders also match byte-for-byte.
- Cobra shared size/orientation classification prefers measured decor, then current WindowMetrics/configuration. Display metrics are a last startup fallback. Player, sources, navigation and preference ownership are not added to sizing logic.
- An already open Cobra drawer updates its width inside the resized pane.
- Very short player panes reduce duplicate metadata/decorative spacing and budget system insets. Transport, timeline, bottom actions and locked playback behavior remain intact. Normal-size player rendering is retained.

## Intended → observed → result → action

| Feature | Intended | Observed evidence | Result / remaining action |
|---|---|---|---|
| Chooser constrained geometry | Readable independent choices, no miniature full-phone composition | Production native views at 8 sizes × Dark/Light; name fit/readability, ≥55% card area and nonoverlap asserted; final screenshots inspected | AUTOMATED PASS; verify Samsung WM |
| Chooser touch/settings | ≥48dp settings; independent gear/Enter targets; correct destination once | Actual dispatched touch events processed through Android event loop, correct single callback; existing Splash options-routing suite retained | AUTOMATED PASS; physical touch required |
| Chooser large text/insets | Heading and controls fully inside available content | 1.6 font scale, inset-adjusted panes including 336×220, heading line bottoms and targets checked; render inspected | AUTOMATED PASS; actual Fold safe areas required |
| Chooser fullscreen restore | Same approved composition, no state/action reconstruction | Before/resize/after bitmap equality; same card objects; no navigation callbacks during resizing; 20 protected render matches | AUTOMATED PASS; physical restoration required |
| Current window classification | Measured bounds win over full-display metrics/orientation | Deliberately inconsistent physical metrics vs decor produces correct 320×720 and 720×320 classification | AUTOMATED PASS |
| Cobra five Live TV layouts | Persistent shell and usable channel browser at real bounds | 5 modes × 5 sizes × OLED/Light, populated controlled channel data; actual decor dimensions asserted; shell, route, provider/data objects retained | AUTOMATED PASS; provider/decoded preview/device focus required |
| Cobra drawer | Live resize stays inside actual window, Power reachable | Open drawer reflow, full Power bounds, both appearances; renders inspected | AUTOMATED PASS; OEM insets/keyboard required |
| Cobra Movies/Shows | Same page/navigation/catalog scroll through resize | Populated controlled catalogs, actual configuration callbacks at 4 sizes × both appearances, same page/scroll/provider objects and usable scroll viewport | AUTOMATED PASS; real provider artwork/network required |
| Cobra settings | Same page and reachable navigation | Actual configuration callbacks at 3 sizes × both appearances, retained settings content/header; renders inspected | AUTOMATED PASS; physical large-text interactions required |
| Short fullscreen player | No clipped transport/top/bottom actions | Every named action fully visible at 480×240, 720×280 and 320×240; baseline red test above; final renders inspected | AUTOMATED PASS; actual insets/decoder required |
| Fullscreen player/Display restore | Same source/texture/player/position, no second session or Display reset | 5 sizes, production chrome/sheets + controlled Media3 state, no seek/prepare/release, saved Zoom unchanged, visible Close; existing 15-mode product suite retained | AUTOMATED PASS for tested UI/state; real playback/timeshift required |
| Playing dot, empty-video hold, Ambient/Cinema, Pro | Preserve accepted behavior | Source-preservation whitelist; inherited intended-outcome suites all pass, no protected member/class changes | AUTOMATED preservation PASS; device acceptance remains open |
| Multi-View | Independent owners/transforms, preserved layouts during transitions | Existing 10-test Multi-View and 18-test lifecycle suites plus 268 product tests retained; controlled Media3 state | AUTOMATED preservation PASS; actual Fold resizing of every tile count required |
| Options/Health/recovery | Header/Close/Cancel reachable, real callback semantics | Existing native view short-window/large-text/action tests retained and golden renders unchanged | AUTOMATED tested geometry/actions PASS; actual live dialog resizing/device required |
| Infinity native window bridge | Publish actual native-view dimensions without added provider/player reset | Source reviewed: InfinityCoreBridge publishes measured view width/height on layout; Main configuration/multi-window callbacks request layout and publish bounds. All those files/JNI/native libs unchanged | SOURCE REVIEW ONLY; native render/state not verified |
| Infinity .172 Home/widgets/Movies/Shows/Live TV/drawer/settings/native dialogs/Health | Each actual window genuinely usable, correct native playback/provider/navigation state | Native Kodi and installed skin screens were not executable in Robolectric. No screenshot or geometry evidence from the native renderer was generated | DEVICE REQUIRED; never counted as a product pass |
| Physical Fold inner/cover/split/popup/live resize/fold/unfold/fullscreen | Coherent usable result, no restarts, duplicates or state loss | No physical device available | DEVICE REQUIRED; checklist included |
| Update-over-install/user data | Same permanent identity, higher version, preserved data | Package/version/certificate compatibility verified statically; actual device installation not executed | STATIC COMPATIBILITY PASS / DEVICE REQUIRED |

## Verification and evidence limits

211 tests in 21 Android/Robolectric suites; zero failures, errors or skips. This retains the earlier 203 Display/player/playing-dot/Pro/glass/call/PiP/background/subtitle/timeshift/Multi-View intended-outcome tests and adds 8 responsive product tests. 122 new responsive screenshots were generated. Tests use production Android views, native Canvas, actual measured window/decor geometry and controlled channel/catalog data.

Screenshots of player/video areas contain controlled metadata with no real decoded stream (black TextureViews in some captures; the inherited Display diagnostic images explicitly label their synthetic source). Empty poster areas in catalog fixtures have intentionally empty artwork URLs. These images establish UI geometry, NOT real video visibility, codec output, poster fetching, audio continuity or Samsung WM behavior. The full native Infinity skin renderer is not represented by an Android chooser fixture.

The source whitelist permits exactly 3 production shell files:

1. `tools/android/packaging/xbmc/src/InfinityGlassChooser.java.in` — constrained rendering path; legacy path preserved.
2. `tools/android/packaging/xbmc/src/InfinityLiveActivity.java.in` — `isCompact`, `isMedium`, `isPortrait`, `cobraWidthDp`, `cobraHeightDp`, `toggleCobraDrawer`, `cobraBuildPlayerChrome`, plus a sizing-only `cobraWindowPixels` helper.
3. `tools/android/packaging/xbmc/build.gradle.in` — version code/name.

All other 229 shell files and all Activity code outside those seven members/new helper are byte-identical to the 268 checkpoint. Packaging scripts update release/checkpoint metadata only; exact scripts are included. No skin, provider, native engine, subtitle/call/timeshift/playing-dot/Pro logic is rebuilt or replaced. Independent APK comparison found 4151 unchanged native/asset/resource ZIP entries. The packaging gates additionally preserve 46 native files, 4039 assets/resources, 66 JNI declarations, 78 native-facing Java classes and 186 resource IDs.

## Signed candidate

Package: `com.projectinfinity.kodi`. Version code: **2103269**. Version name: `1.0.9-Responsive-Window-RC1`.

APK SHA-256: `f71fdfad769ae30e57c2c96ab4dbaf51062fc483e54f1702114517fcf47befce`.

Permanent signer certificate SHA-256: `d7adeb68e9341596a02bd3262b737a0f45fc6e771ed7e60285437e833b58c6d7` (same identity as 267/268). Signature schemes v1/v2/v3 verified. Native core SHA-256 remains `c7976ce0adb45b9264f2092a27111be4e05bde4220be2b26b1ea0e2cc74f1e2d`.

No signing private key is present in the evidence package. No Infinity skin ZIP was created. Actual update-over-install, native Infinity rendered usability and the complete physical Fold checklist remain pending. **Do not lock this candidate until those pass.**
