# 2103257 Glass Chooser — PHONE/FOLD TEST CANDIDATE

Parent: locked 2103256, ef0ef44a9020f6a2d1488babff87caffc0a5b686.
No sound integration, no native engine rebuild, no skin/add-on/provider/player edits.

This is not a new stable lock until device acceptance. The earlier intermittent
black-startup report remains unresolved; this patch does not claim to fix it.

1. Install as update over 2103256; do not uninstall, clear data or Start Fresh.
2. With Ask Every Time, open chooser: dark glass/gold Infinity/cyan Cobra/HM orb.
3. Open each gear. Verify Remember & Launch / Once / Ask Every Time / Health
   Center; Cobra Recovery remains in Cobra gear. Gear must not launch its card.
4. Use the existing Cobra appearance preference: Light / Dark / OLED / System.
   Return to chooser. Light includes both Enter pills; dark uses whole-card
   selection. No added sound/appearance settings.
5. Check phone cover, unfolded, landscape and multi-window; both choices/gears
   must remain reachable without overlap. System bars/cutout must not hide them.
6. Tap each experience and return. Existing default/autolaunch must stay intact.
7. Compare cold/warm startup against 2103256; report freezes without clearing data.
8. Keyboard/D-pad and accessibility: focus order, labels and separate gear actions.

CI tests custom native Views on Android 35/Robolectric and preserves source and APK
payload invariants. It does not replace Android 17/Samsung physical-device testing,
measure real GPU/startup latency, or establish pixel-perfect matching of AI images.

Rollback: original 2103256 APK + exact source snapshot are retained. Android may
reject an ordinary versionCode downgrade; DO NOT uninstall to work around that
without a user-data backup. Request a same-signature forward-version rollback
package if reverting becomes necessary.

Golden master PNG SHA-256:
- Dark, 941x1672: 407fbb2a5c558ccc8b37d67c121a7ed56a195435591f406a9c16043b680f4067
- Light, 840x1873: 672b2cbe362881bd268b6f8fdcdc542439bae175ffb8476d264a4a4663a6e6ce

These are distinct layouts: dark has no Enter pills; light has Enter pills and its
additional approved copy. Native typography is recreated with Android serif/sans;
rendered screenshots must be reviewed against the references before acceptance.
