# Infinity close status ring — APK 2103309 candidate

User-selected APK base: **2103308**. Skin **1.0.5.201**, Cobra and installed
Diggz Arctic Mirage 421 are preserved.

The Infinity chooser settings gear draws a cyan rotating arc while the real
close plan is WAITING_FOR_STOP, QUIT_QUEUED, DESTROYING or FORCED. The arc is an
activity indicator, not a percentage or an assertion that a stalled task is
making forward progress. It disappears only when the plan becomes COMPLETE
after `Main.super.onDestroy()` returns, or a close request is canceled before
Quit is dispatched. A fresh process has no active close plan.

Retain the last plan in memory without retaining its Activity. Losing the Main
slot or passing the 15-second observer cannot produce a false ready state.
The observer is read only: it does not quit, relaunch, save, reset, force stop,
or change the inherited lifecycle/routing policy.

Only InfinityExitCompletion.java.in and InfinityGlassChooser.java.in change.
The ring respects reduced animation, runs at most 30 frames/second while visible,
checks state every 250 ms when idle, and removes callbacks when hidden/detached.
Cobra's gear does not subscribe, poll, or paint the ring.

CI compiles and tests the actual production views and state machine, renders
light/dark cover/inner/landscape/short-window examples, compares disassembled
DEX classes outside the two declared owners, retains every base native, asset
and Android resource byte, and verifies the permanent signer. No native build.

Device test: Power → Close Kodi → immediately reopen Infinity. While cleanup
is active, the chooser must show the blue Infinity gear ring. When the old
process exits the chooser may close with it; reopening presents the normal
gear. A slow cleanup must never clear the ring because of a timer. Check
settings, fold/rotation/background-return and Cobra's normal settings gear.
Host tests cannot establish the physical device's shutdown timing.
