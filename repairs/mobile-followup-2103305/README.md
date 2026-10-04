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
The separate Actions workflow retains all inherited Android tests and adds
seven Robolectric conditional-route tests. It produces source evidence only.

The regression suite fails on the locked helper with “Missing command 200” and
passes 33 host checks with the corrected helper. Full Android compilation and
Robolectric checks must finish before packaging any installable update.

## Outstanding gates

- The native shutdown hang is not resolved by this installer fix.
- The complete 194/195 skin archive could not be transferred during recovery.
  The replayed repository Power fixture is not a complete-file skin hash proof.
- Drawer height/focus polish, source/resolver windows and idle takeover remain.
- No APK or skin ZIP is produced by this workflow.
- The front/inner screens, orientation, live resizing, themes, playback and
  Close/relaunch require physical device validation after a packaged candidate.
