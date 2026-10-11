# Installer close repair 2103368

## Verified checkpoint

Continue from completed 2103367 commit `fa37772017bb5ccd4ebcc0761e937426c44d7c36`.
The protected 2103365 commit and APK are unchanged. Skin 1.0.5.207 and all
completed Command Center, media, recovery and diagnostics work are retained.

The new diagnostic is `Infinity-Diagnostics-20261011-073138.zip`. Its current
session is `d9616b46-56c2-4dbc-ac93-dc9060b7949d`, PID 23794, native producer
2103367. Closing failed after 9,504 ms. Sixteen owners finished; background
jobs retained seven `addon_install` receipts: two each for DistroTV EPG and
TMDB Helper, and three for Health Center. No close authorization was issued.
The older ANR and native-cleanup record belong to different processes.
Installed-code evidence reports Health Center 2.5.18; it does not establish
that a separately supplied 2.5.19 package installed successfully.

## Reproduced source defect

`InfinityAddonFileReceipt::OpenParent` opened every ancestor using `O_RDONLY`.
An app can access its own storage leaf while an ancestor permits search but
not directory listing. The extra read request fails, preventing capture and
commit receipts even when the ordinary VFS can access the installation.

The regression uses the production filesystem installer and receipt class in
an unprivileged process with a mode-0111 ancestor. The old source fails its
preimage check; the repaired source passes installation, rollback, nested
installation, exact restoration, uninstall and injected fsync failure cases.
The supplied phone diagnostic has no errno or failing path, so this establishes
a real defect consistent with the observed receipts, not the exact device
syscall or proof that every phone failure is resolved.

## Repair and limits

Use descriptor-relative `O_PATH` traversal for ancestors, retaining
`O_DIRECTORY` and `O_NOFOLLOW`. Open the actual parent readably for the existing
file/directory fsync and identity checks. Permission failures, symlinks,
dot-components, unsupported resources, failed writes and incomplete recovery
still fail closed. No fsync error is ignored and no failed job is discarded.

Add bounded `failure_detail` to blocking job receipts, distinguishing file
operations/errno from unresolved database writes without exporting user paths.
Only the diagnostic producer tag changes in the Android implementation.
The 17-owner protocol, authorization, process-death checks and navigation
behavior remain unchanged.

## Validation

- Nine production installer cases with a searchable, non-listable ancestor.
- Symlink/dot-component refusal and unreadable actual-parent refusal.
- All 21 existing filesystem/receipt and 21 DoWork cases pass.
- All 18 protected source contracts, five package tests and four preservation tests pass.
- Complete JobManager callback/lifetime and failure fixture passes.
- Full Android/native build and signed packaging run:
  https://github.com/mahfouzhassine8-ops/project-infinity/actions/runs/38137092930

No physical acceptance or release lock is claimed. The new APK must be tested
on the phone, including install/update followed by close. If close still fails,
the new receipt will retain the failed check and errno for the next repair.
