# TEST4 upgrade comparison: existing directory attempts

Native `38881674542` at `e9224dad` completed successfully, including all
61 native Python regressions, 11 initialization cases, four startup/Close
race cases and the complete ARM64 engine. Android `38882588772` at `ca58d72c`
passed all 308 regressions, signed TEST2/TEST3 preservation and the fresh
TEST4 production Close, both Java seals, whole-package death, seven database
integrity checks and saved-favourite reopening.

The same Android run failed before upgrading the separate disposable TEST3
installation. Its 37 synthetic services all reached their entry points,
then loaded Close failed in 5,238 ms with
`native_admission: protected_durability_failed:/storage`. This is neither
another physical Fold test nor a reproduced observer initialization failure.
TEST4 installation, early Close and loaded-upgrade acceptance were not reached.
The workflow withheld the Fold candidate.

## Original writer and exact production path

The synthetic `service.observerprobe.writer01` through `writer37` services
created missing profile directories using `xbmcvfs.mkdirs(root)`.
`ModuleXbmcvfs::mkdirs` calls `CUtil::CreateDirectoryEx`, which walks every
ancestor through `CDirectory::Create`, including existing `/storage`.
`CPosixDirectory::Create(std::string)` acquired `posix.mkdir` protection before
the actual `mkdir` syscall. `BeginProtectedOperation` added every attempted
path to the durable destination inventory; `mkdir` then returned EEXIST for
existing directories, with no namespace mutation. The URL overload accepted
the existing directory, and creation continued normally. Seal subsequently
attempted durability on those falsely inventoried ancestors.

The emulator mount table identifies `/storage` as tmpfs and `/` as read-only
ext4. The old receipt does not identify whether its failing syscall was the
directory sync, parent sync or open; do not invent that errno. The exact
classification defect reproduces with actual `mkdir(/proc)` returning EEXIST
and actual fsync refusal: the old production function registers `/proc`,
then denies authorization despite no successful mkdir. No access flags from
a file read are involved; the original writer is a native directory operation.

## Narrow correction

On Android, the existing-directory branch now uses `stat` to recognize an
already-present directory and returns the original false/EEXIST result without
attempting mkdir. The unchanged URL overload confirms existence as before.
Missing/unknown destinations still acquire the original full-operation lease
before the actual syscall. No recorded obligation is removed: a directory
actually created earlier remains tracked and must still pass durability.
There is no exemption for `/storage`, `/proc`, tmpfs, failed writes or add-ons.
Admission, SyncProtectedPath, SealEssentialWrites and timeouts are unchanged.

Seven tests compile the actual patched production Create function against the
real write ledger: existing non-mutating directory, genuine durable creation,
created-directory EIO, parent EIO, existing check after real creation,
failed actual creation and denied creation after final seal. All pass locally.
The unchanged function's negative control records EEXIST and refuses exit.
Native CI runs these cases against its actual staged Kodi source before build.

## Installation comparison

The upgraded-data control seeds existing service settings/profile directories
while the disposable baseline is stopped, then requires real baseline Close,
verified backups, in-place APK upgrade, early and loaded Close and reopening.
A separate candidate script must create a genuinely missing profile through
real `xbmcvfs.mkdirs`, save essential settings and survive the subsequent
complete production Close/reopen checks. This retains coverage of the directory
defect instead of suppressing it to obtain a pass.

The 37 services are synthetic; they are not a verified Diggz/custom Infinity
skin clone. No physical device data was accessed or modified. Signed TEST3
and all previous green native/Java results remain preserved. Full internal
acceptance and physical Fold approval remain required; no final lock.
