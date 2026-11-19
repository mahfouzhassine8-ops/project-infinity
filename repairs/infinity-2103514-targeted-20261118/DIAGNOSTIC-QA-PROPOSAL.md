# Proposed 2103514 diagnostic-only QA

The three-source patch from `301a6cd0` is the candidate diagnostic delta.
Its purpose is to correlate add-on IDs and separate the interpreter call
from the ledger wait during an intermittent occurrence. It does not implement
a repair. The existing installer and signing identity remain the reference.

**Native build.** Start from the exact `2103514` native source map and
preimages in `SCOPE.json`, authenticated by retained ARM64 run 43861331996.
Apply just `startup-boundary.patch` to a verified copy. Recompile the
participating native translation units and any users of the changed tracing
header, then link `libkodi.so` on Android ARM64 using the retained toolchain,
dependency configuration and build inputs. Reuse matching artifacts.
A ready-to-install APK cannot use the previous unchanged engine binary to
exercise new C++ markers. If verified matching objects are unavailable, the
existing supported native compile/link path is required. Cast Java, relays,
remuxers, resources and dependencies are already built and remain the exact
signed 2103514 members.

**Engineering checks before any install.** The existing focused host result
covers the two diagnostic boundaries, a NULL result, privacy, the process
gate and ring capacity. An actual build needs ARM64 ABI and dependency
comparison, manifest and signature verification, and a selected Android
startup run. Confirm marker order, instrumentation scope, normal Python
completion, working Home presentation and data ownership during install-over.
A normal startup is a diagnostic sanity check. It does not reproduce the
intermittent stall or establish a fix.

**Preservation.** Freeze the source and APK member lists before the build.
The payload allowance is the ARM64 Kodi binary and required version metadata.
Any extra runtime member or changed Cast/Cobra class rejects the package.
Compare signed member hashes, source maps and ELF exports with the reference.
Reuse the original signing workflow and package identity only if a diagnostic
install is separately authorized. Reconcile the available version code at
that point, leaving signed 2103514 protected. No version is reserved by this
proposal. A matching forward recovery would restore signed 2103514 content
with only the necessary version metadata changed.

**Limits.** Added trace records can affect timing and consume part of the
existing fixed ring capacity. The bounded add-on field adds about one MiB
to the ring. If Kodi stops draining events or the capture starts too late,
a missing marker can't establish a blocked call. A natural recurrence or
same-process stack is necessary to attribute the underlying cause. Continue
Playing has no runtime change in this proposal.

No build, install, signing operation, or new device test was started for this
proposal. Any later physical diagnostic capture is separate from repair
verification and release approval.
