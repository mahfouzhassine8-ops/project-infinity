# Cobra 2103211 — Movies/TV Shows + Infinity-native Health Center

Parent: exact successful 2103210 Android source. Native engine: exact successful 2103209 Python 3.11 GIL-stability engine, reused without recompilation.

## Locked media structure

Movies:
Featured → Recent Releases → Continue Watching → Trending Movies → Popular Now → Genres.

TV Shows:
Featured → Recent Releases → Continue Watching → Trending Shows → Popular Now → Genres.

Additional approved behavior:
- No Movies/Shows/Search mini-navigation inside either library. Existing Cobra navigation owns destination switching and Search.
- My List remains the existing Cobra drawer destination rather than another permanent rail.
- Recent Releases is dynamic and never displays a hard-coded year in the UI.
- Genres is directly below Popular Now and opens a visual genre picker / collection view.
- Because You Watched… is conditional and appears only when viewing history can support it.
- See all is interactive for content rails.
- Featured hero rotates slowly through a small set and stops when its controls receive focus.
- Continue Watching shows progress; TV continuation can expose the saved episode label.
- Poster selection opens details first. Playback starts only from explicit Play / Browse Episodes.
- Details expose synopsis, year/rating when supplied by the provider, runtime when supplied, genre, provider availability, My List, and explicit playback/episode action.
- Provider data, source ownership and playback routes are not rewritten.

## Infinity Health Center correction

2103210 incorrectly launched Kodi and then executed script.kodihealthcenter. That fails the recovery use case when Kodi/Infinity's native runtime is itself crashing.

2103211 removes that Infinity-to-Kodi bridge. Health Center now lives in the Android chooser layer and can operate before Kodi Main or Cobra is launched. It:
- reads Android ApplicationExitInfo history for this package;
- identifies native crash, Java crash and ANR exits;
- reads Android-provided exit traces when available;
- shows build/device/version information;
- copies a diagnostic report to the clipboard;
- exports a text diagnostic report through Android's document picker with no new storage permission;
- detects a newly observed abnormal exit and bypasses an auto-launch preference once so Choose Your Experience remains reachable after a crash.

Cobra's separate existing diagnostic/health behavior is not removed; this change only fixes the Infinity-side recovery entry.

## Protected boundaries

Explicitly untouched:
- 2103209 libkodi.so and Python 3.11 GIL repair;
- Live TV, Guide, channel playback, Quick Peek;
- timeshift/rewind, Multi-View, PiP/background playback;
- provider ownership/network policy;
- player controls and native engine;
- APK assets/resources and permanent signing identity.

Representative Live TV/player/provider methods are exact-hash protected before and after the patch. Final packaging rejects any native/resource drift.
