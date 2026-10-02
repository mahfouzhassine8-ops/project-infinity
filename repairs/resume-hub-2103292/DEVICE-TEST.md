INFINITY 2103292 — RESUME HUB 2 RC1 — DEVICE TEST

Install as an UPDATE over locked 2103291. Do not uninstall and do not clear data.

Expected:
- Native engine remains byte-identical to locked 2103291.
- Command Center advances from 0.3.5.17 to 0.3.5.19 on first app start.
- Infinity skin advances from 1.0.5.181 to 1.0.5.182 after Command Center starts.
- Existing Trakt Movies and Trakt TV remain present.
- New Infinity Movies and Infinity TV appear beside the preserved Trakt sections.
- Resume Hub retains in-progress positions and watched history.
- Completed items leave Continue Playing/Continue Watching while remaining in watched history.
- Manual Mark Watched / Mark Unwatched updates Resume Hub and Kodi playcount.
- Existing blue watched checkmarks follow that state wherever the skin supports watched overlays.
- Watchlist, Collection, ratings and local lists are available without requiring Trakt.

Preservation:
- No native-engine rebuild.
- No player XML changes.
- No provider/account changes.
- No Start Fresh.
- No user-library deletion.

If the skin does not advance to 1.0.5.182, open Command Center once, return Home, and allow one skin reload. If anything fails, export diagnostics before changing the installation.
