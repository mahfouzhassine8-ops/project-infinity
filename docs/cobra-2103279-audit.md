# Cobra 2103279 preservation audit and repair candidate

This is a forward repair candidate. The requested full device/provider acceptance is **not complete**, and this version is **not locked**.

## Source and rollback

- Approved locked source: Cobra 2103278, `41f08774a8b908d60c0f9e6647497e40d6bbe081`.
- Locked branch: `locked-infinity-cobra-2103278-watch-ambient-user-approved-20260930`; verified unchanged after this pass.
- Candidate branch: `candidate-cobra-2103279-end-to-end`.
- Product/runtime source commit: `7c91b569ccb3056ea33439434707c2c52d2bd828`.
- Final candidate build and regression source commit: `92dbd3bb9547e1afe03cfda382abdad6773d7a14`.
- Final build and regression run: [Actions run 36810766190](https://github.com/mahfouzhassine8-ops/project-infinity/actions/runs/36810766190), successful.
- Runtime evidence: [Actions run 36808284951](https://github.com/mahfouzhassine8-ops/project-infinity/actions/runs/36808284951), emulator job passed 21/21. I extracted the APK from that run and confirmed its SHA-256 is byte-identical to the final candidate APK built by run 36810766190. The final run changed only the supplementary test’s list-layout settling and CI runtime scoping, so it reused that exact runtime evidence.
- A rollback Git bundle and exact reconstructed source archive were made before repairs. CI repeats the rollback step before every candidate build.
- The source rollback is also published as [`rollback-cobra-2103278-before-end-to-end-2103279-20261001`](https://github.com/mahfouzhassine8-ops/project-infinity/tree/rollback-cobra-2103278-before-end-to-end-2103279-20261001), pointing to the exact approved commit.

The Android application layer was rebuilt from the locked source archive. The parent APK supplies the preserved native engine, resources and binary assets; it is not replacement source. All 46 native library files, 4,039 assets and Android resources remain byte-identical. The source preservation check also confirms 228 other shell source files remain unchanged.

## Confirmed defects repaired

| Defect | Repair and evidence |
| --- | --- |
| Quick Peek had an independent Fit path, bypassing embedded Fill. | Its actual TextureView now uses the shared proportional Fill calculation and refits on first-frame, surface and layout events. A real independent decoder was exercised without interrupting the main player. |
| Embedded scaling could be lost on reattachment, surface changes or temporary unknown video size. | The existing binding reapplies the transform and retains the last valid dimensions. Real decoded 16:9, 4:3, portrait and odd-aspect fixtures were exercised across Mobile, TV Grid, Compact, Cards and Pro. |
| Some feeds contain black padding within the encoded picture, which ordinary center crop cannot identify. | A conservative embedded-only detector removes stable, symmetric black borders using the minimum additional proportional crop. It requires repeated evidence and retains its prior crop through dark/transient frames. It uses a reusable 96×64 buffer, probes at most every 200 ms during establishment and then every two seconds, and suspends when inactive. Captures fail closed. |
| TextureView readback omits its display transform, so ambient capture could include content the user cannot see. | Ambient capture maps the viewport back into source coordinates before sampling. Capture never temporarily resets the live display transform. The approved renderer, glass design and Off/Subtle behavior are preserved. |
| Direct Movies/Shows playback could lose Watch illumination after guide teardown released its engine. | Eligible Watch playback restores one shared engine behind the UI and reuses it. Showing/hiding controls immediately refreshes illumination instead of waiting for the one-second presentation ticker. Existing visibility, Off/Subtle, background and playback gates remain in force. Video color and fullscreen scaling policy are unchanged. |
| Movie playback exposed a timeline restricted to Live TV. | The existing scrubber and ±30-second transport now seek seekable VOD without preparing or replacing the player. A native touch gesture and visible transport controls were exercised with a real movie decoder. Live rewind policy is preserved. |
| Adaptive subtitles could sit underneath visible player controls. | Adaptive captions fit above the existing footer/mini controls and recalculate as chrome or bounds change. Disabling adaptive placement retains stream placement. Real caption screenshots were inspected. |
| A delayed movie-details response could overwrite a newer drawer destination. | Responses are gated by the current navigation request and profile. A delayed HTTP response was exercised while navigating to Shows. |
| Extremely short windows could push the channel browser out of reach. | When the usable guide height is under 240 dp, the existing guide has a scrollable 360 dp working area. Touch, wheel and accessibility scrolling expose the existing content, retaining the same player and surface. Growing the window resets the overflow. Normal-size layouts are unchanged. Hidden previews suspend both ambient and border sampling, then resume when visible. |
| Changing themes could leave system-bar icons and the underlying screen background out of sync. | Appearance changes immediately refresh both system-bar contrast and the existing backdrop palette. A rendered-background test and a composed-screen status-bar check guard the Light/Dark pairing. Fullscreen system-bar behavior remains unchanged. |
| The player Channels drawer footer hint overlapped transient Android navigation buttons. | The existing drawer content now reserves the actual navigation and cutout insets while leaving the video/player bounds unchanged. On the API 30 emulator, the hint ended 37 px above the safe content boundary, with a 126 px navigation area; its screenshot was visually reviewed. A unit check also verifies that normal padding is restored when insets disappear. |

No controls or approved features were removed. Main playback ownership, native playback engine, fullscreen display preferences and Multi-View scaling policy were preserved.

Pro's approved saved-hero/resting-entry behavior is preserved: entering Pro may intentionally select its saved channel and pause it. The stress test checks that selection and release of the prior binding. Other view-mode changes retain the existing player. This distinction is explicit rather than forcing a new playback policy onto Pro.

## Verification

- Clean Android build and successful release signing for version code **2103279**, version name **1.0.9-End-to-End-Repair-RC1**.
- **519 passing tests**, including the exact locked 300-test suite with all 35 locked test source files unchanged. The supplementary player-drawer test now waits for the ListView’s posted layout before asserting its playing-row view; no product test contract or app behavior was weakened.
- **20 protected reference images byte-identical** to the approved parent.
- The older supplementary tests only adapt assumptions explicitly superseded by approved later behavior; the adaptation list and all test XML are retained with the build evidence.
- APK SHA-256: `cf7aedadded921e5ddc023ba08161638d8f6207dd7002f3258daf178073679cd`.
- Release certificate SHA-256: `d7adeb68e9341596a02bd3262b737a0f45fc6e771ed7e60285437e833b58c6d7`, matching the approved baseline.
- Native engine SHA-256: `c7976ce0adb45b9264f2092a27111be4e05bde4220be2b26b1ea0e2cc74f1e2d`.

The exact signed APK passed **21 of 21 Android runtime scenarios** on API 30, including installation over 2103278, launch, all five embedded view modes, Quick Peek, pause/resume, player menus, Multi-View 2/3/4, fullscreen return, actual Android PiP/background return, resizing, themes, rapid retuning, favorites/search, live rewind and network recovery, movie/episode playback, audio/CC, Smart Return and activity recreation. The Channels drawer scenario additionally measured the footer hint above the current navigation-safe boundary. The final build run skipped the emulator job because its only subsequent changes were test/workflow files; exact APK hash equality proves the tested package matches.

All **31 main-player composed-screen crop checks** measured zero black boundary pixels in the generated bright fixtures. The independent Quick Peek screenshot also had zero black boundary pixels and 58 sampled light grid pixels, confirming visible decoded content. Three pause/resume cycles had zero position movement during each 600 ms paused interval. These measurements describe the exercised fixtures and timings, not every possible provider scene or transition.

The emulator run retained 74 screenshots and per-scenario memory snapshots. Its log contained no `FATAL EXCEPTION`, application ANR, fatal native signal or out-of-memory marker. Snapshot PSS ranged from 87,199 to 377,433 KB; that is not a leak test or a physical-device performance/thermal result. Exact results and artifact references are in [the runtime verification JSON](cobra-2103279-runtime-verification.json).

The runtime harness installs the exact release-signed arm64 APK on Android API 30 with ARM translation, updates it over the signed 2103278 baseline, and exercises real MediaCodec playback through generated HTTP/M3U/Xtream fixtures. It invokes actual controls and callbacks, includes native pointer events for the scrubber, and saves composed-screen screenshots. Some setup/navigation uses reflection into the existing application, so it does not prove that every possible touch, focus or accessibility path has been exercised.

An earlier [diagnostic run](https://github.com/mahfouzhassine8-ops/project-infinity/actions/runs/36803508172) passed 20 of 21 scenarios but failed a position check sampled immediately after Pause. The test now waits for a bounded playback-thread acknowledgement before checking that position stays fixed for 600 ms, then verifies Resume advances it. The following [pause diagnostic run](https://github.com/mahfouzhassine8-ops/project-infinity/actions/runs/36804839174) passed all 21 scenarios on the **byte-identical APK**, with zero position movement in all three pause intervals. No application playback code was changed to obtain this result. Those failed and passing records remain available. The drawer-inset candidate’s runtime run also passed 21/21; its overall first two CI attempts were blocked by the supplementary ListView test’s immediate-attachment assumption, which the final passing test run corrected. The app source and APK did not change in that test-only correction.

Quick Peek verification also requires the decoded fixture grid to be visible in the composed screenshot, with filled edges and the correct live status. A first-frame decoder callback alone is not counted as visible playback.

## Scope and remaining acceptance

| User acceptance requirement | Evidence and remaining work |
| --- | --- |
| Clean build, packaging and signing | Verified. Exact APK and signing reports retained. |
| Install/update and Cobra launch | Android framework install-over-parent and launch are exercised. Physical Samsung update with the user's existing data remains required. |
| Representative provider/content playback | Real network-delivered generated M3U and Xtream-compatible content is exercised. User-provider authentication, catalog formats, live channels and protected feeds remain unverified. |
| Mini-player Fill at runtime | Composed-screen pixels and visual screenshots cover five modes, four source aspect ratios and encoded padding. Physical channels previously showing bars still need confirmation. Conservative encoded-border detection intentionally avoids uncertain scenes and cannot promise removal of all unusual baked-in padding. |
| Major view modes and player controls | Five modes, pause/resume, channel switching, transport, menus, favorites, search, audio/subtitles and Smart Return are covered by runtime and regression evidence. Exhaustive touch/focus coverage of every control remains open. |
| Multi-View | Real 2/3/4-player decoding, pane replacement, peer preservation, audio-source changes and fullscreen return are exercised. Samsung decoder capacity, physical rotation/folding, Multi-View PiP return and sustained four-stream operation remain open. |
| PiP and background return | Real Android PiP and HOME/foreground transitions are exercised with background playback enabled and disabled. Samsung-specific behavior and process-pressure recovery remain open. |
| Fold and resize | Several Android window/display sizes and native layout tests are exercised. This is not a physical fold/unfold, inner/cover switch, Samsung split-screen or pop-up-window test. |
| Dark/Light UI | Light, Dark and OLED runtime captures plus protected renders are checked. Physical display appearance and all secondary screens under every theme remain open. |
| Navigation and Smart Return | Movie and episode playback return to their owning sections; stale movie responses, drawer ownership and activity recreation are checked. Exhaustive back-gesture/hardware-back combinations remain open. |
| Crash/ANR/performance | Runtime logs and per-scenario process memory snapshots are collected. They do not establish long-term leak freedom, real-device frame rate, startup performance, battery use or thermals. |
| Sports and external integrations | Existing Sports/resolver/provider regression suites pass. Authenticated Sports action-to-playback, recording destinations and file permissions, trailers/YouTube handoff and Cast/Route hardware remain unverified. Opening a screen is not counted as successful end-to-end integration. |
| Settings/subtitles/audio | Real tracks, CC state, VOD seek and selected persisted settings are exercised; broader policies are regression-tested. Every preference after process restart, every language/track format, and physical-call interruption/resume remain open. |
| Broken features repaired | Confirmed reproducible defects above have bounded repairs. Unavailable external/device checks are explicitly unverified, not silently marked working or removed. |

No physical Galaxy Fold, authenticated user providers, incoming telephone calls, recording destination or external casting hardware was available to this run. Those requirements cannot be honestly reported as passed from emulator or unit-test evidence. The candidate should receive physical Fold/provider acceptance before any lock or promotion.
