# Cobra 2103199 — repair scope and evidence boundaries

Protected delivered baseline: 2103197, commit `b5fa21731a1662cc7206ac6dc45cb6d6682612cd`, APK SHA-256 `b1197aae8456940210a7c99dbd20e849fb8148ebe3bc673ceb56ac1b7c6c660c`.

The exact signed APK, complete 206-file Android source/package snapshot, original receipts, repository recipes and restore instructions were preserved before edits. All 17 source hashes recorded by the delivered build match. Device-private user data and the private signing key are not part of that archive. Existing 2103198 (`e6b4c0371aacc358ebd7eaff4e79b1bfc1de640b`) is used only as the immediate manifest/metadata parent; its DEX and runtime are byte-identical to 2103197.

## Surgical repair scope

- Refresh the existing timeshift scrubber and rewind enablement as playback advances; preserve user dragging and paused intent through activation/recovery/direct fallback.
- Cancel a stopped timeshift provider request and keep segment closure on its ingest thread; wait for that owner only on the cleanup worker. Actual-method tests reproduce blocked reads and a stop/write race in the baseline.
- Resolve aspect selection from the current channel/player binding through resize/video callbacks, match untouched Custom defaults to the displayed 100% values, and expose actual transform/viewport observations in existing diagnostics.
- Repair existing sheet contrast, interrupted focus/entry animations, profile scrolling, active-session subtitle visibility, and human-visible escaped-newline strings. Additional scoped navigation/async-input repairs are recorded in the committed module and regression tests.
- Redact scheme-less provider socket endpoints in exported failures, and disclose bounded history/attachment age without claiming old logs are current.
- Follow HLS master playlists and redirected relative references before recording TS media, preserve the provider entry URL between polls, and honor cooperative cancellation. Unsupported encrypted/map/range/separate-audio formats use the existing error path instead of producing misleading recordings.
- Restrict the existing background-mode activity to Cobra's own UID, preserving its action contract. Bound and close the legacy YTDL provider's redirect probes and streaming resources above the native engine.

No new controls, settings, player options, menus or features. No mode redesign, buffer-policy change, network-family change, timestamp rewriting, timeshift-architecture replacement, theme ZIP change or Kodi engine rebuild. The same permanent signer and package identity are required; native libraries/assets/resources must match the protected APK byte-for-byte.

## Evidence standard

Source inspection follows each owner's controls, persistence, runtime code and callback lifecycle. Host tests execute extracted production methods with disclosed fake collaborators and include baseline failures. Android/Robolectric tests exercise actual view trees, Matrix transforms, focus/scroll/caption state and existing inherited contracts. Signature/APK verification is separate. None establishes physical Fold rendering, decoder performance, live-provider behavior, PiP/SystemUI behavior or real installed-update data retention.

The inherited 265 Android cases remain mandatory. New behavioral suites and host evidence are separately enumerated in ACCEPTANCE.json and the evidence archive. Tests that only assert a selected aspect integer are not accepted as display coverage; every existing aspect mode is exercised through actual TextureView transform geometry. Physical pixel output remains a device gate.

## Buffering findings

Sixteen supplied diagnostic archives show multiple failure classes. In one problem-channel session media timestamps advance about 0.559 seconds per second while transport bytes arrive regularly; later the same channel receives about 1.033 seconds per second with larger upstream pauses. Another capture fails to connect before any frame. These observations do not justify a universal buffer tweak or a native renderer rewrite. Later improvement is confounded by changed delivery conditions. Timestamp rewriting remains disabled. The available captures do not exercise local HLS rewind, so the reported rewind defect cannot be declared physically resolved from those ZIPs.

## Open findings and limits

- Real-device acceptance in DEVICE-TEST.md remains mandatory; candidate_locked and physical_device_verified stay false.
- Source Change colour persists metadata but has no identified visible consumer. Its existing control is preserved; no new decoration is invented.
- Existing `.file`/`.media`/`.ytdl` provider exposure requires compatibility-aware review. `.file` serves search/recommendation imagery; blindly disabling provider exports would break integrations. Source establishes an inherited authorization gap; cross-app reachable data has not been physically tested. Provider exports are preserved; the same-UID background-control activity is made private.
- Recording cancellation is cooperative between reads; an already-blocked read can still wait for the existing HLS/direct timeout. This is distinct from the timeshift Call-cancellation repair.
- Preserved native libraries use 4 KiB ELF alignment. 16 KiB native-device compatibility is not established; the engine is not rebuilt for a hypothetical target change.
- Local HLS and progressive TS extractor configuration differ; no supplied raw-media replay proves that this difference causes the user's rewind problem. This is recorded rather than applying an unproven parser change.
- Source inventories identify further performance/coverage risks, including large eager VOD lists, theme-driven geometry, bounded diagnostics history and external provider/SAF/recording integrations. No crash-free or exhaustive physical-product claim is made from compile/test success.

This candidate preserves Cobra and repairs demonstrated defects. It is not a final shipping acceptance or a new baseline lock.
