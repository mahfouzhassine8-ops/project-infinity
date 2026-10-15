# Native protocol startup repair 2103343

Test candidate over 2103342; no locked or accepted lineage change.

## Confirmed incident

Kodi_Diagnostics_20261009T025917Z-5d958387.zip identifies installed APK 2103342 and current PID 2778. Its current log records native startup owner publication failing at read_metadata errno 61, followed by Command Center 0.3.5.20 throwing PersistenceError: native checkpoint engine identity/API mismatch in checkpoint_runtime.store_for. The service and Resume Hub plugin listing both fail at that ownership check. Native BeginEngineHandshake writes only engine.json during startup publication. The uploaded Kodi ZIP lacks the chooser's checkpoint receipt and therefore does not identify the failing attribute name. No particular attribute or Android filesystem defect is assumed here.

## Repair

The generic user-state replacement helper was also being used to replace native-generated engine.json/request.json protocol messages. Those messages now use a dedicated, allowlisted protocol writer. It creates a fresh 0600 sibling in the same .android-checkpoint directory rather than transplanting the retired message's inode metadata. This matches the participant's existing fresh-file protocol publishing semantics. The serializer and schema are unchanged.

The two-record allowlist excludes user settings, Resume Hub data, journals and other files. SaveDirty remains the default strict metadata-preserving writer for user state. The protocol writer shares its checked directory traversal, regular-file validation, unique temporary creation, bounded writes, chmod, close, atomic rename, file fsync, directory fsync and cleanup. It retains the old record until successful rename; a failed directory sync/close cannot be acknowledged. Symlink rejection and the persisting-thread check remain. Native owner-lease/death/CAS checks run before engine publication and are unchanged. Engine/API mismatch is not ignored; the intended repair is successful publication of the correct current identity.

Failure logs now include the syscall, attribute name and file basename already present in the 2103342 coordinator receipt, so Kodi Health Center logs can identify any subsequent user-file blocker too. No attribute values are logged.

## Validation

Real POSIX protocol replacement tests inject unavailable metadata and verify it is not consulted for these fresh control messages. They check private new mode, changed inode, both fsyncs, retained original bytes/inode on pre-rename failures, rejected directory sync/close, fixed-name allowlist and symlink rejection. The unchanged user-file policy still fails on ENODATA and preserves user bytes. The actual native XML wrapper is exercised for unauthorized protocol publication and rejection of settings.xml. The production coordinator harness uses the real protocol primitive while peer fixture writers model the participant's separate protocol publishing; all 30 owner/admission/checkpoint scenarios run, including prior-owner CAS, live-owner rejection, malformed prior identity and lost lease. Packaging, engine identity and full source preservation gates remain required.

The reconstructed Infinity checkpoint shutdown and selected Kodi 22 StopPlaying lock-order repair remain present. Native dependencies/compiler cache restore from green run 37873804330. Full ARM64 compilation, Android shell compile, inherited/new tests, asset preservation and permanent signing run in Actions.

## Device acceptance

Install over the previous candidate without clearing data. Open Infinity, allow services to load and check Command Center/Resume Hub. Request Normal Close once, export the chooser's Infinity Health Center ZIP before Force Close, then reopen after confirmed engine death. The target is current startup identity publication and removal of its consequent Command Center error. A full shutdown pass still requires matched persistence confirmation, authorization and observed owner death; unknown add-on writers and user-file failures remain blockers.
