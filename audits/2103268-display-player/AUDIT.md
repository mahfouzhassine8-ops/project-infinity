# Cobra Display + Fullscreen Player — preservation-first audit

Status: **AUTOMATED TEST CANDIDATE — PASS.** Physical Fold acceptance is NOT complete. This report never equates controlled Android tests with live decoding, audibility, Samsung fold/PiP behavior or user acceptance.

## Exact lineage and preservation

Start: `locked-infinity-cobra-2103267-playing-dot-restore-device-passed-20260930`.
Locked source commit: `292351efa4e0840c1f01b343a81e62b8905ba3f0`.
Untouched rollback APK SHA-256: `686d606534906358d35934bf6430972279efeab387731b4178d2dfbd2fe12070`.
Reconstructed source archive SHA-256: `2d7444bfac5a9fa8a364c1edc6c3fb58886159d41cbb6cee0d8252567e18`.
The native engine, APK assets/resources, JNI contract, providers, Pro Mode, other modes, Smart Return, navigation, call policy, PiP and timeshift implementations passed preservation gates. Infinity skin .172 is untouched and no skin ZIP is a deliverable.

Acceptance requirements are written first in ACCEPTANCE.md. Baseline failure evidence, candidate tests, actual-window bounds, screenshot inspection and physical observations are separate evidence layers. The earlier Display matrix that simply reproduced current formulas is not accepted as product proof.

## Final automated verification and visual review

Source/test commit: `46de646cc8a87c4dfafe2e7bf9b1776c011cadeb`.
Successful Android run: https://github.com/mahfouzhassine8-ops/project-infinity/actions/runs/36699564793
APK: `Infinity-2103268-Cobra-Display-Player-RC1.apk`; version code **2103268**.
APK SHA-256: `de03a34643a4693162c2cd46912b826b4a77aaafbb4491ce46d1d33bf1f6d4e8`.
Permanent certificate SHA-256: `d7adeb68e9341596a02bd3262b737a0f45fc6e771ed7e60285437e833b58c6d7`.

- 203 tests in 20 Android suites: zero failures, errors or skips. This includes 15 new product-outcome tests, actual slider MotionEvents and icon state, scrubber/timeshift, subtitles, calls/audio focus, PiP/lifecycle, Multi-View and locked glass/Pro/dot regressions.
- 240 baseline/candidate observation pairs from the actual menu and verified 800×600, 600×800, 320×720 and 960×540 windows/player panes. Independent shape/utilization/label/transition tests accompany the observation record; the CSV itself is not a product oracle.
- 20 locked protected PNGs remain byte-identical. Native source/resources and package/signature gates passed. Local independent APK comparison rechecked 4,151 native/asset/resource entries; all match baseline bytes.
- 46 native files, 4,039 assets, Android resources, 66 JNI declarations and 78 native-facing Java classes are preserved by the packaging gate. 230 of 232 shell-source files are byte-identical.
- Final rendered inspection: proportional diagnostic circles, usable controls across four shapes, white controls under both app appearances, readable glass sheets, pinned Display title/Close, visible selected lower choice and scroll cue, authoritative Channels dot. Diagnostic frames are labeled synthetic and do not prove native decoding.
- The earlier missing historical adaptations were resolved with the exact recorded 2103202 menu migrations, 2103203 wording and 2103207 audio/call adapters. Historical source tests were not edited; disposable staged copies and their complete resulting source are included. The explicit 2103267 inert-hold expectation remains the locked oracle.

**No physical Fold is connected.** Real update-over-install/data retention, live decoder/aspect output, recorded/encoded bars, audibility, providers/recording/cast, real PiP/SystemUI, incoming calls, fold/unfold, Android multi-window and physical timing are UNVERIFIED. The candidate is not locked, device-passed, final or stable.

Fold Fit is byte-preserved, but the observation record makes its crop tradeoff explicit: with 16:9 metadata in a 320×720 cover-shaped pane, geometry uses 60% of the pane and crops 58.3% of the proportional source; full cover crops 75%. This is a crop-comfort review item for the real Fold, not a pass inferred from preserving the existing formula.

## Best Fit history investigation

