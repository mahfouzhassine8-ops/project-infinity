# Infinity whole-stack stability certification

This branch is a read-only-first stabilization lane. It must not silently replace locked artifacts or trigger a full Kodi rebuild merely to run the stability audit.

## Protected anchors

- Native/APK source anchor: Candidate 2 commit `080545faf884741c260d0a4a2c4810a7a788127b`.
- Skin anchor: locked `skin.infinity.diggz` 1.0.5.133, SHA-256 `4bd4cda3335b233f19b3712e9fd65c56c67a91bd45708cdc2f147b2a0b6a4abe`.
- Live anchor: locked `script.infinity.live` 0.1.12, SHA-256 `e2460306c1e8c1171a997a8969a8c85a5198f80389a8174a3941d5e6ba3c1f41`.

## Certification zones

1. Native/APK: preflight, compile, lifecycle, Fold/rotation/PiP/Multi-View, packaging, signer and update identity.
2. Skin: XML/control/action integrity, responsive profiles, Light/Dark/OLED, Home/drawer/player/browser contracts.
3. First-party companions: Command Center, Health Center, Compatibility Guard, Support Exporter, Live, Audio Policy, Refresh Controller and Cobra Theme.
4. Provider/helper compatibility: Umbrella, Fen Light, POV, The Crew, Seren, Ghost, Essential, B&W Movies, Halcyon, Absolution, TMDb Helper and Playlist Browser.
5. Playback/runtime: start/stop/seek/repeat, PythonInvoker teardown, MediaCodec black-video boundary, audio/subtitle tracks, provider handoff and crash evidence.
6. Long-run/device: repeated launch/return, fold/unfold, background/foreground, network loss/recovery and soak testing.

## Current red gates

The initial audit is expected to report source/provenance drift rather than rewrite it:

- Candidate 2 repository Live source is older than the locked 0.1.12 package.
- Candidate 2 repository Support Exporter source is older than the 0.3.0 reference package.
- Candidate 2 repository Compatibility Guard source is older than the 0.8.0 clean-core target.
- Legacy Compatibility Guard tests/source still encode player/theme file reassertion and must not be accepted as the clean-core 0.8.0 contract.
- Command Center 0.3.6, Health Center 2.5.2 and the canonical clean-core companion package bytes are external to Candidate 2 and must be reconciled against the current `skin.infinity.diggz` identity before whole-stack certification.
- Candidate 2 native compile is green, but packaging/signing remains a separate release gate.

## Audit modes

`python3 scripts/infinity_stability_audit.py` produces a report without forcing a red CI result for known provenance blockers. Use `--strict` only when running a certification attempt; blockers then fail the run.

Supplying the locked skin locally adds artifact-level checks:

`python3 scripts/infinity_stability_audit.py --skin-zip /path/to/locked-skin.zip --strict`

The audit never modifies the supplied ZIP.

## Promotion rule

Do not promote a new Infinity baseline until static gates are green, exact artifacts are pinned, device acceptance covers every required zone, and the final adversarial review finds no unresolved release blocker. Pro/Extra High reasoning is reserved for that final adversarial certification pass after the known source/provenance and packaging gates have been reconciled.
