# Kodi 22 Piers Builder Design

## Goal

Make Kodi 22 "Piers" the default Android APK build target while preserving the repository's existing Kodi 21 Omega, Kodi 20 Nexus, and Kodi 19 Matrix choices.

## Upstream Basis

Kodi 22 is built from the `master` branch of `xbmc/xbmc`; there is no upstream `Piers` branch. The current upstream Android guide requires Java 17 or newer, Android NDK r28c, and Android SDK platform/build-tools 37. Kodi 22's addon repository channel is `piers`.

References:

- <https://github.com/xbmc/xbmc/blob/master/docs/README.Android.md>
- <https://github.com/xbmc/xbmc/blob/master/version.txt>
- <https://mirrors.kodi.tv/addons/piers/>

## Build Target Model

The workflow will expose human-readable release choices and resolve them to build details before source checkout.

| User choice | Upstream source ref | Addon channel | SDK/build-tools profile |
| --- | --- | --- | --- |
| Piers | `master` | `piers` | Android 37.0 / 37.0.0 |
| Omega | `Omega` | `omega` | Existing compatible profile |
| Nexus | `Nexus` | `nexus` | Existing compatible profile |
| Matrix | `Matrix` | `matrix` | Existing compatible profile |

`Piers` becomes the workflow default. User-facing job names, APK filenames, artifacts, and releases continue to say `Piers`, while source checkout and cache keys use the resolved `master` ref. Piers deliberately remains a rolling target: each run updates to the current upstream `master` commit instead of pinning a prerelease tag.

## Workflow Changes

Add an early build-profile step that validates the selected release and publishes the source ref, addon channel, Android platform, and Android build-tools version as step outputs. Every downstream source, cache, signing, diagnostic, and release reference will use the appropriate resolved or display value rather than assuming the input is a literal Git branch.

Install Android 34 and 37.0 SDK components so the retained legacy choices remain available while Piers can use the current upstream toolchain. Keep NDK r28c and Java 17, since those already match Kodi 22's documented requirements. Replace hard-coded build-tools 34 signing paths with the selected profile's build-tools path.

Record the checked-out source commit and a fingerprint of Kodi's `tools/depends` tree. Include that dependency fingerprint in the expensive depends-cache key so ordinary Kodi source changes can reuse compatible dependencies, while upstream dependency-definition changes automatically start a fresh cache. GitHub releases produced from the rolling Piers profile will be marked as prereleases; retained stable profiles will continue to create normal releases.

Existing source patches will remain narrowly scoped and idempotent. A patch that is already present upstream must report that no change was needed rather than failing or applying twice.

## Configuration and Documentation

Update the README quick start, addon examples, source example, and local preflight command to use Piers by default. Retain notes for selecting older addon channels when building older Kodi releases. Do not change the repository's customization features, package naming behavior, signing model, or release publishing behavior beyond making them profile-aware.

## Validation

Add a repository-local validation script that checks the workflow and documentation contract without starting a multi-hour Android build. It will verify:

- Piers is the default and maps to `master`.
- Omega, Nexus, and Matrix remain selectable.
- Kodi 22 selects Android platform 37.0 and build-tools 37.0.0.
- NDK r28c and Java 17 remain configured.
- Signing uses the resolved build-tools path rather than a hard-coded 34.0.0 path.
- The depends cache is keyed by the checked-out `tools/depends` fingerprint.
- Piers publications are marked as GitHub prereleases.
- Piers addon URLs and local preflight examples are present.

The test will be written and observed failing against the current repository before production files are changed. Final verification will include the new validation script, YAML parsing, the existing local preflight checks, and a review of the complete diff. A full APK build remains a GitHub Actions integration test because the repository's workflow estimates 20 to 90 minutes and requires the Linux Android build environment.

## Non-Goals

- Removing older Kodi release choices.
- Pinning Piers to a single alpha or beta tag.
- Refactoring the builder's customization pipeline.
- Publishing, pushing, or triggering a GitHub Actions build without separate authorization.

## Acceptance Criteria

1. A default workflow dispatch clearly targets Kodi 22 Piers and checks out `xbmc/xbmc` `master`.
2. The Piers profile uses the Android 37.0 toolchain documented by upstream.
3. Existing Omega, Nexus, and Matrix selections remain available.
4. APK naming, cache keys, diagnostics, and release notes identify the selected Kodi release correctly.
5. Repository documentation and examples describe Piers as the default prerelease target without calling it a stable release.
6. Local automated validation passes with no stale Kodi 21 default or hard-coded signing build-tools 34 reference.
7. Piers tracks current `master`, invalidates dependencies when upstream definitions change, and publishes as a prerelease.
