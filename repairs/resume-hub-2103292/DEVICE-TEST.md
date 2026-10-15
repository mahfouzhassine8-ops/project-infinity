INFINITY 2103292 — RESUME HUB 2 RC1 — DEVICE TEST

Install as an UPDATE over locked 2103291. Do not uninstall and do not clear data.

Expected:
- Native engine remains byte-identical to locked 2103291.
- Command Center advances from 0.3.5.17 to 0.3.5.19 on first app start.
- Infinity skin advances transactionally from 1.0.5.181 to 1.0.5.182 after Command Center starts; 1.0.5.182 requires APK 2103292 / Command Center 0.3.5.19.
- Existing Trakt Movies and Trakt TV remain present.
- New Infinity Movies and Infinity TV appear beside the preserved Trakt sections.
- Resume Hub retains in-progress positions and watched history.
- Completed items leave Continue Playing/Continue Watching while remaining in watched history.
- Manual Mark Watched / Mark Unwatched updates Resume Hub and Kodi playcount.
- Existing blue watched checkmarks follow Resume Hub state through Kodi PlayCount/Overlay plus the Infinity.ResumeHub.Watched skin bridge in Infinity-owned listings/widgets and Kodi-library-backed views.
- Watchlist, Collection, ratings and local lists are available without requiring Trakt.

Preservation:
- No native-engine rebuild; passed 2103291 In-Place Responsive Reflow and its native layout contract remain byte-preserved.
- No player XML changes.
- No provider/account changes.
- No Start Fresh.
- No user-library deletion.

If the skin does not advance to 1.0.5.182, open Command Center once, return Home, and allow one skin reload. If anything fails, export diagnostics before changing the installation.

Whole-skin Resume Hub acceptance:
- Fold/unfold/rotation still uses the passed 2103291 in-place responsive reflow; no Home/window restart is introduced by 1.0.5.182.
- Infinity Movies and Infinity TV appear in every active Home profile (legacy plus responsive classes) without removing Trakt Movies/TV.
- Mark Watched / Mark Unwatched changes the blue watched state after refresh and does not leave completed items in Continue Playing.
- Resume Hub revision changes refresh Infinity-owned widgets without requiring a skin reinstall.
- Player XML, providers, accounts, PiP/background playback and native libraries remain unchanged.
