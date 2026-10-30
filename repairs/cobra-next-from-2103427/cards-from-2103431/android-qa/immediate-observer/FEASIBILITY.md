# Read-only feasibility: immediate platform UI observer

This document records the earlier research phase. The subsequently authorized implementation and host results are recorded in RESULT.json; device execution remains pending root review.

The official Android17 `frameworks/base` source at commit94b4c163b7dfe5ce3607f7bb8456f9573f7de57d exposes the required classes. `UiAutomationShellWrapper` is public with public connect, getUiAutomation, compressed-layout and disconnect methods. `AccessibilityNodeInfoDumper` exposes public static dumpWindowToFile(root,File,rotation,width,height). The build statically includes the wrapper/core implementation in the system uiautomator.jar. These are hidden SDK classes, so a tiny QA main may reflect those existing methods while compiling only against the pinned official Android SDK. It must bundle only its own QA class, never platform implementations or JUnit.

The official DumpCommand calls waitForIdle(1000,10000) before getRootInActiveWindow. Both its null-root and idle-error strings exactly match run41002818185. Calling the same connected platform wrapper and Dumper directly can omit that observation-only idle prerequisite while leaving app timers and feature assertions unchanged. Actual APK source import and Mobile rendering already succeeded; this does not establish the cause of ongoing accessibility activity.

Use the inherited OS BOOTCLASSPATH unchanged. The official shell wrapper establishes the application CLASSPATH prefix /system/framework/android.test.runner.jar:/system/framework/uiautomator.jar. A later approved QA main would append only /data/local/tmp/CobraImmediateHierarchy.jar and run through /system/bin/app_process /system/bin. ANDROID_DATA=/data/local/tmp follows the existing shell tool's QA-cache behavior. Do not add bootclasspath files, install a package, change hidden-API policies, grant permissions or invoke runtest/JUnit.

The previous RepetitiveTest failure occurred inside UiAutomatorTestRunner.WatcherResultPrinter. A standalone main that never calls RunTestCommand or UiAutomatorTestRunner does not enter that failing runner path. Loading the same OS archive does not require loading every unrelated test class.

## Required preflight and state/age guards before any later runtime execution

- Preserve the actual installed431 byte/signature checks and finite baseline selection. Hash and inspect the actual system shell script/JARs and QA DEX; reflect the exact allowed public class/method descriptors. Failure is a blocker, never a reason to alter classpaths or permissions adaptively.
- Create one fresh shell-wrapper connection, enable the same compressed hierarchy, and obtain the current active root once. No waitForIdle, sleeps, speculative cached root or polling inside the observer.
- Record device monotonic acquisition/dump timestamps, expected package, active window ID, root/display bounds and actual rotation. Validate package, visible root, nonempty bounds and the same active package/window again after serialization. Use the platform display-query sequence already present in DumpCommand; no hardcoded geometry or rotation.
- Null/changed root is an explicit observation miss. Only the existing bounded source-save15/Cards-ready10 loops may consume such a miss. Missing classes, connection, transport or malformed output remain fatal. No extra attempts/deadline.
- Write unique XML/metadata paths and reject missing/empty/partial files. Preserve every current strict Cards/action/selection/state assertion.
- Before coordinate dispatch, require the freshly parsed current target, intersection with current root/window bounds, and a conservative host-monotonic age from observer-command start. Keep the existing3.5second guard where a4second player window applies; never lengthen the production visibility interval. A stale target is rejected, never reused.
- The observer injects no input and calls disconnect in finally. Preserve the independent terminal screenshot even when hierarchy capture fails.

This is source-supported feasibility, not a runtime PASS. Prior artifacts did not contain the actual API37 system JAR bytes, and no compatible running device is currently attached to this workspace. The next authorized runtime must verify their descriptors first and fail closed if the image differs. No helper implementation, compilation, application test, third CI run, app/native edit or shutdown test occurred in this investigation.
