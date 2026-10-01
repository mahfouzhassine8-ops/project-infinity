# Infinity Mobile 1.0.5.177 — Native Ambient Warm-up Repair RC1

Parent skin: Infinity-Mobile-1.0.5.176-Native-Video-Ambient-Settings-RC1.zip
Parent SHA-256: 4263de3906ea0dc6e24f3c6f04c2f779b0c7a8bbdd31656b82e221402063d1c9
Required APK: 2103282 (unchanged)
Command Center: 0.3.5.17 (unchanged)

## Diagnosis

The locked .176 observer created a continuous xbmc.RenderCapture and immediately called
getImage(30). If the first Android capture buffer was not ready within 30 ms, the
zero/failed buffer was treated as a hard error. The outer error handler then destroyed
that capture and created a new one. A renderer that needs one warm-up frame could
therefore loop forever without ever reaching the second read.

A deterministic regression reproduces the issue when every new capture's first
getImage call reports not-ready: .176 creates a new capture on each loop and never
activates ambient.

## Repair

Keep the SAME continuous RenderCapture through bounded transient misses.
- 50 ms maximum per getImage wait.
- 12 consecutive misses before a true hard reset/backoff.
- Successful warm-up buffers still drop the first two valid frames.
- Once ambient is active, a transient capture miss holds the last valid field instead of flashing it off.
- Session/title changes still reset immediately so old colors cannot leak.
- Pause/buffering/session/failure ownership remains unchanged.

No APK/native library, Cobra source, playback, provider, resolver, Command Center,
or Home geometry change is part of this repair.

Local verification:
- 17 observer/lifecycle tests PASS, including first-frame-not-ready regression.
- 14 native ambient kernel tests PASS unchanged.
- 562 skin XML files parse.
- 579 protected hashes verify.
- Only 4 files differ from exact .176: addon.xml, infinity-skin.json,
  Infinity-Protected-Manifest.json, and resources/lib/infinity_native_ambient.py.
- 1,377 archive files are byte-identical to .176.

Candidate package SHA-256:
009440bc258cb49286b834be5f745d04d4324d03f11d1c316c81fd803bc50a0f

Status: TEST CANDIDATE. Physical Fold verification is still required.
