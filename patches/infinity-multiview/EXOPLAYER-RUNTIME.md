# Infinity Live TV Media3 runtime

This branch adds a separate, Infinity-owned Live TV playback path. It is not a
replacement for Kodi's main player, renderer, skin, or the locked Infinity
shell.

- Media3/ExoPlayer 1.7.1 is packaged in the Kodi Android module.
- Each two-up tile owns one ExoPlayer and one TextureView.
- The controller owns one shared Android audio-focus lease; the focused tile is
  audible and D-pad/OK or tap switches audio.
- HLS, MPEG-TS and RTSP URLs are handed to Media3; request files are one-shot
  and deleted after parsing.
- Back, pause and configuration changes are handled inside the Live TV branch.
- Cobra is a visual/behavior reference only; no Cobra or libmpv code is bundled.

This is a candidate build. Provider compatibility, decoder limits, video
surface output, audio handoff and return-to-Infinity behavior still require
device acceptance before the branch is locked.
