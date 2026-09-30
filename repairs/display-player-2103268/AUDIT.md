# Cobra Display + Fullscreen Player — preservation-first audit

Status: audit and Android verification in progress. Physical Fold acceptance is NOT complete. This report never equates controlled Android tests with live decoding, audibility, Samsung fold/PiP behavior or user acceptance.

## Exact lineage and preservation

Start: `locked-infinity-cobra-2103267-playing-dot-restore-device-passed-20260930`.
Locked source commit: `292351efa4e0840c1f01b343a81e62b8905ba3f0`.
Untouched rollback APK SHA-256: `686d606534906358d35934bf6430972279efeab387731b4178d2dfbd2fe12070`.
Reconstructed source archive SHA-256: `2d7444bfac5a9fa8a364c1edc6c3fb58886159d41cbb6cee0d8252567e18`.
The native engine, APK assets/resources, JNI contract, providers, Pro Mode, other modes, Smart Return, navigation, call policy, PiP and timeshift implementations are preservation gates. Infinity skin .172 is untouched and no skin ZIP is a deliverable.

Acceptance requirements are written first in ACCEPTANCE.md. Baseline failure evidence, candidate tests, actual-window bounds, screenshot inspection and physical observations are separate evidence layers. The earlier Display matrix that simply reproduced current formulas is not accepted as product proof.

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

| Choice | Intended user-visible result | Baseline observation | Candidate action / acceptance |
| --- | --- | --- | --- |
| Fold Fit | Proportional bounded crop; reduce bands; gentler than Fill | Locked balanced policy uses more pane than strict containment on mismatched Fold ratios | Preserve accepted policy; verify actual rectangles, shape and comparison; physical crop comfort pending |
| Fold Fill | Entire pane, minimum proportional center crop | Existing proportional cover policy | Preserve; assert no bars, centered crop and source proportions on inner/cover shapes |
| Inherit Default | Remove channel override; follow later global changes | Channel preferences store -1 and resolve current saved global preference | Exercise actual Inherit and global-default controls; verify resulting geometry/checkmarks and unchanged unrelated preferences |
| Best Fit | Substantially fuller/full fullscreen pane, truthful description, preserve shape | Strict containment; screenshot shows giant side bands; Android 800×600/16:9 observes 800×450 with 75px top/bottom bands | Fullscreen-only proportional cover; preview/PiP preserved; historical conflict and physical acceptance explicitly pending |
| Crop / Fill | Entire viewport with only necessary proportional crop | Existing full cover | Preserve; document compatibility alias with Fold Fill and candidate fullscreen Best Fit |
| 16:9 | Centered labeled display shape | Existing fixed display aspect; can reshape source | Test 16:9, 4:3, portrait and unusual source; disclose intentional reshape |
| 4:3 | Centered labeled display shape | Existing fixed display aspect; can reshape source | Same independent shape check across representative source content |
| Wide 1.10× | Whole-frame fit widened 10%, centered | Existing horizontal-only modifier | Preserve; verify actual width progression/unchanged height; disclose intentional stretch |
| Wide 1.25× | Whole-frame fit widened 25%, centered | Existing horizontal-only modifier | Preserve; independently compare visible width to whole-frame reference |
| Wide 1.40× | Whole-frame fit widened 40%, centered | Existing horizontal-only modifier | Preserve; confirm progressive increase and reset after switching |
| Short + Wide | Deliberate wider/shorter picture | Existing width 124%, height 84% | Preserve accepted factors, describe them explicitly; test both axes and center |
| Zoom 1.25× | Uniform centered whole-frame enlargement | Existing uniform 1.25× | Preserve; confirm shape, enlargement and intentional crop; not promised to fill every extreme aspect |
| Zoom 1.50× | Uniform centered enlargement greater than 1.25× | Existing uniform 1.50× | Preserve; actual matrix/pane observation, no cumulative transform |
| Zoom 2.00× | Uniform centered enlargement greater than 1.50× | Existing uniform 2.00× | Preserve; centered progressive crop and reset after leaving |
| Custom Width / Height | Independent reachable 55–180% factors, persistence/isolation/reset | Sliders and scoped preferences exist; live per-channel editor has no reset | Add channel-only reset to 100%; preserve bounds/persistence and test another channel remains unchanged |

