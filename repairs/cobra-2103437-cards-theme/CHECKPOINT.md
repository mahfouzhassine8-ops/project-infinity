# Cards theme correction — implementation in progress

Baseline: exact signed437; authorized branch is Cobra-only from437. Infinity,
other Cobra modes, shared/native libraries, chooser and shutdown are untouched.
No APK has been created, signed, installed, promoted or locked in this task.

Confirmed: Cards State.apply forces black after native theme publication; Cards
text and drawables use fixed dark values. Existing native cobraModeDark resolves
cobraEffectiveAppearanceMode and cobraModeColor reads palette.*. The adapter
uses these exact methods, including the existing `line` border role, without
changing appearance settings or global theme code. Dark/OLED return original
Cards colors. Existing geometry and callback bodies are retained.

Changed functional source: CobraCardsLayout, CobraCardsTiles, and the narrow
CobraCardsTheme native-palette adapter. No new settings, worker, listener or poll.
Theme publication uses existing afterRender/refreshDetails and tile bind/refresh.
The new theme repaint is idempotent; existing layout paths remain intact.

Java compilation passed. A source-overlay host fixture using the prior native435
host classpath passes one focused test cycling dark/light/oled/light/dark through
native cobraRestyleGuide and asserting actual native background/text colors.
Actual Light screenshot inspected. This is Robolectric API35, not signed437 DEX
or physical Fold acceptance. A final cached heading-span correction follows that
pass and still requires targeted verification.

Two early host attempts never reached assertions: the new test omitted the
existing fixture's paused Choreographer/frame-clock setup. Thread evidence shows
ActivityController.visible stuck in Choreographer queue scheduling. Restoring the
existing @Before setup produces a 7.2-second passing test. Neither stopped attempt
is a PASS. The source also avoids unnecessary progress invalidation when palette
is unchanged; no production hang has been proven from the failed harness.

Remaining mandatory work: dark/OLED painted parity against baseline; cover/inner,
recycled tile/selection/scroll/mode return tests; source-bound current owner DEX
build and method-level preservation; exact APK/Infinity/native/chooser comparison;
original-key release preparation/signing and matching ZIPs. No signing gate waived.

Current QA paths: /tmp/cards438/classes, host, host-test03.log; original owner DEX
extracted from verified437 components under /tmp/cards438/baseline-dex, disassembled
to canonical0 and canonical1. Existing pinned Android34 jar and D8 are under
/workspace/cobra-evidence/tools; host compiler can use the existing native435
production/support jars. Reference source remains signed437 commit31d55543.
