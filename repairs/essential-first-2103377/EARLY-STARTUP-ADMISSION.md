# Early Close: admission before core and observer initialization

Latest Android attempt `38892686819`, source `7caf6186`, passed all 308
regressions, 14 update-receiver controls, permanent signing, signed TEST2/TEST3
preservation, fresh production Close/reopen and the populated 37-service TEST3
baseline Close. In-place installation retained all 46 compared settings,
favourites, preferences and database files byte for byte. The prior receiver
and directory failures are resolved in this evidence.

The candidate's actual early Close failed in 25,198 ms. No termination was
authorized. The receipt had **zero active, observed or retired Python writers**;
there were no observer initialization exceptions in this attempt. No essential
seal or durable checkpoint was produced.

## Current root cause and original writer

UTC log sequence:

| Event | Time |
| --- | --- |
| Kodi startup log | 11:33:00.926 |
| Power Close action launched | 11:33:01.667 |
| Close receipt starts | 11:33:01.760 |
| Keyboard layouts directory reported empty | 11:33:02.754 |
| Application Create fails | 11:33:02.755 |
| Checkpoint deadline fails | 11:33:26.880 |

`CKeyboardLayoutManager` reads `special://xbmc/system/keyboardlayouts` while
`CApplication::Create` is still executing. Both native `CDirectory::GetDirectory`
entry points use `CheckpointWriteGuard("directory-work")`. Request had already
activated Close; that guard rejected the required startup read. Create returned
false, so the normal application-thread save pump never ran. All owners
therefore stayed unconfirmed until the unchanged deadline. This is a core
startup/admission race, not another 37-writer physical observer failure.

The production guard negative control reproduces rejection before core
initialization, with no termination authorization. Native source pins verify
the engine entry and Application.cpp against the preserved baseline.

A further real CPython control closes mutation admission before 37 already
admitted interpreters start their observers. All 37 fail installation; one
captured original path is `python.source -> python.import.shutil -> zlib`, with
`WriteAdmissionClosed: Infinity protected write admission is closed`. This
proves that mutation admission also cannot close before observer installation.
The existing PyDLL(None) correction remains valid and byte-preserved.

## Targeted sequencing correction

The actual Android `XBMC_Run` entry now owns a native startup scope before
Create. It completes only after Create, CreateGUI and Initialize have returned
successfully. Early Close retains its identity, generation, original start
time and original expiry in CHECKPOINT_REQUESTED while accepted core startup
finishes. Required startup directory/jobs can continue; new playback and
optional cache commands remain rejected. Legacy teardown remains vetoed.

Kodi's `IsInitialized()` additionally waits for GUI_UI_READY, which can depend
on a startup animation. The checkpoint now accepts the independent successful
core-initialization proof; it does not set that UI flag or fabricate a save.
Every original essential save owner and durable receipt is still mandatory.
Actual failed Create/CreateGUI/Initialize never produces this core proof and
fails the checkpoint.

After core readiness, new script admission closes under the existing manager
lock. Already-admitted interpreters finish installing the native-owned
observers before mutation rejection begins. Observed() is recorded before
add-on bytecode, so this does not wait for add-on network work, timers or
service completion. A failed or missing observer still blocks authorization.
The original BeginWriteProtection, abort notification, callback saves, database
barrier, essential seal, Java seals and termination protocol then run.
The application-thread pump polls initialization; no blocking wait, timeout
increase, observer exemption or persistence waiver is introduced.

Successful and failed real writes made during initialization retain their
original native ledger obligations. No pending operation, dirty buffer,
transaction, save error or owner confirmation is removed. The old
unobserved-writer regression remains fail-closed; its refusal now occurs before
mutation admission rather than after trying to save unrelated owners first.

## Verification and limits

- 34 coordinator/entry/startup cases pass locally, retaining the original 18.
  They compile the actual staged entry and checkpoint Process branch, real
  coordinator, real write barrier and original CVariant; Kodi save/UI peers
  remain explicit host adapters.
- 15 complete JobManager cases pass, retaining all original 13 and adding
  required startup-job admission and genuine startup failure accounting.
- All 12 repository controls pass; all 16 original source contracts pass.
- All four existing observer race cases pass. The fifth is the 37-interpreter
  before-installation refusal counterexample: zero observed, no seal or
  authorization. This is expected negative evidence, not 37 successful saves.
- Full native CI retains the 61 Python, 11 identity/initialization, eight
  SQLite, seven directory, installer, file-save and authorization controls.
  New native binary markers prevent pairing a stale engine with this source.

Evidence: `evidence/runtime/test4-38892686819-early-startup-failure.json`,
`startup-admission-negative.json`, `startup-coordinator-corrected.json`,
`startup-observer-races.json`, `startup-repository.json` and source contracts.
Android artifact `12042654417` was verified against SHA-256
`e7be1e8d21d5ca46f61381d4a03f2b7161e994ee4de00de4c6f05f80b7444b4c`.

All 308 Android tests, Java runtime, permanent signing identity, signed TEST3,
read-only descriptor correction, repository correction, custom Infinity skin,
Diggz add-ons and user data remain preserved. No physical installation was
accessed or modified. Synthetic services are not the full Diggz/custom-skin
clone. A full native rebuild and complete matched early/loaded Android Close,
both Java seals, whole-UID death, integrity and reopening are still required.
No new Fold APK is promoted and no final lock is authorized.
