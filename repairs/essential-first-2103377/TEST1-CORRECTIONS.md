# TEST1 shutdown correction evidence

The actual TEST1 export reports CHECKPOINT_FAILED at `native_databases`, no
consumed termination authorization and no confirmed process death. First-party
callbacks and required jobs finished. Later settings, profiles and favourites
did not. Twenty-five blocking script warnings plus one native path warning
made the early database barrier wait until the existing deadline.

## Save admission and final authorization

`InfinityDatabaseBarrier::ReadLocked` now counts live protected operations,
dirty buffers and transactions for admission to essential save stages. It no
longer confuses historical coverage warnings with live database transactions.
Those warnings remain mandatory blockers in `SealEssentialWrites` and final
native authorization. No warning is fabricated as a successful save.

The compiled production coordinator regression verifies that settings,
profiles and favourites complete despite a historical warning, then final
authorization fails with that warning. Separate cases verify that active
protected writes and transactions still prevent unsafe save admission.

## Corrected production paths

- SQLite VFS observes actual main, ATTACH, URI, journal and WAL destinations,
  including transactions opened before Close. Tests commit protected
  transactions before sealing and reject writes afterward. Parent processes
  reopen the databases after actual host child death and check rows/integrity.
- CPython native entry hooks cover cached functions, existing file objects,
  raw/buffered/text writes, filesystem namespace changes and native Pillow
  encoder writes. Native descriptors cannot be spoofed through `fileno()`.
  Descriptor replacement and rename races keep active operations protected.
- The private SQLite inventory cursor disables only its own row factory;
  provider connection and result behaviour remain unchanged. A custom row
  factory reproduces the old inventory failure and now passes. The TEST1
  export does not contain IAGL's underlying exception, so device resolution
  remains unconfirmed.
- Successfully closing an observed buffer retires its original tracked
  identity without looking up the already-closed descriptor. This was
  reproduced by the unchanged Command Center durable save callback.
- Native pre-mutation admission rejections use a dedicated PermissionError
  subtype. They propagate to callers and remain diagnostic. Genuine failed
  saves, unknown capabilities, existing dirty buffers and transactions still
  block authorization. No failed essential participant receipt is waived.
- Invalid native POSIX descriptors return the original error before entering
  path verification. Valid writes and directory mutations hold real leases.
- The locked ambient image is verified against the existing audited binary
  hash `a876a76abe4faea63046953579899b0b7a67572722c2ed92331e41fcd1475684`.
  Thirteen exact entry points used by the locked script are bounded memory
  operations, mailbox reads or anonymous memfd creation. No image, ambient
  source, script, playback or skin behaviour is changed. Changed bytes,
  wrong locations, symlinks and unlisted symbols fail the contract test.

The ambient audit reuses the locked source archive
`repairs/infinity-ambient-surface-2103284/payload.*.b64` (archive SHA-256
`df30f27c3d8be9857a2e9a7f92471eac83cc7cf022a05b394211c1652eee42ad`).
The reviewed source hashes are `ambient.cpp`
`6146607a295ec451e5fab1c666f5b60b4530f83e11e59cea16bf859558f050d6`
and `surface_frames.cpp`
`b58e4ef088c729c9eb54da0f913aab51061b84d8d28d0c48bc7b1fcae22aa752`.
The host verifies the exact ARM64 image's contract; it does not execute that
ARM64 image or claim on-device ambient regression acceptance.

## Verification boundary

Evidence in `evidence/runtime/` covers 48 production CPython cases, 8 SQLite
cases, 15 coordinator cases, 13 full JobManager cases, 24 installer cases and
compiled native/Android receipt agreement.
The indefinitely waiting optional Python worker is still alive when host
authorization succeeds. Essential failures remain denied. No extra optional
wait, watchdog, interpreter destruction or fabricated receipt was introduced.

The full ARM64 build passed at `3acc3a9e`, run `38819025107`, including
the exact read-only `uname -rs` contract. Actual Android packaging passed
permanent signing and decoded instruction preservation against the locked APK
in run `38819866749`. The unchanged first-party fixtures were unreadable due
to root-adbd-assigned SELinux labels; no Close was attempted. The test now
restores platform labels on the backing path and records the actual add-on
inventory before querying individual approved participants. Enforcement stays
on, and no app startup code changes.

A further actual-child test found that a permitted read-only command could
retain protected stdout and write after sealing. The retained negative-control
result reports `seal=1; authorized=1` followed by changed protected bytes.
Native `_posixsubprocess.fork_exec` now captures converted stdout/stderr file
descriptors and transfers their existing operation leases to the real child
PID/start identity. Existing barrier observation releases them only on actual
child death. There is no watchdog, waiting thread, join, or new timeout.
Protected output prevents sealing until complete; pipe/private-cache output
does not become an essential obligation. Numeric output descriptors are
verified through the same native entry. Unsupported `posix_spawn` file actions
remain explicit fail-closed evidence. Forty actual CPython cases, the eight
SQLite cases and thirteen coordinator cases pass. This new correction still
requires a full ARM64 build. Host child-lifetime tests do not prove Android
whole-package termination.

