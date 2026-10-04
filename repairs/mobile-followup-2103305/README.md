# Locked 304 Power route follow-up

The 2103304 Android installer matches only unconditioned `<onclick>` elements.
Skin 1.0.5.195 uses separate Android and non-Android actions on its two Power
buttons. The installer therefore reports “Missing command 200” and aborts the
remaining profile loop even though those approved unified actions are correct.

This follow-up accepts the exact approved conditional pair without changing its
bytes. It continues to replace only the two allowlisted legacy command bodies,
rejects unknown commands/conditions/attributes, and isolates failed profiles so
later valid profiles can still be checked. Original-file backups and atomic
installation remain in place. No shutdown policy is changed.

The transform verifies all 250 inherited sources against the successful
2103304 source export before editing. Exactly one helper may differ afterward.
Weather, playback, providers, native libraries, signing, skin identity and the
deferred movie-video framing are untouched.

The host checks compile the production installer and test XML preservation,
unknown-action refusal, backup contents, idempotence and profile isolation.
Minimal host Android stand-ins do not represent lifecycle or device acceptance.
The source-validation job retains all inherited Android tests and adds
seven Robolectric conditional-route tests. It produces source evidence only;
the newly authorized, dependent packaging job is described below.

The regression suite fails on the locked helper with “Missing command 200” and
passes 33 host checks with the corrected helper. Full Android compilation and
Robolectric checks must finish before packaging any installable update.

## Outstanding gates

- The native shutdown hang is not resolved by this installer fix.
- The complete 194/195 skin archive could not be transferred during recovery.
  The replayed repository Power fixture is not a complete-file skin hash proof.
- Drawer height/focus polish, source/resolver windows and idle takeover remain.
- The dependent packaging job produces a narrowly scoped APK candidate. No
  updated skin ZIP is produced; the complete authoritative archive is missing.
- The front/inner screens, orientation, live resizing, themes, playback and
  Close/relaunch require physical device validation after a packaged candidate.

## October 4 authorized APK packaging

The workflow now gates a Java-only APK 2103305 package on all inherited Android
tests, weather isolation, host routes and source-preservation tests. The exact
locked APK 2103304 is its payload parent. Every native library, asset and Android
resource remains byte-identical; manifest differences are limited to version
identity and JNI declarations must match exactly. The permanent signer is
mandatory. Signing configuration stays in the existing GitHub secrets.

This packages the evidenced installer correction, not a speculative shutdown
rewrite. The earlier chat suggestion that the 2103299 change proves the current
hang's cause is withdrawn. Direct Quit() restoration is not made in this build;
current phone evidence is required to establish shutdown ownership.

Rollback source branch: rollback/2103304-195-before-2103305-20261004. The locked
APK and skin lock receipt remain authoritative and unchanged. The complete
194 archive failed transfer twice; the 195 archive is not in the repository.
No 196 skin candidate, provider-window fix or idle-owner fix is claimed here.
See DEVICE-TEST.md for the candidate's actual scope and remaining gates.
