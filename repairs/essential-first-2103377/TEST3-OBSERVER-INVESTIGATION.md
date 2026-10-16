# TEST3 physical observer initialization investigation

**Update:** compact Fold logs establish the `PyDLL(None)` guard-ordering
failure. See [FOLD-OBSERVER-CLOSE-RACE.md](FOLD-OBSERVER-CLOSE-RACE.md) for
the traceback, early/loaded Close reproduction and correction. Native diagnostic
run 38876390312 passed. A full backup is no longer a prerequisite; the original
missing-evidence findings below are historical.

Continuation baseline: `9e9ef198ef0a68f13644621724b0762e1150438b` on
`work/infinity-2103377-essential-first-shutdown-only`. No reset, rollback,
shutdown redesign, timeout extension, add-on exemption, signing change, or
physical-device mutation is part of this investigation.

## Current evidence

The latest completed native run **38867886900** passed at `77a6fc13`. The
matched Android run **38868115575** passed at `9e9ef198`: all **308** regressions,
nine native fixture controls, both Java save seals, essential saves, actual
engine and whole-UID death, seven SQLite integrity checks, and saved-data
reopening. Earlier internal fixture and repository/database failures are
resolved. These results concern a disposable internal emulator.

The permanently signed TEST3 APK remains unchanged:

- APK SHA-256: `4ec1e3b2cabb595d228bc07bae2c6b3073c5af12822c8e40b1ec505b00865bf8`.
- Certificate SHA-256: `d7adeb68e9341596a02bd3262b737a0f45fc6e771ed7e60285437e833b58c6d7`.
- Signed artifact: `12033617596`; Android evidence: `12032839495`.

Physical TEST3 failed. `Infinity-Diagnostics-20261016-041100.zip`, SHA-256
`f981984e093dac92177e0bf5263c86ac690ac85ec50cbe640f284911f98f3bf5`,
records **25,170 ms**, **37 active / 0 observed** Python writers, and 37 blocking
`checked_python_observer_initialization_failed` receipts with empty details.
Fifteen essential owners did not complete; PVR was already durable. There was
no successful essential seal, termination authorization, or verified process
death. The archive's older `native-cleanup.json` belongs to another PID/time
and is not TEST3 death evidence.

The native-hook-specific failure marker is absent. This narrows investigation
but does not identify the failing Python call. The archive contains no
`kodi.log`, original Python exception, full add-on sources, or database/profile
backup. The exact physical root cause is **not established**.

## Targeted diagnostic correction

`Start()` formerly continued after a failed `PyRun_String`, attempted further
callback/module operations, and recorded only a generic final failure. The
installation boolean chain similarly lacked a failing-stage receipt.

Initialization now records its first failure immediately in the existing
blocking ledger. Details include the native installation step or Python
import/constructor step, exception type/message, traceback file/function/line,
and errno observed at failure. The original pending exception and traceback
are restored for Kodi; diagnostic formatting imports no modules. If exception
formatting itself fails, the original exception still survives. A missing
native descriptor or calling-convention check remains a failed installation.

This corrects an established diagnostic gap. It is **not a claimed repair of
the physical shared initialization failure**. Protection policy, the read-only
descriptor correction, real write durability, SQLite VFS, owner requirements,
Java lifecycle code, and termination authorization are unchanged.

## Local verification

All eleven new cases use the production observer and native hooks with pinned
CPython 3.11.7 and a host Kodi VFS adapter. They do not run the actual Diggz
ecosystem or the physical Fold installation.

| Case | Observed / active | Result |
| --- | ---: | --- |
| Fresh observer | 1 / 1 | Pass |
| Sequential live interpreters | 37 / 37 | Pass |
| Concurrent interpreter initialization | 37 / 37 | Pass |
| Exception already pending at observer entry | 0 / 1 | Original interpreter error recorded before new imports; authorization denied |
| Deliberately retained shadow `sqlite3.py` | 0 / 37 | Original RuntimeError, import stage and file recorded; authorization denied |
| Long import chain | 0 / 1 | Originating frame survives the bounded receipt; authorization denied |
| Deliberately failing `ctypes` dependency | 0 / 1 | Constructor/import stage recorded; authorization denied |
| Deliberately failing native `fcntl` import | 0 / 1 | Native import stage and ImportError retained; authorization denied |
| Changed `FileIO.writable` descriptor | 0 / 1 | Exact descriptor-reader stage recorded; authorization denied |
| Missing required VFS File entry point | 0 / 1 | VFS installation stage and AttributeError retained; authorization denied |
| Exception whose `__str__` raises | 0 / 1 | Original exception preserved; authorization denied |

The same deliberately retained dependency under the unchanged `9e9ef198`
headers produces 37 generic failures with empty receipt details. This is a
controlled example of the diagnostic ambiguity, **not evidence that the Fold
has a shadowed dependency**. Retained fixture bytes are hash checked before
and after the tests.

Additionally **57 existing native Python cases**, **8 SQLite cases**, and
**16 source contracts** pass locally. These include real user-data fsync EIO,
real procfs writes, cached writers, callback overrides, descriptor races,
Command Center/compatibility saves and save failures. The full existing
**61-case** host gate remains in CI, including its private-mount vendor,
exact Pillow, and ambient-library cases. All 308 Android tests remain intact;
they have not been rerun against the diagnostic-only native changes yet.

## Required configured-installation comparison

The user's environment is the modified Infinity APK/engine, Diggz add-ons,
providers and enabled background services, **custom `skin.infinity.diggz`**,
and retained databases/settings/profiles/add-on state from in-place upgrades.
Stock Diggz skin and an empty installation are not equivalent.

The exact available skin archive is version **1.0.5.223**, archive SHA-256
`557003afc83a2661fec6ccef921979e264ff28e93595fb633340c618ab69bd56`.
Its `addon.xml` SHA-256
`917de56a4c31d97b74ae62d0b1a87ba6129dd95d99cdb4accae550e88a00585e`
matches the installed-code observation in the physical diagnostic. The
archive contains only the skin; it does not contain the complete ecosystem
or the user's data. Skin match alone is not a configured-installation match.

| Comparison | Current status |
| --- | --- |
| Fresh internal APK, approved first-party add-ons | Prior 38868115575 passes; basic control only |
| Fresh APK with matching Diggz ecosystem, custom Infinity skin and services | Not executed; complete matching add-on payload/configuration unavailable |
| Upgrade APK over verified copy of existing Fold state | Not executed; verified current Fold backup unavailable |
| Host 37-interpreter count/concurrency controls | Pass; does not establish the configured APK will pass |

An exact installation-state comparison would require verified Fold state.
That is no longer a prerequisite: compact logs supplied the actual traceback.
Any later installation-state comparison
must occur in disposable installations with backup hashes, database integrity,
enabled service/version inventory, module origins, observer counts, owner
receipts, both Java seals, whole-UID death and preserved-data reopening
recorded separately for each case. A fresh control passing cannot attribute a
defect to retained state.

The physical Fold has not been accessed, uninstalled, cleared, or altered.
No new APK is ready for promotion, and no physical approval or final lock
has been inferred. The targeted correction requires matched native/Android
acceptance and subsequent physical review.
