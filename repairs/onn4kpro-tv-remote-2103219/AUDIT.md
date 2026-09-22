# Infinity/Cobra 2103219 — onn. 4K Pro TV Remote Responsiveness RC2

Protected parent: passed 2103218 onn. 4K Pro ARMv7 TV candidate.

## Scope

This change exists **only on the 32-bit TV branch**. The arm64 phone/Fold Infinity/Cobra line is not modified.

## Problem observed on physical onn. 4K Pro

The ARMv7 TV APK installs and launches, but Cobra remote/D-pad navigation feels slow and heavy.

Source audit found two TV-hostile hot paths:

- every normal Cobra focus change launches a ViewPropertyAnimator;
- Live TV guide focus synchronously rebuilds programme detail UI on every D-pad step.

The TV candidate also carries relatively long panel/child motion timings inherited from the touch/mobile presentation.

## TV-only correction

- Keep Cobra's focus visual state, but apply it immediately on D-pad focus changes rather than animating every step.
- Coalesce guide programme inspection with a 45 ms delayed update so rapid D-pad travel is not blocked by repeated detail re-renders.
- Shorten TV panel/child presentation motion while keeping the approved visual language.
- Explicitly keep drawer rows remote-focusable.
- Preserve all playback, providers, guide data, timeshift/rewind, PiP, background audio, Smart Return, Movies/Shows, Health Center, and native stability fixes.

## Protection

- Parent 2103218 remains installable and unchanged.
- Mobile/Fold arm64 branches are untouched.
- Package remains `com.projectinfinity.kodi`.
- Permanent Infinity signer is mandatory.
- ABI remains `armeabi-v7a` only.
- Physical onn. remote acceptance is required before promotion.
