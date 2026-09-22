# Infinity/Cobra 2103209 — Python 3.11 GIL native stability candidate

## Protected parent

This candidate starts from the exact successful Infinity/Cobra 2103208 Integration Polish build and does not replace or modify that baseline.

- Parent build: 2103208 / 1.0.9-Cobra-Integration-Polish-RC1
- Parent workflow run: 35676573761
- Parent source head: a876bb6fd698635b55805f56ff5484cbb622736d
- Parent APK SHA-256: 9143271bb241290467f68aa922a0cf441ab2621575091857706ef97e1e46da2d
- Parent native engine SHA-256: e230a498a716ce0b82acedfce494fc521457af646c2f504965b247dcb5ee9281
- Parent generated Android source SHA-256: ca3995f542412e2cb91809c21f61fc8361bedab2fd0f463b0fe2ed057c1d949c
- Parent acceptance record SHA-256: 6e5cd284eac64bac1bf66d1867220381ab7b292507b85253fd02c25575d3ef4a
- Parent Android acceptance inventory: 740 tests / 77 suites
- Permanent signer SHA-256: d7adeb68e9341596a02bd3262b737a0f45fc6e771ed7e60285437e833b58c6d7

2103208 remains the rollback/reference artifact. This candidate is a forward test build only.

## Crash evidence and root cause

The 2103208 device tombstones repeatedly terminate in the embedded Python runtime while a Cobra/Infinity Python invoker thread is creating a sub-interpreter. The repeating chain includes `_Py_FatalErrorFunc`, `PyEval_SaveThread`, `_Py_NewInterpreter`, and `CPythonInvoker::execute`.

Infinity already carried the first Kodi upstream Python thread-state repair from PR #27320 / merge `0186f895271d4ce7d240b4e9f40da03b4833539d`. The Infinity backport, however, retained the first version's use of:

```cpp
PyThreadState_Swap(m_mainThreadState);
l_threadState = Py_NewInterpreter();
```

Kodi upstream subsequently fixed this exact Python 3.11 problem in commit:

`ddb60bd932b929724a9b0d2226043dc54d0d1912`
"[python] Fix python 3.11 segfaults due to python API usage without holding GIL"

That follow-up replaces the swap with `PyEval_RestoreThread(m_mainThreadState)`, which restores the thread state and acquires the GIL before calling Python APIs used by `Py_NewInterpreter()`. It applies the same correction to the failed-interpreter cleanup path.

2103209 layers that missing upstream follow-up on top of the existing Infinity thread-state/refcount hardening.

## Authorized delta

Only the following product change is authorized:

1. Rebuild `lib/arm64-v8a/libkodi.so` from the existing accepted Kodi 21.3 + Infinity/Cobra native source with the complete PythonInvoker repair set, including upstream commit `ddb60bd9...`.
2. Advance package identity to versionCode 2103209 / versionName `1.0.9-Cobra-Python311-GIL-Stability-RC1`.

There are no authorized Cobra UI, player, provider, timeshift/rewind, PiP, background playback, phone-call audio, visual-theme, branding, navigation, Quick Peek, file-picker, or resource changes.

## Fail-closed preservation gates

The workflow refuses to publish unless all of these hold:

- The downloaded parent APK, generated Android source archive, and acceptance record match the exact SHA-256 values above.
- The parent acceptance record still says 740 passing tests in 77 suites.
- Before recompiling the Android shell, the controlled parent APK differs from exact 2103208 in exactly one member: `lib/arm64-v8a/libkodi.so`.
- The rebuilt engine differs from the known 2103208 engine.
- Every other native library is byte-identical to 2103208.
- All APK assets, Android resources and `resources.arsc` remain byte-identical to 2103208.
- Current Cobra contract tokens remain present in the final DEX.
- Package name, permanent signer and non-debuggable release identity remain correct.
- Source verification proves the GIL is reacquired before `Py_NewInterpreter()` and the bad swap pattern is absent.
- The earlier Infinity thread-state race guard and refcount hardening remain present.

The 740 parent Android tests are cryptographically verified from the exact accepted 2103208 artifact; they are not represented as newly executed native-device tests. This candidate still requires physical device acceptance.

## Device acceptance

Install 2103209 as an update over 2103208. Do not uninstall Infinity and do not clear app data.

First stress the previous failure path with repeated cold launches and Python add-on/script initialization cycles. The previous build has reproduced this failure in only a few seconds, so rapid repetition is the primary first gate. Then run Cobra playback, stop/start, timeshift/rewind, PiP/background, provider, Quick Peek, theme and call-audio smoke tests.

After the stress pass, capture the native crash history again. Promotion requires absence of the old `_Py_FatalErrorFunc -> PyEval_SaveThread -> _Py_NewInterpreter -> CPythonInvoker` crash signature.

No lock/promotion is implied by a successful CI build.
