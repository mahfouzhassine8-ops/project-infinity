# Infinity 2103159 — Experience Chooser ZIP Bridge RC1

## Scope

This candidate branches forward from the user-locked Cobra 2103158 baseline at
`fd2af59bab2edcaea6be9e5046720715e25e64e0`. The 2103158 lock is never moved or
edited.

The 2103159 Android delta is deliberately limited to two presentation areas:

1. the startup `Splash` experience chooser bridge; and
2. three Cobra presentation/navigation methods: `cobraDrawerView`,
   `toggleCobraDrawer`, and `showCobraPowerMenu`.

The Cobra cleanup removes the duplicate bottom `∞ Infinity` drawer handoff,
removes Health Center from the main drawer because Health Center already exists
inside Cobra Settings, keeps Power as the only drawer footer action, and changes
the Power-sheet label `Exit Infinity` to `Exit`. The existing Power actions remain
`Switch to Infinity`, `Exit`, and `Cancel`; their callbacks are unchanged.

Cobra Health Center behavior, per-channel playback, recovery, EPG, all five view
renderers, diagnostics, player ownership, lifecycle, native engine/assets and
signer remain the locked 2103158 implementation unless a gate proves otherwise.

## Experience chooser ZIP bridge

The locked 2103158 startup chooser is constructed inside `Splash.java.in`; the
existing Cobra UI ZIP loader only feeds `InfinityLiveActivity`. A ZIP alone cannot
reach that screen. Bridge 1 makes Splash optionally read one bounded visual JSON
file that the existing Cobra UI installer already stages safely. Future chooser
copy/color/spacing changes can therefore be ZIP-only while they remain inside
this contract.

Required UI 1.4.0 presentation:
- `INFINITY` / `BEYOND ENTERTAINMENT`
- `HM` with `PERSONALIZED FOR YOU`
- `Choose Your Experience`
- Infinity: `YOUR HOME FOR MOVIES, SHOWS AND MORE`
- Cobra: `FOCUSED. FAST. POWERFUL.`
- footer: `INFINITY BY HASSINE MAHFOUZ` and `ONE APP • YOUR WORLD`

The themed screen contains no `2-IN-1`, no explanatory subtitle under the title,
and no `Live TV` wording on the Infinity card. `HM` is a visual token in the
installed package; no separate identity data is read.

## Cobra navigation cleanup

The main Cobra drawer remains Search, Live TV, Movies, Shows, Recordings, My List,
View and Settings. Health Center is not duplicated there. The footer contains only
Power.

Cobra Settings retains its existing `COBRA HEALTH CENTER` action and existing
`showCobraHealthCenter()` owner. No Health Center repair/diagnostic behavior is
reimplemented by 2103159.

The Power sheet remains the single session/handoff surface:
- `∞  Switch to Infinity` -> existing `returnToInfinity()` path
- `⏻  Exit` -> existing `finishAndRemoveTask()` path
- `Cancel` -> existing dismiss path

Only the visible Exit label changes. The callbacks and cleanup sequence are
protected.

## ZIP contract and hardening

`Infinity-Cobra-UI-1.4.0-Experience.zip` is built from exact locked matching UI
1.3.9 SHA-256
`88ada1fded508fede9368bf9dc4259c60220a4f067b9ba5ae2b45ffdb6b2a81a`.
The existing Cobra theme/module bytes are preserved. The additional staged
resource is `resources/experience-chooser.json` with explicit scope
`infinity-experience-chooser` and `minimum_bridge: 1`.

Splash accepts only its app-specific external-files location, canonicalizes the
resource path, caps the JSON file at 64 KiB, performs a complete bounded read,
requires schema/scope/bridge compatibility, bounds dimensions and validates
colors/copy. Invalid, missing, oversized or future-schema data falls back to the
exact legacy chooser.

The old chooser body is preserved under a fallback method. Existing `startXBMC`,
card settings, `launchInfinityExperience` and `onCreate` methods are byte-protected.
The theme remains presentation-only and cannot inject class names, intents, Java,
provider credentials or arbitrary paths.

## Automated gates

Host gates require the exact locked 2103158 Splash and Activity hashes. The Cobra
cleanup patch must reproduce exactly from the locked Activity, and only the three
approved presentation/navigation methods may differ. `showSettings`,
`showCobraHealthCenter`, player, guide, lifecycle and channel-action owners are
byte-protected.

The inherited EPG/mode test uses the exact `CobraModesHarness.java` preserved in
the successful locked 2103158 evidence artifact, rather than an older 2103155
mode harness. This prevents a stale test fixture from being mistaken for a runtime
defect.

CI reconstructs exact locked 2103158, preserves a complete rollback, rebuilds and
signs the 2103159 Android shell against the locked native payload, verifies the
permanent signer, and proves native libraries/assets remain byte-identical.

The Android gate reruns the locked navigation and health/recovery suites. The one
health UI test whose old navigation path depended on the removed main-drawer
Health row is adapted only in the test harness to open the same Health Center via
Settings; its health/recovery assertions are unchanged. Two new 2103159 tests
verify that the main drawer has no Health Center or direct Infinity footer, that
Health Center is visible from Settings, and that Power shows Switch to Infinity,
Exit and Cancel. Six chooser tests remain in place.

Delivery requires 19 Android cases with zero failures/errors/skips plus screenshot,
APK/signature/native/assets and staged-ZIP integrity gates.

## Device acceptance still required

Install the 2103159 APK over 2103158 without uninstalling or clearing data. Install
UI 1.4.0 through the existing Cobra UI update picker. Verify the approved chooser
on the real Fold displays and landscape, then verify:

- Cobra drawer has no bottom Infinity handoff;
- Health Center is absent from the main drawer and present in Settings;
- Power is the only drawer footer action;
- Power shows Switch to Infinity, Exit and Cancel;
- both handoff/exit actions still perform their established cleanup paths; and
- playback, guide, health, rotation/Fold and background/resume behavior remain
  unchanged.

This RC is not a new lock or official release until physical-device acceptance is
completed.
