# Physical Fold acceptance — required, not yet performed

This protocol does not grant acceptance. The exact candidate must first pass
compilation, signing, member preservation and Android 17 integration gates.
Version code alone is insufficient: the internal candidate and its parent both
use 2103401. Record the installed APK SHA-256 and permanent signer fingerprint.

## Preserve the existing installation

Use the existing Fold profile, add-on locations, databases and settings. Do not
clear data, move directories, edit provider code/databases, disable services or
change quarantine policy to obtain a passing Close. Do not enter Cobra or alter
its settings, code or shared infrastructure. Do not install the disposable CI
fixtures into the user's existing profile as part of this protocol.

Retain startup crash/tombstone evidence as well as Close receipts. An Android17
emulator run crashed in the unchanged talloc constructor before Kodi startup;
the underlying unmapped auxiliary pointer remains unexplained. Later successful
Closes cannot erase that failure, and physical startup/reopen reliability must
be checked explicitly.

Record the Android version/build, Infinity APK identity, active versions and
enabled states of The Crew, Umbrella, Seren and POV. Record the actual Version
Check service version if installed; the bundled desktop subprocess failure is
a distinct unresolved compatibility case, not a reason to waive persistence.
Keep account tokens and credentials out of the report.

## Record semantic preservation before testing

Record representative Resume Hub entries and positions, watched-history entries,
provider settings, favorites and add-on/profile paths using existing app views.
Use stable identifiers and expected values, not screenshots containing account
credentials. A changed SQLite file hash alone is not evidence of data loss:
normal transactions and WAL checkpointing can change its representation.

Verify ordinary provider navigation and playback through each installed provider
without modifying its implementation. Record an observed failure separately from
a test that could not be exercised because credentials or content were unavailable.
The host identity matrix is not a substitute for this real-provider test.

## Exercise at least five Close/reopen cycles

Cover idle service activity, completed provider settings writes, watched-history
updates through the existing UI, stopped playback with a Resume Hub position,
and active background service/worker activity. Use Essential-First Close each
time. Observe UI responsiveness while the checkpoint worker runs.

For every successful Close, retain the complete coordinator/native diagnostic
receipt and independently observe the original engine PID's disappearance.
Require the same checkpoint owner/generation throughout; completed required
writes for every mandatory owner; no remaining essential operation, buffer,
transaction or opaque-writer blocker; verified durability and consumed safe-exit
authorization. A script's return, a timer expiration or disappearance of a window
is insufficient. Reopen and verify a new engine session/PID and preserved values.

After a verified Close, perform database integrity/readback checks only on
consistent diagnostic copies opened read-only, if such copies are available.
Never repair, vacuum, migrate, delete or directly edit the user's databases to
make this check pass. Verify Resume Hub, watched history, settings and provider
functionality again after the final reopen.

## Preserve failure evidence

An unverified mandatory persistence state must withhold safe-exit authorization.
A completion-receipt failure after verified authorization must remain visibly
failed and retain the actual consumed authorization and observed engine state;
never rewrite that history or report COMPLETE without durable completion proof.
Retain its actual writer/invocation, interpreter/thread, operation, resource and
checkpoint generation. Do not force-kill the interpreter, clear the blocker,
reclassify profile data as optional, or disable a provider to manufacture success.
Null VFS arguments must retain their original TypeError. A verified rejection
before native write is a failed operation with no mutation, never a saved-write
receipt, and never settles another outstanding obligation.

The disposable Android 17 tests separately exercise invalid arguments, an
uncommitted transaction and an opaque external writer. Their expected failure
controls must remain visible in the qualification report alongside successful
cycles; do not inject faults into the real providers on the Fold.

## Acceptance record

For each cycle, record the exact APK, device/build, provider versions, prior/new
engine identity, checkpoint result, elapsed time, unresolved-operation details
when applicable, data/readback results and corresponding diagnostic filenames.
Acceptance requires real-provider functionality and repeated physical Fold
Close/reopen without data loss. Until that evidence exists, final_lock and
physical_fold_verified remain false and this repair is not permanently resolved.
