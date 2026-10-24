# Surgical RC native-gate repair — 2026-09-09

## Evidence, not a device-crash diagnosis

The failing RC1 and RC2 logs and the earlier successful audited log were downloaded in read-only diagnostic run 34311574944. Artifact 10088543507 has ZIP SHA-256 `feab0e1b47f18b82b4a66f2dfd58084b16a4b7b635c4dc3d9e9482529a3c8172`. Log line counts/hashes and bounded excerpts are preserved in that artifact.

| Build | Real outcome | First compiler failure / comparison |
| --- | --- | --- |
| RC1 run 34295950801, job 102292707429 | Preflight and dependency configuration passed. Native gate failed; engine/APK and presentation skipped. | 2026-09-09T01:17:08Z: `JNIMainActivity.h:14:10: fatal error: 'androidjni/Activity.h' file not found`. No dependency cache was restored. |
| RC2 run 34307781843, job 102328197299 | Preflight/configuration passed. JNI unit passed after the one-off libandroidjni install. Gate then failed; engine/APK skipped. | 2026-09-09T04:15:48Z: `VideoSettings.h:15:10: fatal error: 'fmt/format.h' file not found` while checking XBMCApp.cpp. Restored RC1's prefix cache. |
| Audited run 34270347697, job 102210334751 | All three compiler checks and full build succeeded. | Restored the older hooked-d dependency cache. All three gate markers occur at 20:17:31–35Z. This warm-prefix success did not demonstrate a cold-prefix gate. |

RC2 was already present when this repair started; it is not a new retry launched by this repair. Its single-header fix was incomplete. No matching phone crash log was supplied: dark-mode/Fold device failures are separate and remain unaccepted.

## Root cause

`infinity71.py native-check` replayed compile_commands.json entries with `-fsyntax-only`. That database records compiler arguments, not prerequisite build execution. Kodi's tools/depends target default list does not build every CMake-internal library. FindLibAndroidJNI.cmake, FindFmt.cmake and FindSpdlog.cmake create the respective internal dependency targets. A CMake configure-time "Found" message can describe an output that its ExternalProject has yet to generate.

The native gate bypassed that build graph and accidentally relied on a previously populated dependency prefix. RC1 exposed the JNI header gap. RC2 added just JNI and exposed fmt next. Installing one header per failed run or disabling the compiler gate is not an adequate repair.

Pinned Kodi's `core_add_library` gives `platform_android_activity` and `windowing_android` their GLOBAL_TARGET_DEPS via both add_dependencies and target_link_libraries. The successful log confirms these exact target names. Build those targets normally so CMake supplies all required prerequisites before compiling their sources.

## Changes

1. Replace raw compiler replay in the gate with the configured CMake executable building `platform_android_activity` and `windowing_android`. Verify the three expected changed-source entries belong to those target object directories before running anything. Keep the real compiler gate; it now compiles the complete affected Android targets and produces reusable object files, not just syntax checks.
2. Add eight real host-CMake regression cases: empty prefix, the exact single-header RC2 trap, warm object reuse, real source failure, dependency-generation failure, unexpected target mapping, missing source, and invalid parallelism. They use small generated-header fixtures, not Android/Kodi native binaries.
3. Run those tests in the canonical Android-first workflow and upload native-gate output/status even on failure. Retain the existing independent engine/presentation/signing stages and dependency cache handling.

No Kodi C++/Java source patch, JNI ABI, version, branding, themes, lock, PiP, resume, or add-on payload is changed. Source.patch, contract.json and assets retain their original hashes. No new API, backup hook, external-player hook, refresh-rate policy, signing key or phone installation is introduced.

## Validation performed before push

- Exact pinned source patch applied successfully; repeated application verified idempotent.
- Real Android API34 javac + D8 check passed.
- Existing 47 Python tests passed unchanged; eight new native-gate tests passed: 55 Python tests in total.
- Host C++ bridge-state test, including 20,000 concurrent state publications, passed.
- Workflow YAML parsed and existing signing shell passed syntax check.
- Git comparison confirms runtime source/contract/assets/presentation unchanged.

The host fixtures reproduce the dependency-ordering defect and test the repair. They are NOT proof that the full ARM64 engine has compiled or that the app works on a Fold. The next canonical build must pass the actual Android target compile, full engine build and final packaging before those outcomes can be claimed.

## Remaining release gates

A retained signing identity is still required; no key was generated and current FIXED6 install-over compatibility is not established. Do not uninstall the phone app. Full engine compilation, final APK signing, dark/light switching, Fold/touch, PiP/lock/resume and supported device/page-size acceptance remain separate checks. RC2's parallel workflow should not be rerun instead of the repaired canonical `.github/workflows/build-infinity-android-first.yml`.
