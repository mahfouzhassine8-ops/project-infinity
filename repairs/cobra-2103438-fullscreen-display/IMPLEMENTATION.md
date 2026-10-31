# Fullscreen Display correction from signed 2103438

Scope: Display popup ownership/reveal only. Signed 2103438 is the recovery input; Infinity 2103437 and all sizing calculations remain frozen.

The actual fullscreen Display icon (`aspect`) sends exactly one call to the original picker. For live channels that picker creates `channel-aspect`. In the baseline host reproduction the attached panel stays at alpha zero: repeated native anchored-layout callbacks cancel/restart the reveal before it becomes visible. The existing Cards one-reveal guard covered More and visual settings, but omitted Display. A second ownership case exists when an inactive Multi-View overlay is retained: native host selection prefers that non-null overlay even when it is GONE.

The correction extends the existing Cards-specific visible-player host and reveal guard to the five original Display sheet kinds (live, global, default and both custom editors). It runs only with Cards selected (the existing predicate excludes Pro) and excludes Pro Sports. No timer, alpha forcing, overlay copy, new menu, player callback, sizing policy or global UI change is added. Existing More/sun behavior is retained.

Only two existing methods and two private predicates in `CobraCardsLayout` are merged into the signed class. Every other method/field/nested class is copied from the original component. `CobraComponent.version` changes for truthful component metadata. Exact class definitions and method budgets are enforced after final DEX assembly. The second Cobra DEX is byte-identical.

## Verification interpretation

Robolectric API35 native-graphics tests use real production views, touch DOWN/UP dispatch through the Decor, native fullscreen handoff and sheet creation/reveal. Only stream metadata/player state/network are controlled. The final check translates the actual method-merged candidate DEX to JVM bytecode. This is host verification, not Android installation or hardware-decoder/Fold acceptance.

No Android device or adb runtime is attached to this workspace. The historical Android17 x86 Kodi constructor blocker is separate and is not evidence about Cobra Display. No identical emulator retry or native bypass is performed. The user screenshot is described in the scope document; actual screenshot bytes are not available here, so no new screenshot-inspection claim is made.

Mode 0 retains signed438 semantics: its label is Best Fit, but its existing fullscreen description explicitly says fill/preserve proportions/center crop, and the original transform implements that. PiP uses contain. This correction neither removes normal letterboxing from other policies nor changes this established calculation to reinterpret its label.

## Physical acceptance

Install over the existing app without clearing data. In Cards on the front and inner displays, enter fullscreen through the preview; press Display, Back, Display, close and reopen; repeat after Multi-View return. Verify all existing choices, custom sliders/reset and inheritance, then fold/rotate/resize and return from PiP. Confirm video/audio/subtitles remain continuous. Other modes, guides, theme settings, More/PiP/Channels and Infinity must retain baseline behavior. No shutdown acceptance is requested. Candidate is not automatically locked.
