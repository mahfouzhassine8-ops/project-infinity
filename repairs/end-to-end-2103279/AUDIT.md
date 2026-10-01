# Cobra 2103279 preservation audit

Status: forward candidate; acceptance is still in progress. Do not lock from CI alone.

The approved parent is `41f08774a8b908d60c0f9e6647497e40d6bbe081`, Cobra 2103278. The locked branch is unchanged. Every build first verifies the archived source hash and creates a Git rollback bundle. The parent APK supplies preserved binary assets/native libraries, never replacement source.

## Repairs

* Quick Peek used its own Fit transform and bypassed the earlier embedded Fill policy. It now shares the proportional Fill calculation and refits after the first frame, surface changes, and layout changes.
* The main binding now reapplies its transform on same-surface attachment and first-frame/surface events, and retains valid video dimensions through transient UNKNOWN metadata.
* Real Android decoding of the locked APK reproduced encoded pillarboxing: 45.45% of the measured boundary remained black in the padded fixture. A bounded embedded-only detector removes persistent symmetric black padding with proportional additional crop. Dark scenes and asymmetric shadows do not establish a crop.
* The detector reuses one 96×64 bitmap and matrix/pixel buffers. It requires repeated evidence, samples initially at 200 ms and then every two seconds, suspends when paused/hidden/backgrounded, and releases callbacks/buffers with its binding. Fullscreen, PiP and Multi-View retain their existing scaling policies. Failed captures restore the previous transform and stop probing that session.
* Delayed movie metadata is now gated by the current navigation request and profile, preventing stale results from replacing a newer drawer destination.
* Display help text now describes the actual embedded center-crop behavior.

The ambient implementation and all other unmodified shell sources are checked byte-for-byte against the parent. Ambient captures the displayed texture, including its current crop.

## Evidence and limits

| Area | Evidence collected or scheduled | Acceptance limit |
|---|---|---|
| Installation and launch | Exact signed arm64 APK installed on API 30 Google APIs emulator with ARM translation; update-over-parent workflow | Physical Samsung update still required |
| Mini-player | Real HTTP clips in 16:9, 4:3, portrait, odd aspect and encoded padding; five modes; TextureView pixel captures | Representative user channels and protected feeds still required |
| Player / Multi-View | Real decoders, visible player callbacks, 2/3/4 panes, audio selection, fullscreen handoffs | Physical decoder capacity, phone calls and Samsung lifecycle still required |
| Movies / Shows / audio / CC | Generated Xtream-compatible HTTP provider, actual video/audio/text tracks and return navigation | User-provider authentication, catalog quirks and supported languages still required |
| Background / PiP / recreation | Android framework transitions against the installed signed product | Samsung pop-up/PiP and process pressure still required |
| Responsive / visuals | Native screenshots and multiple window sizes; Light/Dark/OLED; protected reference renders | Physical Fold inner/cover/fold transitions and thermals still required |
| Sports, providers, timeshift, rewind, settings, navigation | Locked regression suite plus historical feature-policy/integration suites | Authenticated services, recording destinations, external YouTube/trailer apps, long-running provider-specific TS/network recovery still require representative integration testing |

The HTTP fixtures are generated test content, not proof that every external provider or add-on works. Emulator captures are not physical Fold acceptance.

## Regression policy

The locked 300-test suite is copied unchanged. Older supplementary tests are adapted only where approved later changes superseded their assumptions: non-IDR compatibility, Smart Return's enabled default, menu deduplication, Sports navigation, and the current glass chooser/spatial ambient renderer. The adaptation list is saved with build evidence; current locked visual and ambient tests remain authoritative. Missing branding resources and incomplete player-session fixtures are test setup corrections, not product rollbacks.

All failures, screenshots, test XML, signatures, hashes and reconstructed source are retained by CI, including failed diagnostic runs. A successful package is not a completed audit.