Best Fit, Crop / Fill and Fold Fill intentionally have equal proportional-cover fullscreen geometry on identical inputs. Their existing IDs remain compatible with saved preferences and historical menu entry points. They are not presented as distinct algorithms. Fold Fit remains the gentler option. Default/preview/PiP and Multi-View policies remain explicitly scoped.

## Display sheet and player presentation findings

| Intended | Observed on locked baseline | Action |
| --- | --- | --- |
| A user can discover all 15 choices | Physical screenshot shows only initial rows; no explicit scroll cue. Android sheet lacks the new cue/selected auto-reveal | Add persistent scroll affordance, non-fading scrollbar, bottom edge fade, and reveal the selected row after layout; verify actual portrait/landscape bounds |
| Selected state reflects the choice | Live channel rows use actual preferences; non-live picker relied on “Selected” descriptive text | Use consistent selected/checkmark rows for non-live Display; preserve stored choice |
| Custom values can be reset without clearing other settings | Per-channel custom editor lacks a reset control | Add scoped width/height reset; retain aspect 11 and other preferences |
| Five transport controls remain inside a true cover pane | Source sizing can exceed a 320dp viewport | Require actual rendered bounds; use compact spacing/widths with minimum 48dp targets when the pane is narrow; larger layouts retain sizing |
| Actual player Channels shows the authoritative playing state | Guide views have the locked dot; fullscreen Channels adapter only returns text buttons | Bind existing dot to drawer rows using the same actual-session ownership policy; preserve focus/selection independence and original row actions |
| Only one player menu surface is open | Some entry paths only closed one peer surface | Display and More also close the Multi-View picker before opening; no player/session replacement |

Animations retain the current glass system, sheet easing and locked dot policy. No new decorative layer covers the video. Focus feedback for drawer rows must remain visible, accessible and truthful.

## Complete player audit matrix

All rows require physical acceptance even when controlled Android/source gates pass. A downstream network/service/device outcome is not marked passed from a callback or stored preference.

