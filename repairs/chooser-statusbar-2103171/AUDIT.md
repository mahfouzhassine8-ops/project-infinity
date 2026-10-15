# 2103171 chooser status-bar surface audit

Base: exact passed/locked 2103170 Run #10, commit 6046c0ac64c7ef83a65550d53ffd4211c6cb5bef.

## User-visible defect
With the HM 2.0.3 light chooser, the chooser body renders correctly but the Android status-bar region remains black. The prior 2103170 repair applies to InfinityLiveActivity; the experience chooser is owned by a separate Splash Activity, so it never received the same transparent edge-to-edge/status-icon policy.

## Scope
Only Splash.java.in chooser presentation is changed. InfinityLiveActivity, PiP, playback, provider/EPG, background playback, rotation ownership, native Kodi, the HM 2.0.3 ZIP and all chooser launch actions remain untouched.

Both themed chooser paths now draw behind a transparent status bar, disable the OEM/framework status contrast scrim, use the resolved chooser background as the decor underlay instead of black, choose dark status icons for light backgrounds and light icons for dark/OLED backgrounds, preserve safe-area padding through transient zero-inset handoffs, and do not take navigation-bar ownership.

Legacy/corrupt-theme fallback remains byte-protected and outside this new policy.

## Gates
CI reconstructs exact 2103170, applies this chooser-only delta, compiles/signs over the same locked 2103168 native APK, compares signer/native/assets/resources to the passed 2103170 APK, repeats all 118 passing 2103170 Android tests and adds 7 chooser-window tests for Light, Dark, OLED, styled fallback, transient-zero insets, settings dialog persistence and legacy fallback isolation.

Physical Fold/OEM SystemUI confirmation is still required before this candidate is locked.