1. 2103151's `applyCobraAspectTransform` reset TextureView view scales/translations and returned for mode 0. 2103152 preserved that branch. This left the buffer at the full pane; it does not establish proportional source geometry or a physical approval of proportional filling.
2. 2103153 introduced `CobraLayoutMath.fit`, source/pixel aspect correction and a centered contain matrix. Its accompanying description explicitly promised preserved proportions. This is the first identified change from the earlier full-pane mode-0 path.
3. The mode 0–11 **fit method** in locked 2103207 is byte-identical to 2103267: SHA-256 `2e670b1b2dc6da809817b31da090df2ae5bb48c218c0d16c4f3bcd262f554a94`. The wider class also contains tile-layout logic; equality here is specifically the fit method.
4. Later Fold changes introduced/changed modes 12 and 13, including device-driven bounded Fold Fit. They did not restore mode 0. Glass/Cinema/playing-dot work was not the origin of this fitting change.
5. The supplied physical landscape screenshot has Best Fit selected and a narrow central cartoon picture with large black side bands. That contradicts the user's current screen-utilization expectation. Its exact decoded sample/pixel ratio cannot be proven from the image alone.

**Unresolved historical acceptance:** no last device-passed proportional full-pane Best Fit implementation was recovered. Older descriptions favor complete-picture fitting, while the user's report favors screen filling. The candidate interpretation is explicitly disclosed: proportional minimum center crop in fullscreen; preview and PiP retain complete-picture fitting. It uses the already accepted Fill policy forward on 2103267 and does not restore an old APK or legacy stretching.

**IMPLEMENTATION PASS / PRODUCT BEHAVIOR REVIEW REQUIRED:** Best Fit's restored behavior needs the physical Fold comparison and user acceptance. It must not be described as an exactly recovered historical proportional-fill approval.

## Display audit matrix

Baseline and candidate observations must come from the production Activity/TextureView and actual UI action. Native rendering uses an explicitly labeled diagnostic source; native decoder output remains a device gate.

| Choice | Intended user-visible result | Baseline observation | Audit verdict | Candidate action / acceptance |
| --- | --- | --- | --- | --- |
| Fold Fit | Proportional bounded crop; reduce bands; gentler than Fill | Locked balanced policy uses more pane than strict containment on mismatched Fold ratios | AUTOMATED geometry/action PASS; device UNVERIFIED | Preserve accepted policy; verify actual rectangles, shape and comparison; physical crop comfort pending |
| Fold Fill | Entire pane, minimum proportional center crop | Existing proportional cover policy | AUTOMATED geometry/action PASS; device UNVERIFIED | Preserve; assert no bars, centered crop and source proportions on inner/cover shapes |
| Inherit Default | Remove channel override; follow later global changes | Channel preferences store -1 and resolve current saved global preference | AUTOMATED geometry/action PASS; device UNVERIFIED | Exercise actual Inherit and global-default controls; verify resulting geometry/checkmarks and unchanged unrelated preferences |
| Best Fit | Substantially fuller/full fullscreen pane, truthful description, preserve shape | Strict containment; screenshot shows giant side bands; Android 800×600/16:9 observes 800×450 with 75px top/bottom bands | Baseline utilization FAIL; candidate automated PASS; historical/device REVIEW | Fullscreen-only proportional cover; preview/PiP preserved; historical conflict and physical acceptance explicitly pending |
| Crop / Fill | Entire viewport with only necessary proportional crop | Existing full cover | AUTOMATED geometry/action PASS; device UNVERIFIED | Preserve; document compatibility alias with Fold Fill and candidate fullscreen Best Fit |
| 16:9 | Centered labeled display shape | Existing fixed display aspect; can reshape source | AUTOMATED geometry/action PASS; device UNVERIFIED | Test 16:9, 4:3, portrait and unusual source; disclose intentional reshape |
| 4:3 | Centered labeled display shape | Existing fixed display aspect; can reshape source | AUTOMATED geometry/action PASS; device UNVERIFIED | Same independent shape check across representative source content |
| Wide 1.10× | Whole-frame fit widened 10%, centered | Existing horizontal-only modifier | AUTOMATED geometry/action PASS; device UNVERIFIED | Preserve; verify actual width progression/unchanged height; disclose intentional stretch |
| Wide 1.25× | Whole-frame fit widened 25%, centered | Existing horizontal-only modifier | AUTOMATED geometry/action PASS; device UNVERIFIED | Preserve; independently compare visible width to whole-frame reference |
| Wide 1.40× | Whole-frame fit widened 40%, centered | Existing horizontal-only modifier | AUTOMATED geometry/action PASS; device UNVERIFIED | Preserve; confirm progressive increase and reset after switching |
| Short + Wide | Deliberate wider/shorter picture | Existing width 124%, height 84% | AUTOMATED geometry/action PASS; device UNVERIFIED | Preserve accepted factors, describe them explicitly; test both axes and center |
| Zoom 1.25× | Uniform centered whole-frame enlargement | Existing uniform 1.25× | AUTOMATED geometry/action PASS; device UNVERIFIED | Preserve; confirm shape, enlargement and intentional crop; not promised to fill every extreme aspect |
| Zoom 1.50× | Uniform centered enlargement greater than 1.25× | Existing uniform 1.50× | AUTOMATED geometry/action PASS; device UNVERIFIED | Preserve; actual matrix/pane observation, no cumulative transform |
| Zoom 2.00× | Uniform centered enlargement greater than 1.50× | Existing uniform 2.00× | AUTOMATED geometry/action PASS; device UNVERIFIED | Preserve; centered progressive crop and reset after leaving |
| Custom Width / Height | Independent reachable 55–180% factors, persistence/isolation/reset | Sliders and scoped preferences exist; live per-channel editor has no reset | Baseline reset FAIL; actual slider/reset automated PASS; device UNVERIFIED | Add channel-only reset to 100%; preserve bounds/persistence and test another channel remains unchanged |

