# Defer the unused command resolver during observer initialization

Android diagnostic **38973572640 / de0560d5** passed packaging, permanent signing,
all 30 packaging controls, exact non-engine APK byte preservation and saved 308
regression association. Native **38967896318 / e78c769d** passed completely.
The signed internal diagnostic APK SHA-256 is
`284465f25e1551ed1b167fdb1db129d483b8dc8e3a12ec746fae396b3e68852c`.
The earlier cache-timestamp packaging problem is resolved.

The candidate then failed a real phase-matched Android Close at 25.279s native /
25.870s coordinator. All 41 observers were pending: **38 at `python.import.shutil`,
2 at `python.import.importlib`, 1 at `python.source.compile`**. There was no Python
exception. Write admission and every essential save remained unstarted, sealing
was false, termination was refused, and both package processes remained alive.
The baseline controls passed, but those are not candidate shutdown passes.

The observer eagerly imports `shutil` in every interpreter but uses it only for
four later child-command PATH lookups. Initialization itself needs none of those
lookups. The targeted correction defers that import until `_which(command)` is
called. It still invokes the original `shutil.which`, propagates import/lookup
errors before a child starts, and retains every Python/native command, descriptor,
write-admission and durability check. No timeout, add-on, skin or user-data policy
changes. AST comparison confirms all other observer behavior is unchanged.

Five new real-native controls pass under CPython 3.11.7. An unavailable resolver
makes the exact previous production source fail all 41 observers; the correction
initializes 41/41 without requesting that unused dependency. On-demand lookup
retains standard results; an original import failure starts no child; an actual
buffered-write flush failure still prevents sealing/authorization. Existing
11 initialization, 5 Close-race, 7 live-stage, 8 progress, 16 selected write/child
guards and 16 strict source contracts pass. Live-stage pause tests now pause the
next required import, sqlite3; the removed shutil dependency has its explicit
old-versus-new reproduction rather than a weakened observer-success assertion.

This proves the dependency correction and preserved host guards. It does not
prove Android timing, the exact inner shutil import wait, or physical Fold
acceptance. A new complete ARM64 build and Android checks are required. Reuse the
unchanged RC05 Java/manifest/assets and 308-test proof; only the embedded observer
engine changes. No Fold APK promotion or final lock is authorized by these results.

Exact Android artifact identities and all 41 interpreter stages are recorded in
`evidence/observer-shutil-stage-38973572640.json`. Disposable synthetic services
and the emulator's Estuary skin are not the Fold's full Diggz ecosystem and
custom Infinity skin 1.0.5.223. The physical installation remains untouched.

Correction source **f5e3d943** is saved. Native workflow **38975950035** has
passed its complete mandatory host suite (job 117225316491); full ARM64 build
117225830503 is in progress. The internal workflow will require that exact
complete success, preserve RC05 Java/308 proof, and run the four original probes
in independent AVDs with fail-fast disabled: fresh, cold, core-initialized and
loaded. Twelve dispatch/identity/failure controls pass normally and under -O.
The original probes and their save/death/integrity/reopen assertions are unchanged.

Four-case verification **38976250598 / 94b03c20** is queued and waits for the
exact complete native **38975950035 / f5e3d943** success before packaging/signing.
Each case preserves its own evidence and failures do not cancel other cases.
Only CI execution remains at this handoff; the user can monitor those queued runs.
There is no background assistant monitoring and no corrected Fold APK delivery.
