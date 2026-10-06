# Infinity 2103313 — Cooperative shutdown candidate

## Exact parent and scope

- User-approved parent: **2103312**, `1.0.9-Cobra-Pro-Teams-RC1`.
- Parent APK SHA-256: `6d6543dda3d54fd8b4ff12cdf79995c198a399839a29e71e1bf741789332deed`.
- Parent source: `1df07a46469040bbeee6bae34b13b4b3f8a7970d`.
- Native parent: the exact 2103308 engine inherited through 2103312; packaged SHA-256 `b4b2630e37abd56a6e522ca633649a65b255b44bd6b39bcb9f8b84866b822aa6`.
- Skin remains **skin.infinity.diggz 1.0.5.201**. Retain Diggz Arctic Mirage 421 and installed user data.
- Only seven native source files change. All parent DEX, Cobra code, assets, Android resources and other native libraries must remain byte identical. The manifest differs only in version code/name. Use the permanent signing certificate.

## Captured evidence

The supplied October 5 log records Close Kodi at 21:28:12.405, quit acceptance at
21:28:14.300 and pre-destroy script cleanup at 21:28:14.307. The chooser runs in
a separate PID and draws its first chooser frame at 21:28:13.869, about 57 ms
after its activity creation (about 1.46 seconds after the close request).

Seven separate script invokers report their five-second stop timeout between
21:28:19 and 21:28:54: AutoWidget, JetProxy, Redlight, The Crew, TMDB Helper,
Umbrella and ExtendedInfo. Those messages request Python SystemExit; they do not
prove that all associated threads died. Other add-on startup work is still
appearing during the close. Capture ends at 21:28:55.803 without final native
completion. This proves repeated script stop delays, not the complete cause of
the reported six-minute wait or a crash in this capture.

## Repair

1. Preserve the pre-script settings/skin save. Close script admission before
   shutdown notification and serialize already-admitted thread dispatch with
   that gate so a registered thread cannot start after the stop pass.
2. Signal all current Python monitors together. A monitor registered later by
   an already-starting script inherits the shutdown signal under the same lock.
3. Start one monotonic five-second cooperative grace period for this shutdown.
   Repeated requests cannot extend it. Individual script stops outside shutdown
   retain their existing behavior. Existing Python abort escalation remains;
   the change does not impose a process exit deadline.
4. Release the script and service registry locks before stop/join callbacks.
   Retain shared ownership and iterate a snapshot because the message pump can
   remove registry entries while scripts are being stopped.
5. Leave final settings saves, Python/GIL teardown, native cleanup, thread joins
   and the native completion receipt in place. The chooser's completion ring
   still requires actual cleanup evidence and process exit. Close still exits
   to the phone launcher; reopening shows the independent chooser.

No add-ons are deleted, disabled or rewritten. No profile reset, automatic
timed process kill, native wait bypass or new user interface is introduced.

## Validation and limits

The host test compiles the complete production script manager plus the changed
Python stop, monitor and service-stop methods, with explicit dependency fakes.
Real C++ threads, locks and a real five-second clock exercise callback lock
access, reentrant registry removal, launch admission, all/late monitor abort,
unchanged ordinary abort, and seven unresponsive script waits sharing one grace
period. Python C API calls are faked: this is not a live Python runtime or ARM64
device test. Additional checks retain the accepted interpreter teardown and
the complete original final CApplication::Stop body.

Packaging tests reject changes to parent DEX/resources/assets/other libraries,
extra payload and incorrect native content. The build reconstructs the exact
locked native source map, runs the tests, recompiles the ARM64 library, verifies
the declared source delta, packages only that library and versioned manifest,
then verifies permanent signing and all protected payload bytes.

Physical acceptance remains required. A script blocked in a native extension,
network call or unrelated finalizer may still delay actual exit after the grace
period. This candidate is not automatically locked and does not claim that the
full six-minute delay is already resolved.

## Device acceptance

On the Fold, test Close Kodi and immediate reopen after both a short startup
and an ordinary playback session. The chooser must remain responsive, Kodi must
finish cleanup, and entering Infinity again must launch a fresh Kodi process.
Retest at 1/5/15-second reopen intervals. Export Health Center plus the same
logcat through final native completion if any wait persists. Check saved skin
settings, resume position and Cobra playback afterward. Record the installed
APK version with each run; historical exits do not identify their build.