| Function | Intended → observed/check | Action / remaining gate |
| --- | --- | --- |
| Last channel / Recents | Tap returns to the prior channel; hold opens playback Recents with truthful ordering | Preserve existing actions; channel provider tune and actual history sequence require Fold |
| Favorite | Add/remove immediately, truthful icon, persistent synced state | Preserve state implementation; existing action regressions plus physical rail/drawer synchronization |
| Rotation control | Icon reflects requested orientation policy and viewport reflows | Preserve; reflow uses existing surface, physical Samsung rotation policy pending |
| Player lock | Controls inaccessible; tap exposes unlock; no playback action from locked hold/tap | Real Activity lock/unlock and no-menu tests; physical touch/rotation/fold pending |
| Play / pause / resume | Actual owned player's requested/suppressed state matches icon | Existing AudioFocus/PiP tests exercise pause intent and callbacks; actual audibility/video pause pending |
| Previous / next | One intended channel transition; disabled in enlarged Multi-View | Preserve original stepping; real rapid channel changes and provider startup pending |
| LIVE / transport availability | Non-live/unsupported states must not pretend to be seekable live | Preserve availability and timeline ownership logic; controlled live windows and real streams must both be checked |
| Timeline position and live edge | Position/range correspond to actual session; no fake seek controls while warming/off | Android scrubber tests cover native/local window readiness and unavailable states; real buffered pixels/window lengths pending |
| Rewind / forward / drag | Drag changes preview; one seek on release, cancellation/stale owner safe | Existing scrubber suite tests real MotionEvents and owned controlled player, retained source; native rewind/retention/forward pending |
| Go Live / Reset Live | Return to actual live broadcast/edge without stale window or display | Preserve implementations; native live-edge/provider outcomes pending |
| Channels | Groups/Favorites/Recent/All usable; focused and playing are separate | Existing filters/actions preserved; add locked-session dot to this actual drawer; physical switching/filter history pending |
| Channels / Display / Multi-View / More | One surface, Back/outside dismiss, playback/context retained | Real Activity sheet transitions and preservation checks; physical focus/remote/touch dismissal pending |
| 2 portrait / 2 landscape / 3 / 4 Multi-View | Layout occupies intended pane, independently playing feeds | Existing layout tests and lifecycle source preserved; actual concurrent decoder behavior pending |
| Enlarge / return / adding / removing tiles | Preserve peer sessions and originating owner/layout | Existing lifecycle/PiP tests and source equality; full physical tile session pending |
| Multi-View audio / Display isolation | Audio owner changes cannot pause peers; per-channel transforms do not leak | Controlled owned-player and tile transforms; actual audio routing/display/decoder continuity pending |
| More: Channel playback | Opens current channel's preferences | Actual source routing and inherited options tests; physical tune/recovery paths pending |
| More: Health | Observable diagnostics; does not stop playback or invent success | Existing Health action regressions; actual device vitals/source availability pending |
| More: Night Cinema | Immediate surrounding UI atmosphere update, readable controls, saved state | Ambient/Glass regression suite and unchanged video fitting; physical appearance/readability pending |
| More: Restart programme | Only appears when catch-up is available; provider starts intended programme | Conditional source path preserved; requires an actual supported provider/programme |
| More: Record / Stop | Duration prompt/recording outcome is truthful; failure explained | Original recording dialog/storage/service implementation preserved; recording output requires real source/storage/service test |
| More: Audio & subtitles | Actual current session tracks, supported choices, synchronized disabled/selected states | Android subtitle tests verify real chooser/cues and track parameter changes; actual caption pixels/language/audio audibility pending |
| More: Cast / Route | Opens actual Android route settings or truthful unavailable message | Existing ACTION_CAST_SETTINGS path preserved; receiving device/system availability pending |
| More: Manage sources | Leaves player and shows Sources | Existing source/navigation path preserved; real full session/context/account check pending |
| More: Close / Return Multi | Close stops current playback; Return Multi keeps all tiles | Preserved exact close/return implementation; physical full-session check pending |
| Subtitle Off / track / language | Off clears displayed captions and disables text; supported tracks/languages truthful | Subtitle suite covers stale owner, discovery, Off cues, preferred language and synchronization; live provider tracks pending |
| Subtitle size / adaptation | Fits actual video pane; readable at chosen size | Retain caption-fitting source and adaptive policies; real subtitle bounding/clipping/safe area pending |
| Ambient Off / Subtle / Immersive | Changes UI atmosphere immediately; video matrix/pixels unaffected | Actual UI/presentation tests and exact effect source preservation; decoded color comparison pending |
| Empty fullscreen long-press | Opens no Channels/Live TV/menu; ordinary tap still toggles controls | Locked hold consumer byte-preserved; real Activity gesture/lock tests; physical gesture acceptance pending |
| PiP pause/play/return | Same owner and pause intent; safety fit active only in PiP; saved Display restored | MediaSession/PiP/lifecycle tests plus transform round-trip; Samsung SystemUI and live position retention pending |
| Background / foreground | Accepted opt-in behavior, preserved owner/timeshift/Display | Background policy/lifecycle controlled tests and byte-preserved code; actual process/system behavior pending |
| Incoming call / audio focus | Approved normal/manual policy; no automatic decoder restart or position reset | AudioManager/focus controlled suite; phone/modem/route audibility and manual resume pending |
| Inner / cover / rotate / fold / multi-window | Reflow the same session/surface, truthful Display and safe controls | Strict actual-window geometry/screenshots with existing player object; physical fold/multi-window transitions pending |

## Evidence boundary and next acceptance

Automated tests use actual Android production views and controlled Media3 ownership/state. Matrix observations describe the resulting TextureView mapping; diagnostic-grid screenshots render those mappings under the real chrome/sheets and are labeled synthetic. Neither proves decoded video pixels. The supplied physical screenshot is independent baseline visual evidence, not candidate device proof.

Tests must fail for the intended product problem, not fixture/setup failures. The first narrow-screen probe accidentally rendered at 800×600; it was rejected after image inspection. Subsequent tests require decor AND player pane bounds to equal the requested viewport before assessing geometry/touch controls.

Permanent signing/package/version/manifest/payload checks establish structural update compatibility. A real update-over-install retaining user data and the coherent Fold acceptance sequence in DEVICE-TEST.md remain required before locking.

Modified production source files are limited to `tools/android/packaging/xbmc/src/InfinityLiveActivity.java.in` and `tools/android/packaging/xbmc/build.gradle.in`. Packaging constants/receipt and the new audit/repair/testing workflow are separate reproducibility files. The exact diff and source inventory name every changed member/file; all other shell bytes and protected APK payload must match 2103267.
