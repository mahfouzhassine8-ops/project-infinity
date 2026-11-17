# Infinity512 — Cast correction internal QA

Install the original-signed2103512 candidate over the existing Infinity installation. Keep the same profile. Do not uninstall or clear data. The matching original-signed2103513 forward recovery restores signed2103510 functionality at a higher version code. Recovery is optional; it is not a second test candidate.

This Cast-only correction preserves the signed2103510 foundation, Kodi engine, Cobra2103445, providers, Search, tracking, saved progress, settings, Video Lock, UI and shutdown safeguards. It repairs reproduced HEVC RADL fragment ownership, valid bounded in-band HEVC configuration admission, and stale Cast handoff callbacks. Codec declarations are not fabricated, and source safety budgets remain unchanged. Provider credentials are not exposed to the receiver.

Engineering verification includes2571 sanitized CSD checks, lossless source-video/timestamp checks, clean independent fragment decoding, unchanged high-bitrate control output, exact Cast component/API checks, ARM64 JNI integration, actual Android MediaCodec/EGL720p conversion with synchronized AAC, HLS playback/seeking and cancellation with zero remaining native contexts. The existing native engine and verified production DEX were reused where inputs were unchanged.

Actual Android conversion used a genuinely encoded Main8 RADL source on the disposable emulator's bounded software backend. Both available emulator HEVC decoders rejected Main10 Level5.1. That Main10 playback failure is retained; it is not a pass and does not establish the Fold's capabilities. Genuine Main10 native HTTP/range delivery, video packets/timestamps, and strict independent/combined output decoding passed. Sustained Main10 hardware conversion, thermal behavior and actual television video/audio remain unverified.

The owner's exact source hvcC/NALs and detailed receiver decoder error were unavailable. The reproduced supported-source defects are proven; attribution of the original4K incident to that exact source structure is not. Unknown receiver capability remains unverified, never assumed compatible. The earlier two failed CI runs remain documented separately from the successful corrected integration run.

Use one consolidated Fold/receiver acceptance session: compatible4K and Nest Hub casting, actual video with sound, pause/resume/seek, Return to Phone, cancellation and normal Exit/relaunch with retained data. No new diagnostic export or repeat test of an unchanged build is requested. Physical success and final baseline acceptance belong to the owner; this QA release does not promote a baseline automatically.

Exact APK checksums, signing and install-over results accompany the published artifacts. The signing certificate must remain d7adeb68e9341596a02bd3262b737a0f45fc6e771ed7e60285437e833b58c6d7.
