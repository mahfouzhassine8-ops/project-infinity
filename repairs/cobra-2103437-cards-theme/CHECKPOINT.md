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

## Follow-up verified progress

Final source-overlay host tests pass native palette/live restyle and cover/inner
geometry. Geometry comparison excludes only the intentionally changed background
paint; bounds, margins, padding, focus/clickability, model and other properties
remain checked. Initial assertions wrongly compared loading-entry alpha and
Light/Dark background hashes; those failed logs remain evidence. The final test
compares the same native restyle phase and tests native colors independently.

Dark and OLED each have byte-identical PNG output and identical complete shared
view snapshots between baseline437 Java and candidate Java overlays. These are
controlled host renders using the existing native435 fixture classpath, not APK
or device acceptance. Final Light capture inspected after the heading-span fix.

Owner compilation from actual437 component DEX succeeds: seven Cards classes
changed, two palette-adapter classes added, 7,161 original classes exact. The
signed drawer physicalLayout method is copied byte-for-byte into the patch
because recompiling identical Java otherwise renumbers registers. All remaining
method-level changes still need final review. No candidate APK is created.

The original immutable ModuleDexWriter rejected the five new palette-reference
fields. It remains unchanged. A task-local build adapter admits exactly that one
field/name/type in five explicit Cards classes, rejects every other addition and
all removals, and does not ship. Its exact admission and four negative cases pass
FieldGuardTest. These changes and source pins are recorded in SCOPE/OWNER-BUILD.
No failed original gate is relabeled PASS; the admitted field delta requires the
final independent method/field and APK-preservation checks before signing.

Current owner output: /tmp/cards438/owner-build03/owner-dex/COBRA. Remaining work:
finish method/field review, current-owner runtime binding and responsive/lifecycle
negative controls, matching components/unsigned APK, exact437 comparison, original
signer workflow registration and one signed testing APK. Infinity/shared/chooser
and the accepted437 baseline have not been changed. No release run dispatched.