Best Fit, Crop / Fill and Fold Fill intentionally have equal proportional-cover fullscreen geometry on identical inputs. Their existing IDs remain compatible with saved preferences and historical menu entry points. They are not presented as distinct algorithms. Fold Fit remains the gentler option. Default/preview/PiP and Multi-View policies remain explicitly scoped.

## Display sheet and player presentation findings

| Intended | Observed on locked baseline | Action |
| --- | --- | --- |
| A user can discover all 15 choices | Physical screenshot shows only initial rows; no explicit scroll cue. Android sheet lacks the new cue/selected auto-reveal | Add persistent scroll affordance, non-fading scrollbar, bottom edge fade, and reveal the selected row after layout; pin the Display title/Close header so revealing a lower row cannot hide dismissal; verify actual portrait/landscape bounds |
| Selected state reflects the choice | Live channel rows use actual preferences; non-live picker relied on “Selected” descriptive text | Use consistent selected/checkmark rows for non-live Display; preserve stored choice |
| Custom values can be reset without clearing other settings | Per-channel custom editor lacks a reset control | Add scoped width/height reset; retain aspect 11 and other preferences |
| Five transport controls remain inside a true cover pane | Strict actual-window test and 320×720 baseline screenshot PASS; controls fit with little side margin | Restrained polish: increase breathing room using compact spacing/widths with minimum 48dp targets; larger layouts retain sizing. This is not labeled an established baseline defect. |
| Actual player Channels shows the authoritative playing state | Guide views have the locked dot; fullscreen Channels adapter only returns text buttons | Bind existing dot to drawer rows using the same actual-session ownership policy; preserve focus/selection independence and original row actions |
| Only one player menu surface is open | Some entry paths only closed one peer surface | Display and More also close the Multi-View picker before opening; no player/session replacement |

A candidate render exposed title/Close clipping after lower-choice auto-reveal. The Display header is therefore fixed outside its scrolling options, and the scroll height reserves space for that header and cue. Other sheets retain their locked arrangement.

Fullscreen player chrome and sheets intentionally retain the locked dark viewing treatment even when app appearance is Light; the Light-pref renders verify readable white playback controls/dark glass, rather than falsely claiming a pearl fullscreen player. Browsing/Pro Light variants remain unchanged.

Animations retain the current glass system, sheet easing and locked dot policy. No new decorative layer covers the video. Focus feedback for drawer rows must remain visible, accessible and truthful.

## Complete player audit matrix

All rows require physical acceptance even when controlled Android/source gates pass. A downstream network/service/device outcome is not marked passed from a callback or stored preference.

