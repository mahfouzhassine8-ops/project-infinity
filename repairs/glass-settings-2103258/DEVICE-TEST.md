# 2103258 — Glass settings completion (phone/Fold test candidate)

Parent: exact 2103257, commit 2711bb34bb9587f7cb3a81fd3fbf10d30743131a.
Only the presentation of the Infinity/Cobra gear menus changes.
Existing chooser Java and artwork, player, native libraries, skin and add-ons remain unchanged.
Both menu labels and the action callback body are copied byte-for-byte from 2103257.
No startup sound, new toggles or fix for the earlier intermittent startup hang is included.

Install as an update; never uninstall, clear data or use Start Fresh for this test.
Open both gears in Light and Dark/OLED modes. Check glass appearance, readable labels,
Cancel/Back/outside dismissal, and all original options. Confirm gear taps do not select a card.
Check folded/unfolded/landscape and a short multi-window. Rows scroll; Cancel stays visible.
Remember & launch, launch once, Ask every time, Health Center and Cobra Recovery retain
exactly their existing behavior. Do not choose destructive recovery actions just to test styling.

CI runs the original six chooser tests plus seven options tests. Callback-side-effect tests
execute the original callback in an isolated Activity harness, without initializing Kodi.
The four settings PNGs are native Canvas renders of actual UI code over the unchanged chooser;
they are not new AI mockups and not physical-device screenshots. Device acceptance is pending.
The retained plain dialog is the safety/TV fallback; the separate TV build is untouched.
Original 2103256 stable lock and 2103257 rollback branch are unchanged. Android may reject
an ordinary downgrade: request a forward-version rollback rather than uninstalling.
