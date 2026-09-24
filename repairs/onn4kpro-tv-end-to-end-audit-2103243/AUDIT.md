# Infinity / Cobra TV RC23 — preservation-first end-to-end audit

## Scope and evidence rules

Target: onn 4K Pro ARMv7 Android TV. Baseline: `locked-infinity-cobra-2103242-onn4kpro-tv-final-product-audit-passed`, commit `f95e84676932470ec6093bf6408a920d40239702`. All work is on `infinity-cobra-2103243-onn4kpro-tv-end-to-end-audit-rc23`.

This is the existing product refined, not redesigned. No new visible settings, screens, toggles, custom keyboard, navigation destinations or expensive effects. Movies, TV Shows and search are included, not excluded from a Live TV-only pass.

The baseline snapshot was reconstructed from the exact committed RC22 recipe and checked against its source receipt. The APK rollback SHA is `2e0480ae719a319125ad9482840439e3e8406fe47c8181424469a719b44b9754`. A branch named locked is not by itself server-side branch protection; this audit does not claim it enabled repository protection rules.

**Evidence levels are distinct:** source review, source preservation, executable Android-view regression tests, and physical-device/live-provider validation. None substitutes for the others. CI success is not shipping certification. The final Android XML/JSON reports, not this prose, determine which tests passed.

## Reproduced baseline defects

Run `36027475388`, attempt 2, executed 20 regression cases against untouched reconstructed RC22. Nine cases passed; eleven failed with their specific defect assertions. No setup errors were accepted as bug reproductions. The first attempt had a GitHub artifact-service failure; that was infrastructure, not an application defect.

1. A delayed directory focus callback could take focus behind Power.
2. Closing Power could schedule focus restoration that steals focus from a newly opened modal.
3. The transient-menu router ignored explicit next-focus links, including the Channel Playback links added in RC21.
4. The blanket 120ms Left/Right cooldown discarded separate legitimate fast presses.
5. A held Play/Pause key could toggle twice despite the 220ms debounce.
6. RC21's generic non-user-pause recovery automatically resumed a system/audio-focus pause.
7. The dot treated playWhenReady as actual playback and could indicate playing while buffering.
8. IME Search could hand focus off before new results existed; delayed filtering then removed the focused result.
9. Fixed search-card height was smaller than the poster, title, metadata and padding combined.
10. Repeated search refreshes retained discarded view trees through the strong trim registry.
11. Delayed metadata/details completion could open a details panel after navigation to another section.

Additional code-reviewed hazards guarded in the same diff: Multi-View picker callbacks acting on replaced adapters, stale person/collection metadata completion, background library iteration over a mutable source list, oversized artwork decoding/cache retention, and collection card clipping. Two test cases (stale Multi-View focus and inactivity refresh) already passed the controlled baseline scenario; they are preservation checks, not claimed baseline reproductions.

The user's last apparent random-pause incident was withdrawn as an intentional pause. This audit does not reinterpret it as a confirmed network/provider stall.

## Corrections and preservation

### Remote, menus, Power, focus and Back

The topmost modal receives remote input before the drawer, guide or fullscreen player underneath it. Custom-router-consumed key-down events are paired with their key-up and repeats by key/down-time/device identity. Native View activation and long-press handling remain available; this is not a global replacement of Select behavior.

Left/Right edge selection uses press identity rather than an inter-press cooldown. Right-as-Select remains scoped to the approved Live TV drawer/directory paths; Movies/Shows rails, keyboard cursor movement, EPG and ordinary horizontal focus are not remapped globally.

Explicit directional links are followed inside the active modal before geometric fallback. Posted focus restores validate active owner, attachment, enabled state, source adapter and/or navigation generation. Power restores valid previous focus without taking over newer screens. Menu closure takes priority over fullscreen Back. Multi-View fullscreen retains its existing return path after the UI-dismissal stage.

The RC21 automatic chrome-hide policy and visual design are retained. Relevant player key interaction refreshes its existing inactivity deadline. No new timeout setting is added.

### Player and truthful state

A generic non-user pause is now recorded, not automatically converted into a new user Play request. Existing explicit user Play and existing audio-focus/lifecycle policy remain responsible for legitimate resumption. User Pause must stay paused. The player, media construction, decoder bindings, provider fallback and timeshift engines are not rewritten.

The existing dot renderer, pulse cadence, colors and focus presentation are preserved. Its state input now uses actual playback rather than only requested playback. Buffering, paused, waiting, ended and unavailable are distinguished by the existing state path. No duplicate PLAYING label is restored to the grid row.

Ordinary buffering remains observation-only. No new media prepare/restart, forced live-edge seek, media-item replacement or video-surface recreation is introduced as a buffer workaround.

### Movies, TV Shows and search

The cinematic hero, Popular Now, Recent Releases, Genres, details, actions and persistent section ownership remain. The one inline field still reads `Type a title or narrow by genre`; Android TV supplies the keyboard. Exact-title, prefix, contained-title and metadata ranking remains unchanged, as does the 150ms live filtering budget and 35-result cap.

