# Infinity 21.3 Donor Engine

Source artifact: user-provided `Infinity.apk` extracted from `kodi original.apk.zip`.

## Verified donor facts

- APK SHA-256: `1929d1fdaf285eca93a138978323e662a78070c76161ce44f609ac4abaf00e49`
- Native engine: `lib/arm64-v8a/libkodi.so`
- libkodi.so SHA-256: `cfa76e099972e78537b3384d7db6361153dbd30fec3a35fb93f673d575097dd6`
- Architecture: ARM64 / AArch64
- Kodi addon ABI metadata: `21.3.0`
- Native binary target: Android 24+
- Native binary toolchain marker: NDK r28c (13676358)
- ELF LOAD alignment: `0x4000` (16 KiB)

## Role

This binary is the behavioral/native donor reference for Infinity Engine development. It is not to be patched blindly in-place. The replacement engine will be source-built while preserving the donor's known-good runtime traits and Kodi compatibility.

## Required compatibility to preserve

- Kodi 21.3 addon ABI behavior
- Python/addon ecosystem compatibility
- Repository and skin compatibility so Diggz can install normally
- ARM64 Android playback stack
- 16 KiB native ELF alignment

## Infinity-native layers to add above/around the donor behavior

1. Fold-first window/display lifecycle
2. Native playback state bridge
3. Conditional PiP state and lifecycle
4. Renderer/surface resizing for PiP and Fold transitions
5. Background media service / MediaSession integration
6. Persistent Player Settings controls independent of skin/OSD
7. System / Light / Dark theme modes
8. Lock, PiP, Fill, background and Fold controls exposed as engine settings

## Rule

Stable/reference APKs remain frozen. All new engine work is source-controlled and tested before device submission.
