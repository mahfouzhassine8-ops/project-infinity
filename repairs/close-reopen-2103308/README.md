# Close → immediate reopen candidate

Exact APK parent: **2103307**, source `f0625ce0808310876a05b6c5513821336688e7f4`.
Locked skin: **1.0.5.201**. Cobra source/payload must remain unchanged.

The user's diagnostic ZIP contains an older ANR, not a new 3307 ANR. Symbols
from the exact inherited 3306/3307 native engine resolve the captured chain:

- Android main: Main.onDestroy → NativeActivity.unloadNativeCode → android_app_free:325.
- Native event loop: CXBMCApp::Quit → application-thread join.
- Kodi application: CApplication::Stop:2186 → service add-on Stop → PythonInvoker::stop:521 (event wait).

Thus Splash's focus timeout is a symptom of a shared Android UI thread blocked
in native destruction. This does not identify the offending add-on, prove a
permanent deadlock, or associate historical exits with the current APK version.

Candidate: stop service add-ons and remaining scripts cooperatively BEFORE
ANativeActivity_finish, on the existing Kodi application thread. Keep the native
event loop, Kodi messenger/GUI, and Python runtime alive during preparation.
Claim preparation atomically to reject duplicate/reentrant Quit messages.
Release and reacquire the application-owned GUI frame guard around script
cleanup. Announce OnQuit once and save a pre-script settings/skin snapshot;
retain the original final saves, cleanup, thread join and exit(0).

No timed kill, data reset, lifecycle callback moved to a worker, native glue
wait bypass, Python runtime change, skin change, or Cobra change is permitted.
This can leave the chooser responsive during a slow add-on stop; it does not
promise faster or universally bounded shutdown. An unrelated cleanup stall or
external task removal requires separate evidence.

Host tests compile the transformed production Stop method with dependency
fakes. They verify order/reentrancy, not physical Android responsiveness.
Native compilation, permanent signing and device acceptance remain separate.

Physical acceptance: preserve all settings, test normal close and reopening
immediately and after 1/5/15 seconds, then export Health Center diagnostics.
During cleanup the chooser must respond and must not start a second Main/native
runtime. Verify normal completion, no new ANR, successful fresh startup, and
unchanged Cobra playback/PiP/recording plus skin .201 and Diggz Mirage 421.
