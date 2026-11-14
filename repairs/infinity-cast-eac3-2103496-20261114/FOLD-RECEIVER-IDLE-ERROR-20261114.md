# Fold Cast Result — media loaded; first fragment delivered; receiver IDLE/ERROR

**Status:** User-supplied screenshots analyzed (two frames from a single physical Cast attempt, 2026-11-14). Read-only evidence handoff. **The screenshots do not display an APK versionCode**: confirm installed build before attributing to signed 2103498. Do not assume a different TV test has passed.

**Privacy:** The TV's user-defined label and content title have been intentionally omitted from this public report. No original private source URLs, HTTP credentials, screenshot binaries or raw owner diagnostics are published here.

## Observed ordered events

```text
stage=session outcome=connecting result=0
stage=transfer outcome=receiver_connect result=0
stage=transfer outcome=source_prepare result=0
stage=mkv_video outcome=hevc result=0
stage=mkv_audio outcome=eac3 result=0
stage=mkv_inspection outcome=stream_copy_ready result=1447
stage=relay outcome=prepared result=0
stage=media_format outcome=hls result=0
stage=transfer outcome=media_load result=0
stage=receiver_state outcome=player result=5
stage=receiver_state outcome=idle_reason result=0
stage=media_load outcome=accepted result=0
stage=receiver_access outcome=received result=0
stage=receiver_access outcome=body_written result=130799
stage=mkv_fragment outcome=copied result=0
stage=receiver_state outcome=player result=1
stage=receiver_state outcome=idle_reason result=4
stage=receiver outcome=media_idle_error result=4
stage=receiver outcome=media_idle_error result=4
stage=observer outcome=retired result=0
stage=mkv_context outcome=retired result=0
stage=relay outcome=retired result=3
stage=relay outcome=body_bytes_written result=3458206
stage=cleanup outcome=native_released result=0
stage=cleanup outcome=session_released result=0
```

## Code-specific interpretation (verified by reading current on-branch source)

- `InfinityCastRemux.java` logs `stream_copy_ready` with `starts.length - 1`: **1447 is the count of indexed segments, not a Cast error**.
- `InfinityCastRemux.java` `mkv_fragment/copied result=0` refers to **fragment index 0**, not an error status.
- `InfinityCastRelay.java` `receiver_access/body_written result=130799` records the **first positive HTTP body write**, **not total transfer**. `body_bytes_written result=3458206` is the total bytes written by the relay to output streams at retirement. It does **not** prove receiver consumed or decoded all those bytes.
- `InfinityCastRelay.java` `relay/retired result=3` is the **request counter**, not a failure code.
- Official Google Cast Android `MediaStatus` constants: `PLAYER_STATE_LOADING=5`, `PLAYER_STATE_IDLE=1`, `IDLE_REASON_ERROR=4`. The **receiver reported media error after an accepted LOAD and HTTP requests**.
- `InfinityCastSession.java` generates `receiver/media_idle_error` from that Cast status, and falls back to the phone. The duplicate log entry does **not** establish two separate root causes. Successful cleanup is observed afterward.
- The previous source failure `mkv_mux_header_failed` before any payload delivery was **not observed** in this attempt; media preparation, first fragment generation and serving progressed further. This is not proof that the receiver supports this exact HEVC + EAC3 profile or that the fMP4 media is correct.

## New first failing stage

**Receiver initial media playback: Cast player LOADING -> IDLE (ERROR) after accepted LOAD and relay media traffic.**

Discovery/launch and header-generation are **not the first observed failures here**. However, the screenshots **do not contain a granular decoder/manifest/network error code**, request-level response statuses, exact source codec profiles, receiver capability matrix, or proof of decoded frames. **Do not assert a codec incompatibility, an HTTP problem, or a malformed fragment as fact.**

## Narrow Codex next steps (no speculative APK)

1. Correlate installed APK and full event timeline, preserving the signed 2103498 candidate and 2103499 exact-496 forward recovery; no update to accepted release pointer.
2. Validate **the actual HLS master/media playlist, fMP4 init and first .m4s fragment** emitted by the Cast-owned remuxer against real on-branch FFmpeg. Inspect `#EXT-X-MAP`, target duration, track/sample descriptions (`hvc1/hev1`, `ec-3` and `dec3`), fragment initialization, sequence/timestamps and discontinuities. Compare exact packet bytes, but do not claim TV decode from FFmpeg validation alone.
3. Verify **converted relay responses** for playlist, init.mp4 and first .m4s: HTTP 200/206, Content-Type, Content-Length/Range, CORS/OPTIONS, request methods and per-asset output-completion. In current `InfinityCastRelay.java`, `relay_http` diagnostics are logged for non-converted resources; **converted HLS assets lack equivalent per-resource status diagnostics**. Add narrowly scoped, sanitized logging only if needed to distinguish error stages, never raw provider URLs or credentials.
4. Check compatibility with this receiver's **specific HEVC profile/level and EAC3 audio/passthrough** (not merely codec names); HLS/FMP4 support is device-dependent. Isolate by reusing synthetic local H264/AAC, HEVC/AAC, HEVC/EAC3 samples and existing real native bridge/probe tests. Don't change video/audio encoding or add speculative transcoding without demonstrated need and approval.
5. Collect Google Cast `MediaError.getDetailedErrorCode()` if the existing SDK callback actually supplies it; otherwise report **receiver idle reason 4, detailed code unavailable**. Do not invent a detailed receiver error or claim on-device logs were obtained.
6. Only after a causal reproduction/test, implement the **smallest Cast-only correction**, run focused ARM64/Android tests, original signing continuity and exact preservation gate. Release **one** consolidated signed test candidate when verified, with one controlled physical TV acceptance. If not attributable, report the precise missing evidence instead of packaging unproven changes.

## Strict preservation

No Cobra changes. No modifications to Kodi engine, search/providers, Movies/TV, Watchlist/tracking/resume, network settings, shutdown, UI/skins or personal settings. Keep Google Default Media Receiver; no YouTube MDX/DIAL substitution.

Google references: https://developers.google.com/android/reference/com/google/android/gms/cast/MediaStatus ; https://developers.google.com/cast/docs/media ; https://developers.google.com/cast/docs/web_receiver/error_codes
