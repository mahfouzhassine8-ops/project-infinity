# Infinity/Cobra 2103220 — onn. 4K Pro TV Grid Only RC3

Protected parent: passed 2103219 onn. 4K Pro TV Remote RC2.

## Scope

This change is **TV 32-bit only**. The arm64 phone/Fold Infinity + Cobra line is untouched.

## User direction

Remove every Live TV view mode from the TV build except **TV Grid**.

## Runtime contract

- TV Grid is the only selectable/usable Live TV layout.
- Any stale stored preference for Mobile, Compact, Cards, or Focus resolves to TV Grid.
- Legacy mode entry points are redirected to TV Grid so an old callback cannot switch the TV build away from Grid.
- The view-mode chooser is disabled on this TV build.
- The TV Grid title remains informational, not a layout selector.
- Remote responsiveness changes from 2103219 are preserved.
- Playback, providers, guide data, timeshift/rewind, PiP, background audio, Smart Return, Movies, Shows, recordings, Health Center, and native stability are unchanged.

## Protection

- ABI remains `armeabi-v7a`.
- Package remains `com.projectinfinity.kodi`.
- Permanent Infinity signer remains mandatory.
- 2103219 remains untouched as rollback.
- Physical onn. 4K Pro acceptance is still required before promotion.
