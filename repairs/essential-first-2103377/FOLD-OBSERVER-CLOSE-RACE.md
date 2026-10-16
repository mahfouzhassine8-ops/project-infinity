# Fold TEST3 observer setup versus Close

Continue from `a6178df6`; its full native run **38876390312 passed**.
No reset, baseline replacement, skin/add-on removal or physical-device mutation.

## Physical evidence

Collector `Infinity-Observer-Evidence-20261016-091504.zip`: 88,425 bytes;
SHA-256 `96f51b789338964303697c399945345ab9a0442278bd45afa2edfd8208f10a50`.
Five explicit reports in `kodi.old.log` show:

```
_infinity_native_persistence_observer.WriteAdmissionClosed
Infinity shutdown closed native mutation admission
Observer.__init__ -> install -> install_crypto_loads
ctypes/__init__.py:466: pythonapi = PyDLL(None)
ctypes/__init__.py:376: self._handle = _dlopen(self._name, mode)
```

| Event | Fold local time, 2026-10-16 |
| --- | --- |
| Kodi starts | 04:10:10.013 |
| Close starts | 04:10:15.907 |
| First observer exception | 04:10:16.700 |
| Failed checkpoint receipt updated | 04:10:41.045 |

Close started 5.894 seconds after startup; the first exception followed by
793 ms. The checkpoint separately records 37 generic initialization failures.
Duplicate suppression prevents assigning this exact exception to each writer.

`ApprovedNativeLookup` already classifies exact `ctypes.dlopen(None)` as safe:
it obtains a handle to the running process and loads no new image. But `Audit`
first calls the opaque-mutation guard, which rejects during Close phase 1 or
later. Observer setup never reaches the existing approved classification.
This is a native guard-ordering defect, not an established Diggz/skin/data defect.

## Targeted correction

Classify only event `ctypes.dlopen` with exactly one argument equal to Py_None
before opaque admission. All other libraries, symbols, native calls, imports
and persistent writes keep their gates. No observer-wide bypass or timeout change.

The regression pauses real CPython audit events immediately before production
Audit, begins the real Close barrier and releases the interpreters. No
production guard, observer, loader or durability result is mocked.

| Test | Original a6178df6 | Corrected |
| --- | --- | --- |
| Close at one PyDLL(None) call | 0/1 observed; exact exception; no authorization | 1/1 observed; sealed and authorized |
| Close at 37 concurrent PyDLL(None) calls | 0/37 observed; 37 exact exceptions; no authorization | 37/37 observed; sealed and authorized |
| Close after 37 initialize | 37/37 observed; authorized | 37/37 observed; authorized |
| Early Close native/write controls | Observer fails before controls | Unknown library, process open symbol, malformed audit arguments and protected file creation rejected; file absent |

The retained `late-ctypes` case now obtains the non-mutating process handle,
then requires both an unproven writer symbol and library load to be denied
after sealing. Its prior assumption that obtaining the handle was itself a
persistent write is corrected. The case remains in the 61-case suite.

Local results: 57 existing native cases, 11 initialization/identity cases,
4 Close race cases and 16 source contracts pass. Real fsync EIO, procfs writes,
cached writers and callback/descriptor uncertainty still fail closed.
Full 61-case CI, ARM64 build and all 308 Android tests plus complete actual
Android shutdown/reopening remain required before another physical test APK.

Failure details now include actual CPython interpreter and native invoker IDs,
alongside the ledger's service identity, original exception and traceback.
The 37-failure control checks distinct, correctly associated identities.

## Installation evidence and remaining limits

The collector found three skin manifests: two old repair payloads at 1.0.5.179
and the current `skin.infinity.diggz` 1.0.5.223. The current manifest hash
`917de56a4c31d97b74ae62d0b1a87ba6129dd95d99cdb4accae550e88a00585e`
matches the installed-code diagnostic. Its summary selected an old repair
manifest; that does not establish a skin downgrade.

Addons33's version-0 warning appears at both starts, outside this traceback.
It is not established as the observer cause. No database is changed or removed.

A full backup is not a prerequisite for this correction. After internal
acceptance, use the ordinary shutdown receipt and compact startup log excerpts.
Request specific module/configuration files only if a new trace requires them.

Host tests are not a complete Diggz/custom-skin clone. Internal Android is not
physical Fold acceptance. Signed TEST3, all 308 tests and user data remain
preserved. Final lock requires the user's physical results and approval.