| Function | Intended → observed/check | Product verdict | Action / remaining gate |
| --- | --- | --- | --- |
| Last channel / Recents | Tap returns to the prior channel; hold opens playback Recents with truthful ordering | UNVERIFIED on device | Preserve existing actions; channel provider tune and actual history sequence require Fold |
| Favorite | Add/remove immediately, truthful icon, persistent synced state | UNVERIFIED on device | Preserve state implementation; existing action regressions plus physical rail/drawer synchronization |
| Rotation control | Icon reflects requested orientation policy and viewport reflows | UNVERIFIED on device | Preserve; reflow uses existing surface, physical Samsung rotation policy pending |
| Player lock | Controls inaccessible; tap exposes unlock; no playback action from locked hold/tap | UNVERIFIED on device | Real Activity lock/unlock and no-menu tests; physical touch/rotation/fold pending |
| Play / pause / resume | Actual owned player's requested/suppressed state matches icon | UNVERIFIED on device | Existing AudioFocus/PiP tests exercise pause intent and callbacks; actual audibility/video pause pending |
| Previous / next | One intended channel transition; disabled in enlarged Multi-View | UNVERIFIED on device | Preserve original stepping; real rapid channel changes and provider startup pending |
| LIVE / transport availability | Non-live/unsupported states must not pretend to be seekable live | UNVERIFIED on device | Preserve availability and timeline ownership logic; controlled live windows and real streams must both be checked |
| Timeline position and live edge | Position/range correspond to actual session; no fake seek controls while warming/off | UNVERIFIED on device | Android scrubber tests cover native/local window readiness and unavailable states; real buffered pixels/window lengths pending |
| Rewind / forward / drag | Drag changes preview; one seek on release, cancellation/stale owner safe | UNVERIFIED on device | Existing scrubber suite tests real MotionEvents and owned controlled player, retained source; native rewind/retention/forward pending |
| Go Live / Reset Live | Return to actual live broadcast/edge without stale window or display | UNVERIFIED on device | Preserve implementations; native live-edge/provider outcomes pending |
| Channels | Groups/Favorites/Recent/All usable; focused and playing are separate | UNVERIFIED on device | Existing filters/actions preserved; add locked-session dot to this actual drawer; physical switching/filter history pending |
| Channels / Display / Multi-View / More | One surface, Back/outside dismiss, playback/context retained | UNVERIFIED on device | Real Activity sheet transitions and preservation checks; physical focus/remote/touch dismissal pending |
| 2 portrait / 2 landscape / 3 / 4 Multi-View | Layout occupies intended pane, independently playing feeds | UNVERIFIED on device | Existing layout tests and lifecycle source preserved; actual concurrent decoder behavior pending |
| Enlarge / return / adding / removing tiles | Preserve peer sessions and originating owner/layout | UNVERIFIED on device | Existing lifecycle/PiP tests and source equality; full physical tile session pending |
| Multi-View audio / Display isolation | Audio owner changes cannot pause peers; per-channel transforms do not leak | UNVERIFIED on device | Controlled owned-player and tile transforms; actual audio routing/display/decoder continuity pending |
| More: Channel playback | Opens current channel's preferences | UNVERIFIED on device | Actual source routing and inherited options tests; physical tune/recovery paths pending |
| More: Health | Observable diagnostics; does not stop playback or invent success | UNVERIFIED on device | Existing Health action regressions; actual device vitals/source availability pending |
| More: Night Cinema | Immediate surrounding UI atmosphere update, readable controls, saved state | UNVERIFIED on device | Ambient/Glass regression suite and unchanged video fitting; physical appearance/readability pending |
| More: Restart programme | Only appears when catch-up is available; provider starts intended programme | UNVERIFIED on device | Conditional source path preserved; requires an actual supported provider/programme |
| More: Record / Stop | Duration prompt/recording outcome is truthful; failure explained | UNVERIFIED on device | Original recording dialog/storage/service implementation preserved; recording output requires real source/storage/service test |
| More: Audio & subtitles | Actual current session tracks, supported choices, synchronized disabled/selected states | UNVERIFIED on device | Android subtitle tests verify real chooser/cues and track parameter changes; actual caption pixels/language/audio audibility pending |
| More: Cast / Route | Opens actual Android route settings or truthful unavailable message | UNVERIFIED on device | Existing ACTION_CAST_SETTINGS path preserved; receiving device/system availability pending |
| More: Manage sources | Leaves player and shows Sources | UNVERIFIED on device | Existing source/navigation path preserved; real full session/context/account check pending |
| More: Close / Return Multi | Close stops current playback; Return Multi keeps all tiles | UNVERIFIED on device | Preserved exact close/return implementation; physical full-session check pending |
| Subtitle Off / track / language | Off clears displayed captions and disables text; supported tracks/languages truthful | UNVERIFIED on device | Subtitle suite covers stale owner, discovery, Off cues, preferred language and synchronization; live provider tracks pending |
| Subtitle size / adaptation | Fits actual video pane; readable at chosen size | UNVERIFIED on device | Retain caption-fitting source and adaptive policies; real subtitle bounding/clipping/safe area pending |
| Ambient Off / Subtle / Immersive | Changes UI atmosphere immediately; video matrix/pixels unaffected | UNVERIFIED on device | Actual UI/presentation tests and exact effect source preservation; decoded color comparison pending |
| Empty fullscreen long-press | Opens no Channels/Live TV/menu; ordinary tap still toggles controls | UNVERIFIED on device | Locked hold consumer byte-preserved; real Activity gesture/lock tests; physical gesture acceptance pending |
| PiP pause/play/return | Same owner and pause intent; safety fit active only in PiP; saved Display restored | UNVERIFIED on device | MediaSession/PiP/lifecycle tests plus transform round-trip; Samsung SystemUI and live position retention pending |
| Background / foreground | Accepted opt-in behavior, preserved owner/timeshift/Display | UNVERIFIED on device | Background policy/lifecycle controlled tests and byte-preserved code; actual process/system behavior pending |
| Incoming call / audio focus | Approved normal/manual policy; no automatic decoder restart or position reset | UNVERIFIED on device | AudioManager/focus controlled suite; phone/modem/route audibility and manual resume pending |
| Inner / cover / rotate / fold / multi-window | Reflow the same session/surface, truthful Display and safe controls | UNVERIFIED on device | Strict actual-window geometry/screenshots with existing player object; physical fold/multi-window transitions pending |

