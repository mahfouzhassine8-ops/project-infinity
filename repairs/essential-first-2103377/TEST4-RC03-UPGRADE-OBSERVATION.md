# TEST4 RC03: post-install process observation

Latest completed Android attempt: `38899820197`, commit `8dfca753`.
Latest full native build: `38899217848`, commit `402dfe75`, **success**.
Current verification-only retry: `38938908138`, commit `73de91ca`.

## Preserved results

- All 308 Android regressions passed: original 274, 26 Java save tests and
  eight completion tests. All 14 original receiver-boundary controls passed.
- Exact native/Android pairing, permanent signing and signed TEST2/TEST3
  baseline preservation passed.
- Fresh corrected RC03 performed production Close in 12,891 ms, with
  essential saves, both Java seals, authorization consumption, actual whole
  package UID absence, seven database integrity checks and saved-data reopen.
  Internal APK SHA-256:
  `909bc1460db8c6166e8d92e6dea4f2668a925a35fd1903da22478f0d90350315`.
- The separate retained-state signed TEST3 baseline started all 37 synthetic
  services and completed loaded Close in 5,585 ms. All 16 essential owners,
  both Java seals and whole-UID absence passed. The verified backup contained
  46 state/database files.

No RC03 candidate was promoted or delivered. These are disposable Android
controls, not the user's configured Diggz/custom-skin Fold installation.

## Actual failure and limits of the existing evidence

The APK upgrade succeeded. Before comparing saved bytes or launching the
candidate engine, `saved_state_boundary` failed at:

`AssertionError: Unexpected package process before candidate launch`

That assertion tests a process name before examining its Android origin or
native images. Unfortunately, it did not print or save the rejected PID/name.
The artifact therefore does **not** establish which process triggered it or
why its name differed. Do not infer an ART/zygote rename or another engine
from the generic message.

The log independently proves this event sequence (UTC):

| Time | Event |
| --- | --- |
| 12:55:28.099 | Closed TEST3 engine PID 7375 died |
| 12:55:28.372 | Coordinator PID 7340 died; the probe verified whole UID absent |
| 12:55:30.356 | PackageManager began replacing the APK |
| 12:55:31.239 | Android started PID 8284 for InfinityCobraBootReceiver |
| 12:55:32 | The pre-launch process-name assertion failed |

The receiver is an existing MY_PACKAGE_REPLACED component. Its observed
startup does not prove that PID 8284 was the process rejected by the assertion.
The candidate's retained-state early and loaded shutdown tests were not reached.
The older keyboard-layout admission failure must not be reported as this run's
current blocker.

Artifact `12046144477` is SHA-verified:
`bd24ed969acbbf3f14e905a82190c0a0b20685a73a93668101e784b1fa1e37d1`.
The compact receipt/timeline evidence is retained in
`../android-checkpoint-shutdown/runtime-tests/evidence/upgrade-observation-38899820197.json`.

## Verification-only correction

Every boundary now retains the observed PID/UID/name, sampling history,
cmdline/status for mismatched names, matched receiver origin and failure even
when the assertion raises. Evidence files are siblings of the compared backup
directories, so writing observations cannot alter or contaminate saved-data
hash comparisons.

Only a process with an exact observed Android package-update receiver origin
can be re-observed for an ambiguous name. Its maps must already exclude Kodi
and Python. A bounded three-second installation-only observation requires the
expected name to appear, or the proven receiver to finish naturally. Persistent
ambiguous names, unknown PIDs/origins, original engine PIDs, unreadable live
images and any native engine remain failures. Every new sampled process is
checked. This is an observation of the explicit upgrade event, not a shutdown
or termination proof.

The 25-second shutdown deadline, strict zero-process post-Close boundary,
all essential owner receipts, both Java seals, exact upgrade hashes and real
early/loaded Close/death/integrity/reopen requirements are unchanged.

All 21 host controls pass, retaining the original 14. Seven new controls cover
a deliberately simulated transient name, unknown processes that cannot be
waited away, unresolved names, native images under ambiguous names, an engine
appearing on re-observation, strict post-Close refusal and saved identity on
failure. The simulated label is not presented as the unrecorded device label.

No native code, Java runtime, Android manifest, APK version, add-on, Infinity
skin, user data or signing identity changed. The complete green native build
is reused. Full Android retained-state acceptance is pending in `38938908138`.
No physical Fold approval or final lock is granted.
