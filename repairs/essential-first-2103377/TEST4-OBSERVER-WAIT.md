# TEST4: initialized core, unobserved Python workers

Latest completed Android attempt: `38938908138` at `73de91ca`.
Native `38899217848` at `402dfe75` remains a successful full ARM64 build.

## Actual current failure

All 308 regressions, 21 boundary controls, permanent signing and prior signed
baseline preservation passed. Fresh production Close saved, authorized exit,
confirmed whole-package death, checked seven databases and reopened retained
data in 10,936 ms. The 37-service signed TEST3 baseline Close passed in
4,461 ms. The receiver checks and exact 46-file upgrade comparison also passed.
The previous process-name assertion is no longer the current blocker.

The upgraded candidate then attempted genuine early Close with zero services
ready. It refused termination after 25,182 ms:

`native_admission: checkpoint_deadline_exceeded; owner proof incomplete`

The receipt proves core initialization completed and startup scope ended.
However, native mutation admission never started. Its pending detail was
`python_persistence_observer_initialization` throughout the wait. All 41
admitted Python writers remained unobserved, with zero tracked paths, zero
blocking exceptions and no initialization-failed receipt. All 16 essential
owners remained unconfirmed because the coordinator never admitted their save
sequence. No essential seal, authorization consumption or process death passed.

This differs from the physical TEST3 exception receipts and the older aborted
keyboard-layout startup. It does not prove 41 separate add-on defects or a
specific failing Python import. The exact native wait was not recorded before
the observer's existing diagnostic context was created.

Artifact `12062921983` is SHA-verified:
`4071751ec2e354c24a3c64458c72acea74b7ee815eb3e5808b121e5ea81005d5`.
Compact exact receipt evidence is in
`../android-checkpoint-shutdown/runtime-tests/evidence/early-observer-wait-38938908138.json`.

## Source checks and limits

Official Kodi 21.3 XBPython::Process only removes finished scripts. Its
OnScriptInitialized performs Python initialization directly, without an
identified main-thread message handoff. Android's initialization preamble
imports xbmc and configures logging/module stubs; no identified GUI callback
explains this hang. Normal FrameMove still offers graphics/frame guard release
for external callers. A message-pump correction is therefore not justified by
the current evidence.

The 34 coordinator controls retain valid admission/seal/failure checks, but
their observer-pending adapter directly records Observed. They do not reproduce
Kodi's real cold Py_NewInterpreter/module/observer bootstrap. The runtime
observer's SQLite VFS installation also precedes its old initialization-stage
context. Targeted native progress must cover that earlier interval rather than
claim that a missing exception identifies a specific cause.

## Independent acceptance, not first-failure suppression

User-authorized verification `38944119153` at `8d9ec872` builds and signs once,
then runs three separate disposable AVD jobs:

1. Fresh production Close, actual save receipts, UID death and reopening.
2. Verified TEST3 in-place upgrade, early Close with fewer than 37 services
   ready, all essential saves/seals, UID death, integrity and reopening.
3. A separately seeded verified upgrade, all 37 services loaded, actual missing
   profile directory/settings write, full Close/death/integrity and reopening.

Failure of early Close no longer prevents loaded Close from running. Each case
retains its own evidence. Promotion requires all three successes, identical
tested APK hashes, all 16 individual essential owners, both Java seals and
strict whole-UID absence. Original 21 boundary controls, eight routing controls
and five failed-engine identity controls pass locally.

After a refused Close, the upgrade probe requests a native backtrace and saves
thread wait/maps only on the verified emulator and matching live engine owner,
PID and UID. This does not retry or extend Close, terminate the application,
change any save result or turn the failed receipt into acceptance.

Targeted native progress now records invoker entry, handler/GIL/
interpreter creation, Kodi module setup, observer entry, SQLite VFS installation
and existing hook stages. Eight new native controls, six status-size controls,
34 preserved coordinator controls, 36 local write controls, 11 initialization
controls and five observer race controls pass. Original exceptions and all
safety proofs remain unchanged. Auxiliary rows are limited to 64 and 24 KiB,
with current identity/stage prioritized over optional history. A nearly full
original status is returned byte-for-byte without auxiliary metadata. This
keeps all original safety evidence within existing Android limits. Full native
rebuild and matched Android verification are still required.

No add-on, Infinity skin or physical Fold data is changed. Synthetic services
remain a control rather than the full Diggz/custom-skin installation. Exact
native wait identification, corrected runtime acceptance and physical Fold
approval remain outstanding. No Fold APK promotion or final lock.

## Saved monitoring checkpoint

- Native progress source `eaa6ff3f`, full build `38945424322`: host proof passed; engine build running.
- Independent existing-engine Android `38944119153`: 308/signing and fresh case passed; early/loaded pending.
- Exact matched RC04 source `bb251ed4`, Android `38945702659`: running; full native success is mandatory before packaging.
- Both independent Android runs remain active under separate concurrency groups. No case is cancelled by a later push.

Implementation and acceptance setup are saved. Exact native wait identification,
all required runtime outcomes and physical Fold approval remain outstanding.
