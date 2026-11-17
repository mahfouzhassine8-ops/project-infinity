Infinity Cast audio compatibility QA — derived from exact original-signed 2103504.

Install 2103506 over the existing Infinity installation. Keep the app data; do not uninstall or clear data. This is an internal QA candidate, not an accepted baseline.

2103507 is matching forward recovery: it restores the exact signed2103504 payload except the higher Android version code and existing Infinity last-updated label. Install it only if recovery is needed. Its higher code permits normal installation over2103506. It does not restore or replace your personal records.

Included correction: Cast-owned conversion of E-AC3 audio in multiplexed MKV-to-fMP4/HLS delivery to AAC-LC stereo192kbps. Source32/44.1/48kHz preserved, original compressed video packets/timestamps retained, no video transcoding. Existing AAC and direct-play paths stay unchanged. Unsupported rates/configuration changes fail explicitly.

Engineering evidence: host sample-clock/priming/final-padding/random-seek/cache/cancellation tests; actual ARM64 Cast library linked against the unchanged504 engine; selected Android JNI/authenticated relay/range/fragment tests across four fixtures. H264/AAC rendered video/audio and sought successfully. HEVC Main10 evidence establishes video preservation/extraction, not receiver rendering. All owned native contexts retired in the selected cancellation test.

Only the Cast native library, Android version metadata and existing Infinity component-version label differ in the candidate. DEX, Kodi, Cobra2103445, providers, Search, Watchlist, Continue Playing, tracking, Video Lock, UI, settings, shutdown and data schemas are unchanged. Existing504 limitations remain; no broader tracking/startup/crash repair is claimed here.

Physical Fold/TV acceptance remains pending. Confirm supported provider-movie video and sound, seeking/pause/resume, Return to Phone, retained progress, then normal Exit/relaunch with the same profile. No physical playback or shutdown success is claimed by the automated checks. The earlier receiverERROR4 may have additional device/codec causes; video is preserved, not transcoded.

A historical Android run43997770119 had a green workflow but failed its video-render assertion. That failure remains recorded. The wrapper and renderer evidence were corrected; run44000750859's actual receipt passes. Full native engine and production DEX were reused.
