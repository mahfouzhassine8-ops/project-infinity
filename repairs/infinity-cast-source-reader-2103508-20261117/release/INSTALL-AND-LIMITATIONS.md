# Infinity 2103510 bounded Cast source-reader QA

Install 2103510 over the existing Infinity installation. Do not uninstall, clear data or reset the profile. This is internal QA; owner Fold/TV acceptance remains pending.

This candidate derives from the exact original-signed 2103508 APK (SHA-256 9de2cb84b8c9c58e751b3fc6691337d31da224c62884383ed1fed98975782a16). It corrects reproduced MKV source-read amplification during canonical AAC preparation and video seeking. It preserves existing AAC encoder/sample math, hardware-video pipeline, receiver compatibility policy and authenticated private delivery.

The former 32 MiB request quota could be exhausted by repeated interleaved-source scans even when the emitted video fragment was small. Verified cue seeking reduces scanning; a checked per-request allowance accounts for uncached AAC passes and actual cue spans. The allowance remains between 32 MiB and 128 MiB, rejects excessive working sets, is never replenished by seeking and does not allocate a corresponding buffer. The existing 15-second deadline, packet limit, 8 MiB output bound and cancellation guards remain. Numeric diagnostics report fragment, consumption, seeks, ranges, phase and budget exhaustion without source URLs or credentials.

Engineering evidence includes sequential/cold/random seeking, deterministic regeneration, high-bitrate sources, original32MiB exhaustion, ceiling rejection, exact video packet/timestamps, AAC alignment, real ARM64 linking, actual Android private-relay/HLS continuation and seeking, and prompt cancellation with zero remaining native contexts. The original Android workflow 44067382846 failed its JSON result transport after executing the tests; this remains a recorded failure. Read-only recovery 44071299408 validated complete mandatory results and retained media without rebuilding or rerunning the application.

The owner incident selected receiver_capability_unknown direct playback. Neither that incident nor these reader tests establish hardware video conversion, receiver capability or sustained physical TV performance. Original hardware capability safeguards remain unchanged. Source throughput, sustained TV playback, remote controls and Return to Phone remain owner acceptance items. No shutdown code was changed and shutdown was not selected for this focused engineering run.

Only the Cast library, Cast DEX and two version metadata members differ from signed 2103508. Kodi, Cobra, other DEX, provider implementations, Search, tracking, Continue Playing, Video Lock, UI, settings and stored data remain unchanged. Final signing and install-over receipts accompany the downloadable pair.

For one consolidated acceptance session: cast a compatible provider movie, allow multiple fragments to play, seek, exercise Pause/Resume and Return to Phone, then verify ordinary Exit and same-profile relaunch. Do not interpret successful LOAD alone as playback success.

Recovery 2103511 is an original-signed forward recovery restoring 2103508 content without uninstalling or clearing data. Install it only if recovery is needed. Because its version is higher, returning subsequently to an older QA version requires a later authorized forward candidate; do not force a downgrade. Protected 2103506 and 2103504 artifacts remain retained. No accepted baseline is promoted automatically.
