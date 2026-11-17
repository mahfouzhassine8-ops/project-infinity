# Infinity2103508 internal Cast hardware QA

Install `Infinity-2103508-Combined-Original-Signer.apk` over the existing Infinity app. Do not uninstall or clear data. This is an experimental QA candidate; accepted baselines are not promoted.

`Infinity-2103509-Combined-Original-Signer.apk` is forward recovery: it restores the exact signed2103506 content with only a higher versionCode and Infinity version label. Install it only if recovery is needed. Protected2103504 and all historical artifacts remain unchanged.

## Included

Cast-owned receiver-aware HEVC→H264 hardware conversion using Android MediaCodec and Surface/EGL, retaining the existing MKV demuxer and continuous AAC converter. Compatible4K receivers keep direct HEVC playback. New H264 delivery targets720p and at most30fps; no CPU4K conversion is enabled. The original Kodi engine is reused.

The actual device must expose suitable hardware codecs, profile/level/raster/rate support, concurrent configuration and sufficient measured output throughput. Unsupported or insufficient-performance conversion fails explicitly before transfer while phone playback remains available. SDR709 is supported. HDR→SDR is attempted only for confirmed source HDR metadata and supported decoder tone mapping with verified SDR output; Main10 alone is not treated as HDR. Unknown color contracts, unsupported high-tier inputs or changed encoder configuration fail closed.

## Engineering evidence

Production Cast DEX and Cast ARM64 bridge exercised through the authenticated private Relay: real Android HLS video/audio decode and advancement after seeking; cancellation120ms; zero native contexts after cleanup. Actual output analysis verified original video PTS, monotonic DTS, noBframes, independently decodable adjacent fragments, and original continuous-AAC packet data/PTS/DTS equality. Exact signed-payload and PackageManager receipts accompany these installers.

The emulator uses a bounded test-only software codec backend to verify logic and media correctness. That backend is unavailable to the Infinity application package. It does not qualify Galaxy Fold hardware, concurrent phone decoding, sustained thermal behavior or HDR tone mapping.

## Owner acceptance still required

One consolidated Galaxy Fold/TV session: provider-movie video and sound, supported receiver selection, pause/resume/seek, cancellation and Return to Phone with position/tracking retained. Physical hardware throughput, receiver playback and actual phone handoff have not been claimed successful. Normal shutdown remains an owner acceptance check; no shutdown test or shutdown source change was included in this Cast task.

## Preservation

Candidate changes only Cast classes6.dex, libinfinitycastremux.so, typed package version and Infinity version label. All remaining7773 unsigned APK members remain byte-identical to signed2103506, including Cobra2103445, Kodi, otherDEX, skin/add-ons/resources and all nonCast functionality. Recovery changes only the two version metadata members. No user profiles, databases, settings, saved history, providers or data schemas are accessed, reset or migrated.
