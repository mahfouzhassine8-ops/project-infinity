# Cobra 2103204 — OLED Blue presentation candidate

Parent: locked 2103203, commit `45eac1987c7cd583572d6715eee2ba191130ad71`.
Package: `com.projectinfinity.kodi`. Candidate: `1.0.9-Cobra-OLED-Blue-RC1` / 2103204.

This is a presentation pass, not a redesign or feature release. It preserves
the existing controls, navigation, stream handling, timeshift architecture,
video geometry, PiP controls, call-audio policy and Multi-View ownership.

## Scope

- Coordinate built-in Light white/blue and Dark/OLED black/blue defaults across
  the shell, guide modes, chooser, sheets and native dialogs.
- Retain authoritative user-installed palettes, images, fonts, styles and the
  emergency theme recovery path. Built-in appearance remains built-in, not an
  automatically installed theme package.
- Recognize only the exact factory legacy palette manifest when adopting the
  new native Dark colors; retain its existing density/target/motion settings.
  Nonmatching user-edited palette files remain authoritative and untouched.
- Refine existing typography, spacing, focus/selected/pressed surfaces and
  video-safe dark panels. Modest translucent fills and tonal gradients are
  ordinary drawables, not expensive live blur or video-surface effects.
- Repair reproduced Light contrast and narrow chooser clipping; keep labels,
  actions and controls. Short list fades keep hit rectangles stationary.

Only the exact reviewed Java owner allowlist and Gradle version identity may
change. Imported-theme storage and validation, APK resources/assets, native
libraries, JNI signatures, permissions and exported components are protected.

## Verification contract

`reviewed.json`, `visual.patch`, and source hashes freeze the reviewed delta.
`inherited-android-cases.json` retains all 445 inherited test identities; new
test identities and source hashes are recorded separately. The build must
pass both inventories rather than merely report a test count. Two independent
replicas build/sign with the permanent configured signer. A separate local
verifier checks the downloaded candidates and compares signed APK bytes.

Android fixture screenshots use production views with controlled data and, for
player tests, controlled player collaborators. They do not prove physical GPU,
decoder, provider, Fold, SystemUI or live playback performance. See the final
delivery report for actual executed results; this file describes the contract,
not a claim that every gate has already passed.

## Rollback

Complete locked-parent archive: `Cobra-2103203-Complete-Product-Rollback-20260921.zip`.
SHA-256: `7e064b3703c763d49f6c6d630cd1814378a704b25a7c97fca40aa02c082c139f`.
It contains the signed APK, all 220 generated inputs, source recipes, audit
evidence and lock/verification records; CRC and all member hashes were checked
before implementation and the archive was saved durably. It does not contain
on-device private data, recordings, provider credentials or the private signer.
Never uninstall or clear data to force a downgrade; use a supported restore or
a reviewed permanently signed forward-version recovery when required.

Physical-device acceptance remains required. This candidate does not replace
the user's locked baseline automatically and is not described as fully passed
until the separate device checklist is completed.