IME submission flushes the current filter before a guarded post-layout focus handoff. Detached fields cancel pending refreshes. Search cards wrap their actual contents; collection cells get sufficient height for the existing content, and local focus scaling is not clipped. These are sizing corrections, not a poster/layout redesign.

Discarded search/default content is removed from the trim registry; registry keys are weak. Metadata completion is tied to the current navigation request and, for details, the source/profile identity. Workers use a source-list snapshot rather than iterating the UI-owned mutable list.

Artwork input is bounded to 4MiB even when Content-Length is unknown. Bounds are read before bitmap decoding, sampling limits the decoded longest edge, the existing small entry cap is supplemented by a 16MiB cache budget, and deferred work holds a weak ImageView reference. Cached bitmaps still in use are not forcibly recycled. These limits are source-checked, not presented as measured onn memory/FPS improvements.

### Multi-View

Picker selection callbacks check adapter identity, item position/id and attachment, and pending activation is bounded. Healthy stream ownership, 2/3/4 layouts, audio selection, fullscreen promotion/return and the 2-to-1 survivor implementation remain unchanged. Real concurrent decoders are not exercised by a mock media object.

## Coverage matrix

| Area | Review / executable evidence | Remaining physical acceptance |
|---|---|---|
| Launch / Choose Experience / Cobra handoff | Existing launcher/manifest/entry behavior and sources preserved; no new destinations | Cold/warm launch, handoff to Infinity, actual native startup |
| Drawer, groups, channel directory, grid | Routing, callback ownership and repeat handling reviewed; rapid separate edge events and 12,000-channel virtualized UI tested | Actual remote repetition, 50 navigation cycles, crash/ANR observation |
| Power and other menus | Actual Android view tests for modal ownership, stale restore and Cancel; actions retained | Switch to Infinity, Exit, reopening in all sections |
| Channel Playback | Explicit-link routing test plus unchanged row/action construction | Each displayed row in both directions, no two-press hiccup |
| Player chrome and Back | Actual Activity/View tests for hide-before-exit, pause and timeout interaction | Auto-fade timing and submenu hierarchy on real remote |
| Playback / timeshift / audio | Playback inner classes and media/session methods protected; controlled buffering watchdog and pause-state tests | Real streams, rewind/live edge, network loss, audio-focus/lifecycle |
| Current-playing indicator | Controlled READY/buffering/suppression/end state tests; renderer byte-identical | Pulse appearance, channel handoff and theme colors |
| Multi-View | Adapter callback review and controlled selection test; engine classes preserved | 2/3/4 live streams, audio ownership, cancel/failure, fullscreen return |
| Movies / Shows | Actual landing and section-owner tests, guarded delayed details, card measurement | Poster artwork, details/trailers/episodes, playback/return, remote rails |
| Search | Actual text edits, IME action, focus, ranking, reset and trim-retention tests | Real Android TV keyboard presentation and large provider catalogs |
| Settings / subtitles / sources / recording | Existing functionality and non-target sources preserved; no controls deleted or renamed | All settings actions, language/caption choices, provider/file permissions, recording |
| UI polish | Measured search-card geometry, collection sizing/focus boundaries, established design preserved | 1080p/4K, font scaling, overscan, readability and animation feel |
| Performance | 12,000-channel virtualization and repeated search view-retention checks; bounded artwork source changes | Real startup/latency/FPS/memory measurements and extended-use soak |
| Lifecycle / async state | Navigation generations, modal focus and source snapshot reviewed/tested where controlled | Sleep/wake, background/foreground, actual native surfaces |
| Packaging / integrity | Mandatory JNI, resource-ID, byte-preserved payload, package, signer, zipalign gates | Install/upgrade and actual device operation |

## Preservation proof and acceptance

`source-preservation.json` inventories every original Activity declaration using the Java parser. The allowed diff is 29 original declarations plus 13 additions, with no original declaration removed. Every other original declaration, including all original nested playback/timeshift classes and the dot renderer, must retain its source hash. The complete reconstructed source-file inventory permits changes only to the Activity and version identity in build.gradle.

Packaging uses the exact signed RC22 APK as the payload base. Only compiled Android DEX and the versioned manifest are substituted. Native libraries, assets and compiled Android resources must compare byte-for-byte; JNI native declarations and resource IDs must match. The permanent signer/package and ARMv7-only payload are mandatory.

RC23 is publishable only after all 20 candidate Android-view tests pass with no skips and every source/package gate succeeds. Those tests use production Android views/dispatch with controlled data and a Media3 proxy; they are not a physical TV, decoder or network simulation.

**Physical onn 4K Pro, live-provider, long-session, sleep/wake, true multi-decoder and final visual acceptance remain pending.** No blanket production-ready or zero-bugs claim is made. Preserve RC22 until the user separately accepts and locks a candidate.
