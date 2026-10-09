# Shared raw I/O and add-on settings repair 2103345

Candidate over 2103344 on the isolated checkpoint branch. No locked or accepted lineage change.

## Physical failure

Infinity-Diagnostics-20261009-002439.zip identifies APK 2103344, PID 14940, owner b92305a9-cf5b-4892-a0a3-cb2da84df71a and close session 91ae61b5-eca5-4824-9937-fb558c593ba3. Checkpoint failed after 1857 ms. The first script-ledger failure was file_open_bypassed_checked_buffer_observer in context.seren:service.py (invoker 1). Command Center's later missing receipt (invoker 40, default.py) is not proof it originated the file-open failure. No saved checkpoint, SAFE receipt or consumed termination authorization exists for this run.

The same PID crashed at epoch 1791519873050 on thread 15133 (Thread-3), SIGSEGV, fault address zero. Android's retained tombstone records the crash handler's re-raise stack, not the original stack. The independent original-PC capture gives 0x6f1a831c10. The matching process mappings place libkodi.so at base 0x6f19236000, yielding ELF address 0x15fbc10.

The retained 2103344 engine from run 37881036799 matches DELIVERY.json's unstripped SHA-256 d692445b4dd182ca3a0cb90ef956f6c3ffe25f7c022be1dd90972095f18f1e67 and source commit 9fed0129e1384d062033eb1e491fb280a439850c. Its symbols map that address to GetSettingValue<CSettingInt>, legacy Settings.cpp line 28. Instruction 0xf9400008 is ldr x8,[x0], the load before the settings IsLoaded virtual call. The source dereferences settings without checking for a missing shared owner. A host test of the actual pre-patch helpers reproduces the null dereference under UBSan. This establishes a real defect consistent with the captured original fault.

Identity limitation: the phone tombstone and native engine have no GNU build ID, and the crash helper's hard-coded native_engine_sha256 is an inherited value rather than this engine's digest. Attribution uses the installed candidate, matching PID/timing and mappings plus retained build association; the crash record alone does not cryptographically authenticate the installed engine. No caller stack or underlying reason the settings owner was absent is recovered.

## Confirmed shared file-tracking gap

A real CPython subinterpreter running a normal import of a newly created module reproduces the same file-open bypass failure before this repair. CPython's bytecode-cache path uses _io.FileIO; it was absent from the checked buffer adapters. That is a shared observer defect. The uploaded receipt has no path or Python stack and cannot prove the particular Seren operation was a bytecode-cache write.

_io.open and _io/io.FileIO now have checked adapters retaining their native argument behavior and type inheritance. Writable raw descriptors join the buffer/path ledger. BufferedWriter, BufferedRandom and TextIOWrapper layers are tracked too, so admitting a raw descriptor cannot silently discard bytes in a later-added buffer. Observer finalization flushes all layers before closing them from outermost to raw. A failed flush preserves open buffers and denies finalization; write/open/close failures remain sticky. Cached original constructors still fail native audit rather than receiving an exemption. Pending SQLite transactions, opaque writers, worker threads, actual interpreter retirement and filesystem/directory sync remain mandatory.

Add-on settings scalar/list reads reject a missing owner before dereferencing it, preserving the existing invalid-setting exception path. Scalar/list writes likewise fail rather than fabricating success and record an addon_settings checkpoint failure when applicable. Valid settings behavior is preserved.

A remaining audited file-open bypass now includes a bounded path, flags and up to four Python source frames in failure_detail. Capturing that evidence preserves the caller's pending Python exception. The first failure's details remain sticky when later writers fail.

## Validation

The pre-patch fresh-import reproduction fails; the repaired native subinterpreter test passes and reaches file/directory sync after actual interpreter retirement. Tests cover checked direct raw opening, bytecode caching, text-over-buffer-over-raw saving with verified bytes, failed raw and layered writes, retained pending layers, cached-constructor bypass refusal, unfinished SQLite transactions, worker retirement, handled SystemExit and new cleanup errors. Production settings helper tests under UBSan cover null owners, unloaded/empty/missing/wrong-type settings, valid scalar/list reads and writes, and failed-write accounting. The native CI recipe runs this new test before ARM64 compilation.

All 30 production coordinator scenarios, production invoker/ledger lifetime harness, existing observer failure scenarios, strict native file/protocol write tests, package tests and engine-identity test pass locally. The manifest preserves all 9,374 protected parent hashes, changes only six native overlay hashes and adds Settings.cpp to the reviewed changed set. Android source/assets remain inherited from 2103344. Resume Hub / Command Center / compatibility participation, owner protocol publication and selected Kodi 22 StopPlaying lock-order repair remain.

Full source reconstruction, preservation gates, ARM64 and Android shell compilation, inherited tests, asset comparison and permanent signing remain required in Actions. Dependency/compiler cache restore begins with successful run 37881036799. Build green is not physical device acceptance.

## Fold acceptance

Install over 2103344 without clearing data. Allow services to load; inspect Command Center and Resume Hub. Try Normal Close once and export Infinity chooser diagnostics before using Force Close. After a confirmed close, reopen and check resume position, watched state, settings and favourites. A pass requires a matched SAFE receipt, consumed authorization, observed owner death and preserved user state. Another failure should show the actual file path/frames when the remaining blocker is an unchecked file open. Independent add-on failures remain possible.
