# Current native refusal: vendor uname candidate

Resume point: `91a5326e`. Run `38837555854` failed actual Close in 3,374 ms:
13/16 essential owners completed, native admission refused an existing
`/vendor/bin/uname` candidate, and database/deferred-state owners stayed pending.
The earlier Addons.GetAddonDetails fixture failure is resolved in newer runs.

CPython supplies every PATH candidate to fork_exec, including candidates after
the selected `/system/bin/uname`. The native observer checks that actual list.
The existing vendor candidate cannot use the absent-executable contract.

The correction recognizes only `/vendor/bin/uname` as a root-owned symlink to
the root-owned, executable, non-setid `/vendor/bin/toybox_vendor`, with both
paths on actual read-only mounts and the resolved inode identity matching.
Other executables, targets, writable partitions, ambiguous identities and
arguments remain refused. Existing argv, environment, inherited descriptor,
child-output lifetime and final durability checks remain mandatory. No add-on
identity is exempted, no timeout changes, and no service is reported saved.

Source review used AOSP `android-11.0.0_r48`:

- https://android.googlesource.com/platform/external/toybox/+/refs/tags/android-11.0.0_r48/toys/posix/uname.c
- https://android.googlesource.com/platform/external/toybox/+/refs/tags/android-11.0.0_r48/Android.bp

The uname implementation calls uname(2), prints selected identity fields to
stdout, and prints a newline. The system and vendor builds share the applet
sources. Output remains leased because redirecting even a read-only command's
stdout/stderr to an essential file is a real write.

`test_vendor_uname.py` exercises the production identity function against
actual immutable/writable mounts, symlinks, ownership and modes in a private
mount namespace. Its host executable is a topology fixture, not an assertion
about the Android binary. Existing CPython tests and an actual Android rerun
are required. The independent Java pending-write blocker remains unresolved;
this correction alone does not authorize delivering an APK.

## Newer Android result and correction

Full native run `38842156316` passed at `a543811a`; actual Android run
`38843193133` at `a3ec8e0c` still failed. The app's SELinux context cannot
stat `/vendor/bin/toybox_vendor` (`avc: denied { getattr }`). Root-shell
observations were not sufficient proof for the app process. Essential native
admission remained failed, with native databases and deferred dialog state
pending; the package did not terminate or reopen.

The observer now supplies the exact already-selected system executable to
CPython only for an existing approved information command, with every PATH
directory root-owned, non-writable, and on an actual read-only mount. Arguments
and `Popen.args` are preserved. Native validation of the selected executable,
arguments, environment, actual output descriptors and child lifetime remains
mandatory. An inaccessible later candidate is no longer part of the executed
candidate list; it is not granted an exception or treated as saved. Writable
search paths and unknown child commands retain the existing refusal.

A new native-host regression executes real `uname -rs` under an unprivileged
UID while a later vendor symlink is actually inaccessible, and checks the
exact candidate tuple received by the production native hook. This revision
requires a fresh full native build and actual Android process test. Java
producer admission is checkpointed separately, pending full 274-case
regression plus new save-ownership tests. No physical Fold success is claimed.
