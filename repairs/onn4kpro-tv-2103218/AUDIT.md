# Infinity/Cobra 2103218 — onn. 4K Pro / Google TV ARMv7

Protected parent: locked and passed 2103217 Media Return Context.

## Purpose

Build the same Infinity + Cobra product for Google TV devices whose Android userspace accepts **armeabi-v7a** native applications. The mobile/Fold arm64 line is not modified or replaced.

## Architecture

- Kodi 21.3 native dependencies and engine are rebuilt with Kodi's ARM host: `arm-linux-androideabi`.
- Final APK must contain `lib/armeabi-v7a/libkodi.so`.
- Final APK must contain no `lib/arm64-v8a/` native payload.
- `libkodi.so` must verify as ELF32 / ARM.
- The Python 3.11 GIL stability repair from 2103209 is applied to this new native engine before compilation.
- GUI/render hardening remains source-built in the ARMv7 engine.

## Android TV

The existing Infinity manifest already includes:
- Leanback launcher category
- TV banner
- touchscreen not required
- television/Leanback compatibility feature declarations

Those contracts are preserved rather than introducing a separate UI fork.

## Feature parity

The generated Android source is reconstructed through the exact locked chain:
2103209 -> 2103210 -> 2103211 -> 2103212 -> 2103213 -> 2103214 -> 2103215 -> 2103216 -> 2103217.

The onn. build therefore keeps the same:
- Choose Your Experience / Infinity / Cobra handoff
- Cobra Live TV, guide, providers, Quick Peek, recordings, reminders, timeshift/rewind
- Movies and TV Shows final media experience
- media See All/Genre return context
- Smart Return in Experience & Display
- fixed-blue Live TV Ambient and Night Cinema/player presentation
- Infinity Health Center
- PiP/background playback and Android media integration

## Protection

- Mobile/Fold arm64 locked branches are untouched.
- Package remains `com.projectinfinity.kodi`.
- Permanent Infinity signer is mandatory.
- No device-runtime pass is claimed until tested on the onn. 4K Pro.
