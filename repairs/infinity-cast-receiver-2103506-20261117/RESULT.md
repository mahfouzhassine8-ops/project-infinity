# Infinity506 receiver compatibility — incomplete, no successor APK

Foundation is exact signed2103506 (`2d0f6fa80926243934270816fdfc5f83e7ba5f421fd7882a352686999a9eae1d`);2103504 remains protected. No rollback, registry update, version reservation, owner-data change, baseline promotion or successor signing occurred.

## Established receiver mismatch

Google's published Nest Hub formats list H264 High≤L4.1 at720p60, and Nest Hub Max at720p30; neither lists HEVC. Ultra and documented4K Google receivers list HEVC Main/Main10≤L5.1. Thus successful AAC conversion and HTTP200 cannot establish that the reported HEVC movie is compatible with a Nest Hub. ReceiverERROR4 alone still does not uniquely identify every underlying decoder/delivery error.

The existing sender checked VIDEO_OUT, which is not a codec capability. SDK model information exists; CAF canDisplayType runs on the receiver and is not a general DefaultMediaReceiver sender-side capability query.

## Implemented source work (not shipped)

- `InfinityCastReceiverPolicy.java`: documented exact model profiles and typed codec/profile/level/dimensions/rate decisions. KnownHub HEVC or over-limit video requires720p hardware AVC conversion. Documented4K HEVC copy remains eligible within limits. Unknown models keep the existing direct attempt explicitly UNVERIFIED; no substring/friendly-name inference or fabricated support claim.
- `InfinityCastSession.java` / `InfinityCastRelay.java`: pass the selected SDK model to the Cast-owned MKV admission check; reject a known incompatible path before LOAD with an explicit hardware-conversion limitation. No phone/provider/tracking/shutdown code was altered.
- `InfinityCastRemux.java` / Cast-only `InfinityCastRemux.cpp`: carry actual source profile, level, width, height, average frame rate and color-transfer facts. Main10 alone is not HDR. Unspecified transfer is not proof of SDR. Fragment generation, video packets and the existing AAC adapter are unchanged.

This is receiver selection and MKV admission, not a video transcoder. The knownHub branch cannot yet make this HEVC movie play. Other existing transport paths were not represented as fully capability-validated.

Astra corrected two issues before final review: independently known violations now override missing source facts; the comment correctly describes existing transactional pause/return. The existing sender can pause the phone when receiver readiness is PAUSED, before PLAYING; that handoff was preserved, not silently redesigned.

## Actual engineering evidence

-43 host policy checks pass, including known limits with missing frame rate/profile,4K copy, ambiguous models, Main10 versus HDR, and Hub versus Max frame-rate limits.
- AffectedCast Java compiles against retained realCast21.3/MediaRouter1.3/providedHTTP APIs. No productionDEX rebuild.
- Actual host-native Main and Main10/L153 metadata extraction passes with AAC retained.
- Changed standaloneCast native metadata library compiled/linked for AndroidARM64 in44022664950, maintaining seven JNI exports and four dependencies, reusing the unchanged506 engine. New library hash`8f4317d203300b8dff10960a8b05c01ece6b5ee883de13c8e4c17e8ba36f4a73`. This is compile/ABI evidence, not hardwarevideo playback. The same run's subsequent CI-only APK installation failed; precise command output was omitted by the first wrapper, so no hardware conclusion was drawn from it. Storage/alignment preflight and error capture were corrected. Passing native compilation evidence was reused.
- Android inventory44023632394 actually passes against the original506 ARM64 engine under native translation. AAC encoder exists. FFmpeg h264/hevc_mediacodec encoders and hevc_mediacodec decoder do not. Android's advertised goldfish HEVC hardware decoder rejects requested Main10/L5.1/3840x2160/24; there is no hardwareAVC encoder in this image, only softwareAVC encoding. No owner app or profile was launched. Owned codec count ends at0.

Receipts and artifact hashes are in this directory. No Kodi engine rebuild, new global FFmpeg setup, production dependency replacement, or CPU4K video conversion was performed.

## Exact remaining blocker

The required Cast-owned HEVC decoder→surface/GPU scaler→H264720 encoder→fragmented-MP4 integration is **unimplemented and unqualified**. The available verified Android environment lacks the hardware codec pair to exercise it, and the unchanged engine supplies no ready FFmpeg MediaCodec wrappers. A separate Android MediaCodec implementation may be possible; these findings do **not** establish that the physical Fold is incapable.

Actual decoder/encoder operation while local playback is active, source-specific HDR→SDR handling, sustained throughput/thermal behavior, stable initialization/keyframes/adjacent fragments, video/AAC synchronization, random seeking, cancellation and converted-video Return to Phone remain unverified. The emulator's nominal thermal readings are not physical thermal evidence. Codec inventory/configure/start cannot be relabeled as passing those gates.

Per the owner's instruction, no software-only4K fallback or finished-looking successor APK is being shipped. A hardware-backed Android execution path and its end-to-end qualification are required before release. No new owner capture or repeated playback test was requested.

## Preservation and independent review

Astra independently verified the source corrections, unchanged AAC adapter, actual ARM64 receipt, actual Android inventory and accurate limitation. Approval covers bounded policy/inventory work and this blocker report, not finished casting or device acceptance. Source delta stays in the Cast allowlist plus scoped tests/key-free CI routing; Cobra, core engine, providers, Search, Watchlist, Continue Playing, UI/VideoLock, networking, settings and shutdown remain untouched. There is no successorAPK to claim as passed in a member-preservation comparison.

Branch: `work/infinity-2103506-receiver-compatibility-20261117`.
