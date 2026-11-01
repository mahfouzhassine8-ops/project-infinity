# Cards Preview restoration — signed438 comparison, retained439 Display fix

The latest locked approved baseline remains2103438 (`a5f721578c53e026a26cf21d929fbdad530f6d17`). Signed439 is retained as delivered; it has not been promoted. This continuation uses the existing branch and preserves its Display correction. Infinity437, native/shared libraries, chooser executable code and shutdown remain frozen.

The user confirmed the missing tap menu belongs to the SMALL Cards preview. The real signed438 host touch path promotes a small-preview tap to fullscreen. A long press reaches the original Preview controls menu but repeated anchored layout callbacks leave its panel at alpha0. Child Channel actions retains that original preview anchor and demonstrates the same failure. Working fullscreen-return preserves the current player/channel and is unchanged.

Cards also hides the original native `PulseView` while displaying its LIVE badge. Earlier global polish suppresses NORMAL/LIVE status states and permits animation only for BUFFERING/RECOVERING. Those global policies are preserved. Two Cards-preview-only guards restore the existing state/animator path for this owner. No replacement indicator, timer, layout or theme system is introduced.

## Narrow implementation

- The existing small-preview click callback opens the ORIGINAL Preview controls menu for Cards only. Pro/Pro Sports and other view modes retain the old callback body. Explicit Fullscreen and PiP remain their original actions.
- The existing once-per-panel reveal guard now recognizes the actual preview anchor and inherited child-menu anchors. Other sheet owners retain their old behavior; no arbitrary delay or forced alpha is added.
- The original LIVE label is drawn at its exact approved position directly under the same preview host, allowing the original StatusSlot/PulseView to retain its native corner. Native view identities/listeners are retained. Mode exit/paused state restores original label-parent ownership. No view is duplicated or replaced.
- `cobraVisualPulseState` restores original NORMAL/LIVE values only for the current Cards mini-player and only after the original active/priority/error logic. Global pulseState and the enum remain byte-identical.
- `PulseView.restart` retains every original foreground/attachment/visibility/reduced-motion guard, animator, duration1400ms, repeat/reverse behavior, colors and emblem. It admits NORMAL/LIVE motion only when the Cards-preview predicate matches. Unknown contexts, fullscreen, Pro, other modes and unrelated pulse owners retain their old behavior.

`InfinityLiveActivity` is the existing **COBRA-owned** class in classes4.dex; it is not the protected Infinity component. Only two methods in it are changed. Java/Dex method budgets require all other definitions to remain exact.

## Register / ownership review

The click callback expands from2 to4 registers: v0/v1 are new local scratch; original p0/p1 code remains unchanged under the legacy branch. The status method expands from15 to16 registers, preserving the incoming player in new local v13. The original body has no explicit v13/v14 accesses; original wide temporaries end at v12, so the saved reference survives. Existing parameter references remain symbolic p0/p1. The Cards override runs only after the original priority classifier returns NONE, with original active and live-edge observations. The PulseView restart patch changes no register/field set. The original field-default-preserving DEX writer and exact class/method comparisons remain mandatory.

The final method merge changes five of7170 existing Cobra definitions including required component version metadata; no classes or fields are added. Cards State/drawer/tiles/themes, all sizing policies, Pro/Mobile/Compact/Grid/Multi-View, playback controls and global effects policy stay exact. The previous439 Display host/predicates are carried forward; only its reveal guard gains the preview-owner condition.

## Focused evidence

Eight selected host cases pass across focused runs using actual final owner DEX translated to JVM, Robolectric API35 native graphics, real Decor-dispatched touch/long-press/menu actions and controlled player metadata/decoder entry. Tests cover original controls, pause/resume, nested Channel actions, fullscreen return, PiP terminal handoff, source/player identity, channel-selection routing, leaving Cards, native pulse lifecycle and system reduced motion. All14 existing size settings retain the menu and active pulse in56 front/inner light/dark cases. Additional palette cases include OLED. Active host cover/inner/orientation/split resizing and live light/dark restyling pass8 cases.

Actual signed438 versus candidate measured Cards outer geometry AND LIVE badge bounds/pixels are identical in4 front/inner light/dark cases. The restored native emblem is the authorized visual difference. Existing size math is untouched; the earlier439 geometry evidence remains valid and is not rerun as a new sizing repair.

The stock Robolectric ShadowValueAnimator replaces INFINITE with one repeat, explaining the otherwise eligible pulse stopping after two cycles in the resize check. The QA-only shadow preserves Android's requested infinite repeat; every test still advances a bounded number of paused frames. Production timers, assertions and delays are unchanged. The channel-retune fixture initially entered real decoder construction and met a missing host class; the decoder-entry spy was corrected to match boxed loose signatures. The real channel callback/start counter is verified once, without changing packaged dependencies or claiming hardware playback. Historical failures are retained.

Android17, real stream/audio/subtitles, actual hinge transitions and Android PiP acceptance remain physical Fold checks. No attached Android runtime is available; host viewport and controlled-player results are not device acceptance. No shutdown tests were run. The recovery lock and accepted-release pointer remain untouched.
