# Infinity consolidated project — Phase 0 / ANR evidence checkpoint

**Continuation:** The physical capture subsequently confirmed the reciprocal
graphics/directory owner cycle. Current implementation, builds and all five
workstream gates are tracked in `../fold-deadlock-20261017/PROGRAM.md` and this
directory's updated `CHECKPOINT.json`. The text below retains the original
pre-capture evidence checkpoint and must not be mistaken for current status.

All five workstreams remain one program: watched/Resume Hub/Watchlist, add-on
touch/recovery, native Android background/ANR, full skin polish, and integrated
acceptance. The real Fold ANR remains the first implementation priority.

## Verified starting state

- APK lock branch: `locked-infinity-apk-2103377-test4-user-fold-base-20261016`,
  commit `9dea86a7bf1896993e33ab885aa678a25eddaa0f`.
- Exact TEST4 APK SHA-256:
  `bcdcbed5aeaed0bf30e6e590d9ceda7c0177d780b12e98773fa9503beb793286`.
- Packaged native library SHA-256:
  `2f1597ecc4f8a0ee09f24e399aa738b96a876c7760eaec0ee0ad1a18bafd6929`.
- Matched native source commit `f5e3d9434d8a8c0918d1f4cc6758cf3704eb873c`,
  native run `38975950035`. Its unstripped library's `.text` matches the locked
  APK exactly: SHA-256
  `eb95501280431e17ff4b2b74e52fb98e3fc59b776ba0a20a1ed97534a14ed298`.
- Skin source lock `3cc1e1d5e0d5a21db9d19dd6882bd1c647603488`; exact .223 ZIP
  SHA-256 `557003afc83a2661fec6ccef921979e264ff28e93595fb633340c618ab69bd56`.
- Six recorded Command Center 0.3.5.20 hashes (addon.xml, default.py, service.py,
  plugin.py, context.py, resume_hub.py) match the installed overlay source under
  `repairs/android-checkpoint-shutdown/installed/overlay/script.infinity.commandcenter/`.
- The consolidated package passed every included SHA-256 check and both ZIP
  CRC checks. Original diagnostics and screenshots were kept private and unmodified.

## Corrected native trace attribution

This ELF's executable segment has virtual address/file offset difference 0x3000.
The supplied Fold trace's relevant libkodi PCs require file-offset to ELF-RVA
conversion. Raw symbol names in the trace are misleading for these sites.
The corrected mapping is independently checked against actual AArch64 branch
instructions in the exact packaged binary, not inferred from function names.

| Trace PC | Corrected function / source |
|---|---|
| 0x014adfb8 | CountingLockable::lock, Lockables.h:58 |
| 0x01bb59a8 | CApplication::LockFrameMoveGuard, Application.cpp:1816 |
| 0x0167cba8 | xbmc::getCondVisibility, ModuleXbmc.cpp:363 |
| 0x0168e190 | SingleLockWithDelayGuard, Window.cpp:52 |
| 0x0168cf34 | xbmcgui::Window::getProperty, Window.cpp:618 |
| 0x01a4f1ac | CDirectoryProvider::UpdateURL, DirectoryProvider.cpp:771 |
| 0x01b20d0c | CGUIWindowManager::GetTopmostDialog, GUIWindowManager.cpp:1560 |
| 0x023c9434 | CAndroidTouch::onTouchEvent, AndroidTouch.cpp:288 |

Final corrected attribution run: `38991071668`, job `117273384811`, source
`d6be716e80884394d63e5a9b431a78877affe879`. Earlier raw-RVA and section-alignment
runs were exploratory; they must not be treated as the final attribution.

The trace proves native lock waits in input, directory, and Python access paths.
The export does not identify the native mutex addresses/owners for the actual
stall. GUI label evaluation while holding a directory lock is a source path to
investigate, not a proved complete owner cycle. No speculative behavioral patch
has been selected or applied.

## Concrete next evidence step

TEST4 already contains `InfinityStabilityProbe`. Its automatic arm lasts 90
seconds; the supplied freeze occurred much later. Native owner tracking exists,
but this startup window cannot establish ownership during that long return.

The standalone `script.infinity.foldcapture` 1.0.0 helper checks the loaded
native library's exact hash and calls its verified exported `Arm(int)` for
7200 seconds. It acknowledges the actual native deadline. It leaves the
original eight-snapshot/512 KiB limits intact and adds no background service.
Its Export action copies only the recorder's current and previous files plus
version/checksum/PID metadata. No APK, skin, Rails helper, provider or save gate
is replaced. This is an experimental capture helper, not an ANR repair.

Host verification: ten tests pass, including execution of the original C++
recorder body through a real Linux shared library, deadline acknowledgement,
wrong-engine refusal, readiness/budget refusal, eight-snapshot cap, current and
previous export, malformed/oversized/missing evidence and scoped map discovery.
Five machine-code branch checks and a changed-native negative control pass.
These checks are not an Android/Fold ctypes or UI acceptance result.

## Outstanding program work

- Phase C: obtain same-attempt recorder + Android ANR evidence; establish the
  owner/dependency chain, implement a causal forward correction, build/sign it
  with the permanent signer, and perform the 5/20/45/90-minute Fold matrix.
- Phase A: implement approved blue badges and compatible cross-add-on identity
  integration over the verified .20 controller; preserve its current progress,
  manual actions, Watchlist/Collection, schemas and essential writer contract.
- Phase B: prove the failing custom 1193/50 touch path before modifying it;
  provide a safe disabled-add-on recovery route and test Otaku re-enablement.
- Phase D: complete screen/profile inventory and targeted skin refinement from
  exact .223 after the ANR/targeted-change gates. No broad motion edits yet.
- Phase E: combined runtime/physical regressions, experimental artifacts and
  rollback; user approval remains required for final lock/promotion.

The current branch adds diagnostic tools and evidence only. No application
runtime source or protected baseline was modified. The overall project is not
implemented or physically accepted at this checkpoint.
