# Actual owner-v2 host classpath preparation

Prepared only. No behavioral test, APK build, CI run, emulator, signing, or shutdown execution occurred.

The prototype input is the actual unsigned Cobra owner build recorded in `SOURCE-BINDINGS.json`, based on accepted signed 2103431. Root independently disassembled both owner DEX files with pinned baksmali. Preparation rechecked all 7,142 original canonical class hashes against the exact accepted Cobra component ZIP metadata: exactly five changed existing classes, 7,137 unchanged, sixteen new helper classes, no missing classes.

The host jar overlays only those five translated changed classes and sixteen helpers onto the exact accepted431 host jar. All 4,985 other host class entries and the complete support jar remain byte-identical. Official cached Robolectric native-graphics dependencies are host-test dependencies only.

An initial whole-translation byte comparison failed closed because dex2jar produced 322 unselected class-byte differences. That failed receipt, all 327 changed translation names/hashes, same-input reproducibility evidence, and a representative local-slot-only CobraEmblem disassembly difference are preserved in `initial-strict-diagnostic/`. These translated differences are excluded from the final host overlay. Canonical actual-DEX equality is required before overlay preparation; translated drift is never admitted into the unselected host classes.

Prepared workspace: `/workspace/cobra-evidence/cards432-integrated-host-v2-overlay`. Its `production.jar`, `support.jar`, `pom.xml`, and source-binding receipt form the shared host classpath. The existing real native `buildShell`/`cobraShowGuideShell` fixture is copied under `fixtures-not-selected/`; it has not been compiled or executed against this integrated prototype. Root must select behavioral checks before execution.
