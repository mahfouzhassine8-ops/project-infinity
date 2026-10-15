# Infinity skin 1.0.5.197 Browser Focus RC1

Separate candidate from the exact locked **skin.infinity.diggz 1.0.5.196 ZIP**,
SHA `4bd2483376819089d4fe1ec29a15720fd6ff50dce816bcbba367f3a1312dbc6e`.
Locked APK **2103305** remains the compatible base for this skin-only test.

Only `unified/AddonBrowser.xml` presentation and three metadata files change.
Focused labels retain the resting font size and bounds. Focus uses the existing
palette-following surface/text and transparent-centered cyan rim. Native routes,
IDs, hitbox bounds, drawer, player, providers, weather, artwork and all other
profile files remain byte-identical.

Package checks: 13 source/preservation tests, all 2,026 XML files parsed, exact
archive readback/CRC and protected manifest verification, 2,888 of 2,892 files
byte-identical. These are not Android/device acceptance.

**This ZIP does not fix Source Select, Back freezes, shutdown or the idle
screensaver.** Native provider geometry candidate 2103306 is separate, requires
a rebuilt engine and separately signed APK, and still needs device evidence.

No new candidate is locked without the user's acceptance. Original 196 remains
the forward reference and rollback checkpoint.
