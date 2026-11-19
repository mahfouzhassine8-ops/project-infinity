# Combined QA from signed 2103514

## Continue Playing

A malformed remembered URI introduced a provider-wide negative result for the
rest of a list render. A subsequent valid URI sharing the same verified
provider pins could then go to recovery. Continue Playing now validates each
remembered URI independently and caches only the provider proof. Watchlist and
Save for Later keep their existing behavior.

An exact previously failed route still goes to recovery, and a different
route's failure history cannot suppress an otherwise verified route. Changed
source pins and unapproved Umbrella and POV versions still fail closed.
The latest protected profile's selected record was unavailable, so the
reproduced rendering defect cannot be attributed to the reported Fold attempt.
The scoped decision log differentiates unavailable or previously failed routes
from a validated native failure ticket, chooser cancellation and handoff.
A dispatch return is separate from verified recovery playback.

## Empty Shell

Apply the three-file native patch from 301a6cd0 unchanged. The add-on ID at
interpreter creation, return before the persistence ledger, completion
marker and existing terminal events distinguish where a future occurrence
stopped making progress. The cause of the field failure remains unproven.

## Preservation and release

The module preservation receipt compares the four Python changes and reserved
Command Center metadata to all 83 signed add-on members. Candidate metadata is
0.3.5.85. Forward recovery restores all signed 2103514 behavior using 0.3.5.86
so the original installer can apply it without downgrading a signed module.
The APK versions must come from the live release registry and are not
reserved by module preparation.

Candidate APK payload allowance: the four Python sources in CONTINUE-SCOPE,
their Command Center version and signed manifest pair, the ARM64 Kodi library
validated against SCOPE.json, and mandatory APK version and Infinity release
labels. Recovery restores the 2103514 engine and all Python behavior, with
only required forward APK and Command Center version/signature metadata.
Cobra, Cast, Search, providers, Trakt, skin, screensaver, DEX, profile data and
all other content must remain byte-identical where applicable. No shared
subsystem, shutdown or Python synchronization change is authorized.

Confirm native build/ABI, original module trust and installed version
activation, signed package identity and certificate, exact APK differences,
and the selected Android startup and in-place upgrade checks before delivery.
No owner release or acceptance pointer is advanced in this branch.

## Capture during normal use

Keep raw logs private. With the authorized USB connection, use a separate
terminal per filter on a normal launch or Continue Playing selection.

```sh
adb logcat -v threadtime -s Kodi:I | awk -f repairs/infinity-2103514-targeted-20261118/filter_startup_trace.awk
adb logcat -v threadtime -s Kodi:I | python3 repairs/infinity-2103514-targeted-20261118/filter_continue_trace.py
```

The Continue filter emits fixed reasons, without media identifiers, URLs,
credentials, route fingerprints or checkpoint values. The startup filter keeps
process/thread IDs and the canonical add-on ID at interpreter entry. Keep
`trace.overflow` if it appears. Missing events after overflow or after the
existing finite trace window do not prove an interpreter deadlock.
