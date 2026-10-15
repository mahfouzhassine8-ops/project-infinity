# Infinity filling close ring — APK 2103310

The user approved 2103309's close indicator but requested a ring that fills
toward completion instead of a constant rotating arc. Exact APK parent:
**2103309**; source commit `995c893facfe8a09484627ca24cc8db6e962bd05`.

The corrected blue arc begins at 12 o'clock and grows clockwise at actual
completed milestones: Android stop (one third), shutdown handoff into native
destruction (two thirds), native destruction returned (full circle). These
milestones do not measure equal amounts of work or predict remaining time.
Each newly confirmed segment eases into place over 180 ms. A breathing tip
stays at that position while the next stage is active. Elapsed time cannot
advance progress; 15 seconds does not mean completion.

The full blue ring is stationary after confirmed completion for a chooser that
watched the close. A fresh chooser after an already completed close keeps the
normal gear. The chooser can exit with the process during normal Kodi shutdown;
an indicator cannot paint after its process has ended.

Force recovery holds the last confirmed progress. Missing owners and late old
owner callbacks use the accepted 3309 observer unchanged. Only the Gear block
in InfinityGlassChooser.java.in changes. All other Android source, the complete
3308/3309 native engine, skin 1.0.5.201, Cobra and installed Diggz Mirage 421
remain preserved. No native rebuild or shutdown-policy change.

Validation compiles production views and tests stage growth, stationary holds,
completion, force recovery, old-owner ordering, visibility lifecycle, Cobra's
gear, and light/dark cover/inner/landscape/short-window rendering. Packaging
checks every other DEX owner, all native/assets/resources and permanent signing.

Phone test: Power → Close Kodi → immediately reopen. The blue ring must grow
from the top as stages complete, hold short of full during slow cleanup, and
finish only on actual completion (or leave the screen when the process exits).
Physical responsiveness and timing require the user's device check.
