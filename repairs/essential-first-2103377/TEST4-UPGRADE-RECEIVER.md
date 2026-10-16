# TEST4 RC02: upgrade event versus Close process proof

Current failure is Android `38887412457` at `412c6341`, not a newer native
build failure or a repeat of the physical observer traceback.
Native `38887113826` at `f2c663fa` completed successfully: original 61 Python
cases, 11 initialization cases, four race cases, eight SQLite cases, seven
directory cases, original source/authorization protections and full ARM64 build.

Android passed all 308 regressions, protected permanent signing and signed
TEST2/TEST3 preservation. Fresh TEST4 RC02 completed production Close, both
Java seals, whole-UID death, seven database integrity checks and saved-data
reopening. Its internal APK SHA-256 was
`fc8a2792c6159eeb3d86dae2dddf72d0b8435a9fb846e56c3b00bf471e2e1205`.
No candidate was delivered or promoted.

## Exact latest failure

The separate signed TEST3 retained-data baseline initialized all 37 synthetic
services and completed real Close in 4,877 ms. All required essential receipts,
both Java seals, termination authorization and actual whole-package absence
were verified. The backup contained 46 unchanged state/database files.

| Android log event, UTC | Evidence |
| --- | --- |
| 11:05:04.421 | Engine PID 7122 died after authorized COMPLETE |
| 11:05:04.661 | Coordinator PID 7086 died; whole UID subsequently absent |
| 11:05:06.449 | PackageManager replaced APK and explicitly retained data |
| 11:05:07.340 | New PID 8053 started for broadcast InfinityCobraBootReceiver |
| 11:05:09 | Test rejected post-install snapshot: Verify backup only after real whole-UID death |

The manifest already subscribes InfinityCobraBootReceiver to
MY_PACKAGE_REPLACED. Android started that unchanged receiver as part of the
explicit APK installation. The test incorrectly reused its post-Close
zero-process prerequisite for the distinct post-install/pre-launch snapshot.
The candidate engine was not launched; its early and loaded Close checks
were not reached. This does not establish a new essential-save failure.

Full artifact `12041269355` is SHA-verified:
`3a6ccc3f4b36c7af8ca720991c3c3c55750bdca6527be9da490c0a3f107143b9`.
The exact prior Close receipt and receiver-start line are retained in
`../android-checkpoint-shutdown/runtime-tests/evidence/upgrade-receiver-38887412457.json`.

## Verification-only correction

Normal Close and backup still require zero processes under the package UID.
Only the byte comparison immediately after explicit install -r accepts a new
Java main process when its actual PID has a matching Android receiver-start
record, its maps contain neither Kodi nor Python, the old engine remains
dead, and the original completed Close identity/save proof is unchanged.
Unknown processes, new native engines, old live PIDs and unavailable image
identity fail closed. A receiver that naturally finishes is observed without
termination. This boundary is explicitly not a new shutdown/death proof.

Settings, favourites, preference and all seven databases must still have
exactly the same hashes after installation. Integrity inspection uses a
second copy so it cannot modify the verified backup. Boundary identity is
checked before and after the copy. Subsequent candidate early/loaded Close
retains every original essential receipt, both Java seals, strict whole-UID
death, real mkdirs/essential-settings regression, integrity and reopening.

Fourteen boundary controls pass locally, including the actual failed run's
receipt/receiver origin, rejection of the same Java process after Close,
unknown origins, wrong PIDs, Kodi/Python images and missing save/death proof.
Controlled OS peers in those host tests are not Android acceptance.

No native code, Java runtime, Android manifest, APK version, skin, add-on or
user data is changed in this increment. Reuse native `38887113826`; rebuild
and verify the same matched TEST4 RC02 candidate through the Android workflow.
The synthetic services remain a control, not a verified Diggz/custom-skin
clone. Physical Fold approval remains required; no final lock.
