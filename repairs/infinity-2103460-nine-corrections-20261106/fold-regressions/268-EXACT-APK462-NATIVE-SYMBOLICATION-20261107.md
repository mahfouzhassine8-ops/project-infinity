# Physical Search-triggered native crashes — exact signed 2103462 symbolication

## Why this is new evidence
The prior 6.1 executor reported **“No usable execution environment”**, so it could not run native symbol analysis. **A separate current execution environment was usable.** Extracted exactly the signed **Infinity-2103462-Combined-Original-Signer.apk** from the previously original-signed GitHub workflow artifact `Infinity-2103462-Original-Signed-Build.zip`, and extracted its original `lib/arm64-v8a/libkodi.so` without altering it. No APK was built or installed.

- APK member `libkodi.so` uncompressed size: **637,990,184 bytes**.
- SHA-256 of extracted APK native member: **fadfb1a08e3d125958a77d393c1d66453ec3e9c91aac3349ec5806c67c17694d**; matches the repository's pinned native462 Downloads source-preservation evidence.
- **ELF is NOT stripped and contains DWARF `debug_info`**; `nm` resolves `CGUIKeyboardFactory::keyTypedCB` and `addr2line -afiC` resolves precise source paths/lines. Toolchain: GNU `addr2line`, LLVM `llvm-objdump`, `readelf`.
- The earlier Health Center `native_engine_sha256=704834...` uses a different producer's hashing representation; do not equate it with ELF-file SHA or claim exact runtime identity solely from this field. The user's 2103462 app identity, APK native source hash, and tombstone-derived relative offsets form the current mapping. Independently bind the mapped ELF to exact tombstone build identity if a contrary binary appears.

## 03:12:09 native SIGSEGV — exact instruction and source

From same-event `crash/native-crash-last.txt`, the original (pre-crash-reporter re-raise) fault PC was mapped in the tombstone to **`libkodi.so + 0x1b0daec`**. On the extracted exact signed APK462 native ELF:

```
addr2line -afiC -e libkodi.so 0x1b0daec
  CGUIKeyboardFactory::keyTypedCB(CGUIKeyboard*, std::__ndk1::basic_string<...> const&)
  kodi/xbmc/guilib/GUIKeyboardFactory.cpp:49

llvm-objdump -d --no-show-raw-insn \
  --start-address=0x1b0dae0 --stop-address=0x1b0db05 libkodi.so
  0x1b0dae8  cbz x0, ...          // rejects null keyboard pointer
  0x1b0daec  ldr x8, [x0]        // FAULT PC: dereference keyboard pointer's vtable
  0x1b0daf8  ldr x8, [x8,#0x28]
  0x1b0dafc  blr x8              // virtual call
```

**Interpretation supported by machine code:** Crash happens at a dereference of a **non-null `CGUIKeyboard*` argument** (the immediate null branch already precedes it). The recorded original fault address was `0x7e077d0064086e` (kept private in the original Health Center; avoid public circulation). This is consistent with an **invalid/corrupted/stale keyboard pointer**. It is **NOT proof** that the pointer is use-after-free, nor that both Python keyboard threads were Search invokers, nor that one global pointer is causally responsible. Investigate `CGUIKeyboardFactory::keyTypedCB`, the lifetime/registration of its callback, `g_activeKeyboard` ownership and teardown, concurrent invokers, event dispatch, and whether a callback may outlive its modal keyboard instance. The faulting native instruction is now precisely identified; **native symbol analysis is not blocked**.

The user **explicitly confirmed all three tombstones happened after tapping Infinity Search**, which invokes `xbmc.Keyboard(current, heading, False)` and `keyboard.doModal()` from first-party `infinity_search._open_search`. The same-event all-threads snapshot had **two Python-driven Kodi keyboard dialogs** in progress. This is a strong reason to inspect Search re-entry and callback lifecycle, but the exact invalid-pointer owner remains unproven. Merely preventing double Search activation in Python might not fix an already-dangling native callback.

## 00:47:26 SIGABRT — actual containers and touch/scaling source

The full tombstone faulting stack included native touch/window dispatch, a `CGraphicContext::SetScalingResolution` call and allocator/free abort. Exact signed APK ELF symbols:

| Relative native PC | Function / source |
|---|---|
| `0x1914fec` | `std::__ndk1::allocator<CPointGen<float>>::deallocate`, libc++ header `memory:1816` |
| `0x1912b3c` | `CGraphicContext::SetScalingResolution`, `kodi/xbmc/windowing/GraphicContext.cpp:721` |
| `0x1b3fb00` | `CGUIWindow::OnMouseAction`, `kodi/xbmc/guilib/GUIWindow.cpp:516` |
| `0x241274c` | `CAndroidTouch::onTouchEvent`, `kodi/xbmc/platform/android/activity/AndroidTouch.cpp:288` |

The source preserved in repository at `repairs/android-checkpoint-shutdown/runtime/native/overlay/xbmc/windowing/GraphicContext.cpp`, lines 709–732, shows **line 721 is `m_origins.pop()`**, executed while resetting GUI origin/camera/scaling state. In the observed stack, that ultimately freed a `std::deque<CPointGen<float>>` storage block, producing the Android pointer-tag truncation abort. **Exact ownership/race/memory corruption cause is not proven.**

The nearby `SetRenderingResolution` function (same source lines 734–740) wraps its call to `SetScalingResolution` in `std::unique_lock<CCriticalSection> lock(*this)`; direct calls to the latter must be traced to establish all required native lock/GUI-thread guarantees. **Do not add locks speculatively**: recursive locking, GUI dispatch ownership and shutdown reentrancy require source-specific analysis.

## 00:51:48 SIGSEGV
The final tombstone contains only the crash reporter's `restore_and_reraise` top frame. No original PC is available for this incident; the other keyboard-dialog threads are contemporaneous but not a causal faulting stack. **Unknown original fault function.** Do not transplant the 03:12 symbolication or invent a third cause.

## Next narrow engineering work — no extra owner tests now
1. Review **actual same-build native** `GUIKeyboardFactory.cpp`, keyboard factory `g_activeKeyboard`, callback registration/teardown and Android `CGUIDialogKeyboardTouch` lifecycle; inspect whether native `keyTypedCB` can run after keyboard destruction or concurrent close.
2. Analyze `SetScalingResolution` call origin and synchronization from `CGUIWindow::OnMouseAction` and touch gesture processing; isolate whether origin-stack corruption or cross-thread mutation is possible before choosing an APK patch.
3. Use existing signed268 Python sources to inspect `_open_search` single-modal ownership, but do not claim a Python-only gate repairs native pointer validity. Preserve strict provider settings/ABA validation. User's Fold video separately proves the 268 `search-open-verified` empty-directory navigation FAIL; do not promote it.
4. Only after actual causal proof, implement the **smallest source-matched native patch** and the authorized original-signature APK forward update if needed. Keep Cobra, installed APK462 and the four approved Infinity PASS features protected until owner accepts a new installed generation. Separate crash root-cause repair from Search result aggregation.

## What was actually verified here
**PASS read-only:** Extract source-matched unstripped APK ELF; native binary file SHA; resolve four supplied addresses through DWARF; exact fault instruction; inspect published native `GraphicContext.cpp` source line. Local Python 13-case earlier Search handoff fixture also runs, but **it does not simulate Kodi's native navigation and does not validate 268 behavior**.

**NOT DONE:** Rebuild native, fix Search result validation, fix the native bugs, sign new APK, install on Fold, reproduce/test. No new original signing keys, workflow modifications or user data edits.