Remaining safety evidence: the TEST1 export lacks call-site details sufficient
to establish that every reported Seren/Continuity failure is resolved; real
Android engine and guard-process death, data-preserving reopening and physical
Fold acceptance are unverified. The guard's `stopSelf()` is not evidence that
its containing process died. Unknown writes remain fail-closed. No new APK is
declared safe or locked by these host results. Optional unfinished private
writes can lose data or be corrupted; recovery is not assumed.

## Actual Android probe after restoring platform fixture labels

Run `38824020906` used the unchanged signed internal APK from the verified
`3acc3a9e` native source. Both approved add-ons were discovered and enabled,
SELinux remained Enforcing, and actual Close completed both first-party
callbacks. The native 25-second deadline was not changed. It failed at
`background_jobs`, with a repository callback still mandatory and a synchronous
`metadata.album.universal` install beginning after Close. This is a distinct
blocker from TEST1's historical-warning database-stage dependency.

Repository completion is now diagnostic, with unfinished job identity retained
in `optional_unfinished_jobs`. Its actual file and SQLite write leases remain
mandatory. The existing `CheckpointWriteGuard("jobs")` now covers synchronous
`CAddonInstallJob::DoWork`; rejected work has zero file/database mutations and
its original receipt proves unchanged state. Already-admitted installations
retain their original required receipts. Actual installer and SQLite failure
cases still fail closed. No add-on files or startup policy changed.

The probe also exposed `lsb_release` fallback execution as unknown child work.
The generic runtime contract now proves absence across every executable PATH
candidate on actual read-only OS mounts. Existing, relative, writable, unknown,
and unsupported executable paths retain their original blockers. Native output
leases still cover stdout/stderr. No exception is swallowed or retrospectively
converted into a save receipt. Host positive and negative cases use actual
exec failures on read-only kernel and writable cache paths.

The test-only Close intent no longer requests Android's first-frame wait:
this bridge activity finishes without presenting a frame. Receipt, identity,
25-second native deadline, actual process absence and reopen assertions remain.
The old test's 90-second `am -W` timeout did not negate its captured native
failure receipt. No process termination or successful reopen is claimed.

## Native child entry and error-channel verification

A second actual-child negative control called native `fork_exec` from a
`fileno` callback while a read-only Popen scope was active. The old hook
inherited the scope's trust without verifying the actual executable. A real
shell child changed protected bytes after `seal=1; authorized=1`. This failed
result is retained in `evidence/runtime/native-child-command-negative-control.json`.

The C entry now validates actual argv, every executable candidate, environment,
inherited descriptors, cwd and preexec options before granting the read-only
contract. Writable or unknown PATH candidates remain explicit blockers even
when a later candidate happens to execute successfully. Exact ordinary locale
environments still work. No third-party source or normal subprocess result is
rewritten. Pre-Close unverified execution retains a blocking failure receipt;
new native child admission during Close raises before spawning and remains a
diagnostic denial, consistent with the existing Popen audit gate.

The native exec-error output descriptor is also leased until actual child
exit. A real stopped child that will write its exec failure into a protected
file prevents sealing, then drains after OS-confirmed death. These cases and
all existing native cases pass (48 total). The earlier full ARM64 child-output
build `38824257676` passed, but neither it nor the pending admission build is
a deliverable for this newly reproduced protection gap. A fresh build and
actual Android verification of the final native source remain mandatory.

The first admission CI run failed because its `/sys` mount was writable, not
because a native protection was disabled. CI now uses a real read-only bind
mount in a private namespace, executes tests as the original unprivileged
runner and retains the real `statvfs` assertion. Host checks passed in run
`38827466985`. No coverage flag or fabricated receipt was introduced.

Native launch preparation also holds the existing operation ledger until its
PID/output leases are bound. A real concurrent fork pause verifies that Close
cannot seal in this handoff gap. The test pauses only its host libc boundary;
production has no waiting thread, join, timer or coverage switch.

## Actual Android save-stage findings and targeted correction

Run `38827602302` (native `82aac05b`) passed the former database admission and
required-job stall. Optional repository callback identity remained diagnostic.
Actual Kodi, profiles, skin, favourites, playback and both unchanged first-party
participants received completion receipts. Exit was correctly refused after
5.5 seconds with `loaded_owner_not_serializable` for `skin.estuary` and
`protected_durability_failed:/dev/null`. No authorization was consumed and
neither engine death nor reopening was established. The artifact and exact
owner outcomes are retained in `evidence/runtime/android-probe7-result.json`.

The settings ledger called `CAddonSettings::Save` on the skin's uninitialized
placeholder, although `CSkinInfo::SettingsToXML` owns and serializes the actual
values. The ledger now retains a weak owner serializer and invokes the existing
virtual method for the exact current instance. Stale or retained old trees
still serialize their own values; serialization failures and conflicts stay
blocking. No skin code, settings behavior or normal save callback is changed.
The original real-file owner tests are reused with the extracted production
callback, including failure, stale-instance and lifetime cases.

The null-device path was recorded by real writable opens. Final durability now
recognizes only actual Linux `/dev/null` character device 1:3 with matching
open/fstat inode/device identity. Unknown device destinations remain failures.
Real cached/buffered/raw/os/subprocess DEVNULL paths pass; `/dev/zero` remains
an exact durability blocker. All 50 CPython cases pass locally. These changes
must pass complete ARM64 compilation and the real Android death/reopen probe
before any physical-test candidate can be delivered.
