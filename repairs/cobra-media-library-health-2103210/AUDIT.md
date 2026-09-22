# Cobra 2103210 — Movies/Shows + Kodi Health Center

Parent presentation: exact successful Cobra 2103208 generated Android source. Native engine: exact rebuilt 2103209 Python 3.11 GIL-stability engine, reused without recompilation.

Authorized scope only:
- Replace the initial Movies/Shows library presentation with the locked cinematic Cobra browsing direction: real provider hero artwork, horizontal poster shelves, Continue Watching, My List, category shelves, details, search, and the existing playback/episode actions.
- Add **Kodi Health Center** to both Choose Your Experience card-settings menus. The bridge can execute only the fixed add-on id `script.kodihealthcenter` after Kodi is ready.

Explicitly out of scope: Live TV, Guide, channel playback, providers, timeshift/rewind, Quick Peek, Multi-View, PiP, background playback, player controls, network policy, and native engine behavior. CI hashes representative Live TV ownership methods before and after the patch and fails on any drift.

The legacy `renderVodItems()` path remains untouched for Search/My List fallback behavior. No new Android permissions, resources, assets, native libraries, or arbitrary add-on execution surface are introduced.

Packaging note: the 2103209 Android shell compiled and assembled successfully but its final verifier still required the obsolete literal `EXTENDED BACKGROUND MODE`. This successor updates only that verifier inventory to the already-approved current background runtime markers (`InfinityBackgroundControlActivity`, `BACKGROUND_MODE_NORMAL`, `BACKGROUND_MODE_EXTENDED`) before packaging.
