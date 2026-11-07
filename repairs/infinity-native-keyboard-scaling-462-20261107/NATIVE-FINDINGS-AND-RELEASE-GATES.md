# APK462 native keyboard and graphics engineering — 2026-11-07

This is a native correction candidate and measured investigation result. It is not a complete repair, installer, Android PASS, or release acceptance.

## Preserved references and actual execution

- Protected correction source: `86d5b5e2b65acb878632d407c3a3a07dd1af3b6d`, `work/infinity-2103460-nine-corrections-20261106`.
- Separate Search candidate: `72fefa8fe2554eb3fa7181027d6b9b2f05d7dd75`, `work/infinity-search-unified-native-candidate-20261107`.
- Both branch heads were verified unchanged in run [42366938495](https://github.com/mahfouzhassine8-ops/project-infinity/actions/runs/42366938495). No reset or merge of either branch occurred.
- Native work is isolated on `work/infinity-native-keyboard-scaling-462-20261107`.
- Installed identity remains the user-established APK2103462 / skin1.0.5.268 / Command Center0.3.5.61. No additional version or crash reproduction was requested.
- Execution used the repository's existing GitHub Actions controlled-native workflow, with branch-specific read-only/source/compile jobs. The unavailable local executor was not treated as a universal execution blocker.
- No private diagnostic archive, media, credentials, signing keys or user settings were copied into this branch.

## Exact APK462 source binding

The restored native tree matched **all9411 files** in the compiled APK462 map before applying the candidate. This is an exact current-source reconstruction, not substitution of older functional code.

- Original signed APK462 `libkodi.so` SHA-256, reused from existing source-matched symbolication: `fadfb1a08e3d125958a77d393c1d66453ec3e9c91aac3349ec5806c67c17694d`.
- Compiled APK462 source-map SHA-256: `8a4baedfa0f978a7eedfc332b935deef3572a9deb2d78d8cd488bf02ce7e740a`.
- Full source restoration proof: [42364232328](https://github.com/mahfouzhassine8-ops/project-infinity/actions/runs/42364232328), artifact13571276665, archive SHA-256 `9cd229acfcf0c8bd30b52ed083fa77ab640888fc04950a1e85f11465c79999c7`.

Original signed native symbolication and the reported historical fault locations were reused; no duplicate symbolication was run. These bindings do not manufacture an unknown original PC for the third historical SIGSEGV.

## Keyboard: causally reproduced defect and minimal candidate

**Confirmed source-level defect:** two native factory callers can enter the singleton touch keyboard concurrently. The second `CGUIDialogKeyboardTouch::ShowAndGetInput` replaces its `m_keyboard` unique_ptr before opening its modal dialog. That destroys the original `CAndroidKeyboard` while its worker is waiting on shared editor state. Waking that original worker produces an AddressSanitizer heap-use-after-free when the real `CAndroidKeyboard::ShowAndGetInput` reads the freed object's `m_owner` on its callback path.

The probe compiled the actual hash-pinned native editor, touch-dialog and factory method bodies. JNI notification, window lookup, modal scheduling and timer behavior were explicit host boundaries. It did not run Android.

This gives a causal native defect on the path leading to `keyTypedCB`, consistent with the invalid non-null pointer and simultaneous dialogs in the Fold evidence. It does **not** prove that this was the exclusive cause of that physical incident or all three recorded crashes.

**Only runtime source candidate changed:**

`native/xbmc/guilib/GUIKeyboardFactory.cpp`

- Original source SHA-256: `964e3c943a11f1bbed87c4529bedcd08c0111152954ff5b7140fb96c87ef3fb2`.
- Candidate SHA-256: `fdef3763a10d981649d4312d5f1646514b1e621829153ab9a0fa3900b8418df5`.
- Runtime-candidate introduction commit: `9173df8c812ead816ed7149ae794de9719130a0d`.

The Android-only factory modal lease uses a recursive mutex with **try-lock**, never a blocking acquisition. Both `ShowAndGetInput` and `ShowAndGetFilter` must own the lease before changing filtering/editor/callback state. A second thread returns false immediately. A same-thread modal reentry also returns false while `g_activeKeyboard` is active. The recursive lease permits the legitimate filter-to-input wrapper call before any keyboard is active.

The lease remains held through the existing modal return, cancellation, worker join and editor reset. Callback logic, JNI state registry, timers, touch controller, public signatures and normal worker drain were not replaced. Non-Android code paths are unchanged.

The unified diff is in the verified evidence artifact as `KEYBOARD-NATIVE-CHANGE.patch`.

## Keyboard verification

| Check | Actual result | Evidence |
|---|---|---|
| Pinned baseline overlap probe | Expected native program failure: ASan heap-use-after-free reproduced | [42365055708](https://github.com/mahfouzhassine8-ops/project-infinity/actions/runs/42365055708) |
| Patched overlap and reentry | PASS host ASan: overlapping input/filter requests refused before editor replacement | [42365578534](https://github.com/mahfouzhassine8-ops/project-infinity/actions/runs/42365578534) |
| Normal behavior in the focused harness | PASS: typed callback, filtering ownership, accepted input, cancellation, sequential reuse, editor registry retirement | Same after-probe |
| Actual Android ARM64 translation unit | Compiled successfully with pinned NDK21.4.7075529 and existing original dependencies; ELF64/AArch64/REL | [42365858072](https://github.com/mahfouzhassine8-ops/project-infinity/actions/runs/42365858072) |
| Ownership symbols in that actual object | PASS reconciliation using actual NDK libc++ recursive-mutex try-lock/unlock and unique-lock symbols; no recompilation | [42366436089](https://github.com/mahfouzhassine8-ops/project-infinity/actions/runs/42366436089) |
| Complete engine link | NOT RUN | No claim of a linked engine |
| Android runtime / Fold | NOT RUN | No physical acceptance claim |

The compile run itself ended **FAIL after successful compilation**, because the first symbol assertion incorrectly expected direct pthread symbols. The object uses `std::__ndk1::recursive_mutex::try_lock()` and `unlock()`. The later verifier authenticated the original compile artifact and job log, checked the actual libc++ ABI, and preserved the original failure. It did not rerun the compiler or convert the old run to green.

Object SHA-256: `f13f4aa269e77790f554616b63e80af3391895d352b26a546c1a7909e76fc6eb`;897856 bytes. The failed post-compile assertion occurred before the object-copy step, so the binary object itself was not retained in its artifact. Its compiler commands, source map, object hash/ELF evidence and actual nm output were retained; do not advertise an object binary download.

ARM64 compilation source: `bcb0c4d598b31fd74489eaa50bc2666388501b3c`. Successful evidence reconciliation source: `3430ee8091c0fab06a7a3ae47b3cf3c4f4afcd28`.

Verification artifact13571528023: SHA-256 `8403e4b804be82008fc0f38944c15843be4b9f653d8868946f69aa45c46e9ddf`. It contains the native diff and source-bound verification JSON, not an installer.

## Graphics: demonstrated ownership gap, no speculative patch

Exact-source trace:

1. Android touch-down calls `CGenericTouchActionHandler::QuerySupportedGestures`.
2. That calls `GUIWindowManager::SendMessage` directly.
3. Gesture notification dispatch reaches `CGUIWindow::OnMouseAction`, then `CGraphicContext::SetScalingResolution`, which resets `m_origins`.
4. `SendMessage` already holds the graphics critical section. Adding that lock again would not establish a repair.
5. `GUIWindowManager::Render` releases that graphics lock using `CSingleExit`. `CGUIControlGroup::Render` then calls `SetOrigin`/`RestoreOrigin` without that lock.

The bounded host ThreadSanitizer probe compiled the actual pinned `SetOrigin`, `RestoreOrigin` and `SetScalingResolution` methods. Under the documented render/input scheduling boundaries, it detected a data race between origin-stack mutation and the scaling-reset path, even while the input side held the graphics lock.

Evidence: [42366031630](https://github.com/mahfouzhassine8-ops/project-infinity/actions/runs/42366031630), artifact13571532510, SHA-256 `36b041a49362aedb15697771c19ec28b6757177c2f08236c6f31e20aebaf4d29`.

**Interpretation:** an actual source-level synchronization hole is demonstrated. Host libstdc++ scheduling and transform-math stubs do not reproduce Android's allocator/tagging internals. This does not exclusively attribute the recorded deque-free abort to that race. No allocator workaround, stack clearing, new rendering lock or touch behavior change was applied.

### Why a trivial message substitution is unsafe

The existing `CApplicationMessenger::SendGUIMessage` copies a const GUI message and returns void; it does not return the handler's gesture-mask pointer to the original caller. Substituting it directly would lose gesture information.

A borrowed-payload synchronous query additionally requires proven lifetime on queue rejection, dispatch completion, queue cleanup and window-system teardown. The exact native `SendMsg` implementation may skip its wait when the window system is absent. It is not enough to assume that a stack pointer survives.

Most importantly, the current APK462 `Application::Process` returns after `InfinityAndroidCheckpoint::Pump` while a checkpoint is active, before its normal `ProcessWindowMessages` call. The exact current `Pump` returns in `CHECKPOINT_FAILED` and does not drain those GUI window queries. A simple synchronous marshalling patch can therefore introduce a new stranded waiter.

Exact current checkpoint source SHA-256: `e8f617ac615d657ec0b37d1bef39d277ceafa8e2ad20bb2b6118cebae7f0350f`. Source lines1170–1186 establish the failed-Pump return; exact `Application.cpp` lines3414–3428 establish the skipped window-message pump. Current `Application.cpp` SHA-256: `fb5167b4fd7cb7fa16357fe367c9d212ae9440b4821870e4fd2d90018d9b4356`.

A source-binding check rejected the repository's older checkpoint overlay SHA `e2997a2a3ee58ad92d0835ee1031920e587bdd5b97d07274ebfdee553b26acdc`. Its initial attribution was retracted; run [42366938495](https://github.com/mahfouzhassine8-ops/project-infinity/actions/runs/42366938495) then restored and exposed the actual compiled-source version. The failed mismatch evidence is retained in42366808461.

**Current graphics decision: correction BLOCKED pending a proven query/response ownership and checkpoint-cancellation contract.** A proposed change must preserve the returned mask, keep GUI mutation on the rendering owner, own payloads through reject/drain/teardown, and acknowledge rejected queries without admitting unrelated UI work or weakening checkpoint protection. At minimum this crosses the existing window-message dispatch boundary; it cannot be called a one-line `SendGUIMessage` fix. No protected checkpoint or messenger code was changed.

The third historical SIGSEGV still lacks a proven original fault PC.

## Search coordination and other functionality

The Search branch is untouched. Its existing provider-native search architecture, result publisher, RPC leases, source checks and Python modal guard remain in place.

The existing host/source Search results in the supplied handoff are reused; they were not rerun or reclassified as Android evidence. Crew/Nixtoons settings-metadata false rejections remain unresolved. No timestamps, final-XML equality, retries, per-provider exceptions, source checks, dependency checks or cancellation guards were bypassed.

No new native settings-consistency API is supplied by the keyboard patch. The Search coordinator still needs a trustworthy complete semantic revision/save-order contract that detects intermediate meaningful/ABA changes while distinguishing proven bookkeeping changes. Earlier incomplete mutation-notification findings remain a constraint; a callback-only or final-file comparison is not sufficient. Settings-owner retirement remains BLOCKED and untouched.

Files white-graphic, Watched/Unwatched and Info/Cast corrections on the protected branch remain byte-preserved and are not overwritten. This native pass does not claim new Android verification of those UI actions. Power/Movies/TV/Downloads physical PASSES remain protected. No new owner test or installation was requested.

## Preservation and release decision

- Exactly **one** native runtime candidate differs from the exact9411-file APK462 source assembly; **9410 native source files remain byte-identical**.
- All repository edits are confined to this repair folder plus branch-specific jobs/filtering in the existing controlled-native workflow. The original native build job body is unchanged.
- No Search/provider/skin functional payload, Cobra, Preview, playback, shutdown, settings-retirement, data, databases, signing key, release authority or recovery lock was changed.
- Source evidence does not establish output-APK member preservation: **no successor APK exists from this pass**.
- No package/version number was issued or reused, no complete engine was linked, no installer was signed, and no installation/promotion/lock occurred.
- Signing, combined-APK byte comparison and matching forward-recovery gates remain NOT RUN until the coordinated candidate is complete.
- Unrelated shutdown suites were NOT RUN.

Release blockers remain: safe graphics ownership/cancellation correction; shared Search meaningful-change/ABA consistency; full coordinated engine/component integration; relevant actual Android verification; existing functional Fold acceptance; original-signature/preservation/recovery checks. The unresolved memory issue and unknown third fault are not represented as repaired.

The next native action is a narrowly reviewed GUI gesture-query ownership/rejection contract that can be verified without changing checkpoint durability. Do not ship the keyboard-only candidate or request piecemeal device installs as a complete successor.
