# 2103260 — Cobra Recovery + Fixed Chooser (PHONE TEST CANDIDATE)

Parent: locked 2103259, commit 05dfa1ab6c06533fa02e13f5566256dde548e1ba.

Only two corrections:
- Cobra Recovery AND its Restore Built-in Theme confirmation share the locked cyan glass finish in Light/Dark modes. Exact original labels, safe-launch flags, and confirmation callbacks are preserved.
- Choose Your Experience uses a fixed viewport, not a ScrollView. Dragging does not scroll, bounce or stretch the composition. It fits the inset-adjusted window; landscape omits only overflow decorative floor, not gear/card actions.

Options, Health Center, chooser artwork, theme preferences, main/player source, native engine and installed data are preserved. No sound integration. The prior intermittent startup hang is not claimed fixed.

Install as an update, not uninstall/reinstall. Check both recovery dialogs in both themes. Cancel Restore unless you intentionally want that operation. Drag empty chooser areas in all directions and return from a gear: the scene should remain in place. Check both entry cards and gears on cover/unfolded/landscape. Automated tests do not establish physical-device acceptance.

Rollback source and the exact 2103259 APK are retained. An older versionCode may not install over the new version; do not uninstall/clear data to force a downgrade. Use a same-signature forward-version rollback if needed. No new stable lock until user approval.