## Evidence boundary and next acceptance

Automated tests use actual Android production views and controlled Media3 ownership/state. Matrix observations describe the resulting TextureView mapping; diagnostic-grid screenshots render those mappings under the real chrome/sheets and are labeled synthetic. Neither proves decoded video pixels. The supplied physical screenshot is independent baseline visual evidence, not candidate device proof.

Tests must fail for the intended product problem, not fixture/setup failures. The first narrow-screen probe accidentally rendered at 800×600; it was rejected after image inspection. Subsequent tests require decor AND player pane bounds to equal the requested viewport before assessing geometry/touch controls. The corrected baseline passes the narrow transport reachability oracle; narrow spacing is polish, not a reproduced defect. Four baseline product failures are recorded with their specific intended-outcome assertion messages; all 240 baseline geometry observations succeed.

Permanent signing/package/version/manifest/payload checks establish structural update compatibility. A real update-over-install retaining user data and the coherent Fold acceptance sequence in DEVICE-TEST.md remain required before locking.

Modified production source files are limited to `tools/android/packaging/xbmc/src/InfinityLiveActivity.java.in` and `tools/android/packaging/xbmc/build.gradle.in`. Packaging constants/receipt and the new audit/repair/testing workflow are separate reproducibility files. The exact diff and source inventory name every changed member/file; all other shell bytes and protected APK payload must match 2103267.

## Exact changed-file and helper inventory

Production shell: `tools/android/packaging/xbmc/src/InfinityLiveActivity.java.in`; `tools/android/packaging/xbmc/build.gradle.in`.

Changed existing Activity members: `showCobraAspectPicker`, `cobraShowChannelAspect`, `cobraShowChannelCustomAspect`, `cobraShowPlaybackDefaults`, `showPlayerSettingsDrawer`, `cobraBuildPlayerChrome`, `cobraOpenSheet`, `cobraRenderPlayerDrawer`, `cobraRefreshPlayingIndicators`, `cobraFitVideo`. Added members: `cobraDisplaySheet`, `cobraDisplayDescription`, `cobraRevealDisplaySelection`, `CobraPlayerDrawerRow`. The source gate restores these whitelisted members/removes the exact added block and demands complete byte equality with 2103267.

Packaging/release reproducibility: `scripts/infinity_background_resume.py`, `scripts/package_background_resume.py`, `engine/background-resume-source.json` update the forward version, exact parent/hash, output names and evidence receipt. Native signing/merge behavior is preserved.

New audit infrastructure: `.github/workflows/infinity-2103268-display-player-audit.yml`; under `repairs/display-player-2103268/`: `apply.py`, `verify_source.py`, `stage_tests.py`, `observations.py`, `Cobra2103268ProductAuditTest.java`, `ACCEPTANCE.md`, `AUDIT.md`, `DEVICE-TEST.md`. Historical fixture source files remain unmodified; only staged copies receive the documented prior approved adapters. Final documentation under `audits/2103268-display-player/` does not change the tested APK/source commit.
