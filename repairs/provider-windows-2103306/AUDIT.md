# Source Select audit — 2026-10-04

## Exact locked base and rollback

| Artifact | SHA-256 |
| --- | --- |
| APK 2103305 | `e82ce26b666bc5df089f8b4b3d493a44daf0634690854eb4b6fbbc2c007471ab` |
| skin.infinity.diggz 1.0.5.196 ZIP | `4bd2483376819089d4fe1ec29a15720fd6ff50dce816bcbba367f3a1312dbc6e` |
| 3305 complete native source receipt | `b870052cc344b8d419ed8fb29eb5dbc019fdbc9a528219a576576dcc4332b82b` |
| Inherited libkodi.so | `2b0897a286a7286e17109e8f5c7c2ec152c838dc91686ce349be3100eea69eac` |

The APK, ZIP, and lock receipt were copied and their hashes verified before this
pass. The repair branch preimage is `847ca440c39c4d1522a44428c6c26a0043328714`.
Native behavior scripts are unchanged between the engine commit
`dcfb7a097fa542c69f1aae1130305e7b409d968b` and that branch preimage.

## Provider ownership

Umbrella is the user-confirmed reproducer. Its inspected primary-source revision
is [3baead15](https://github.com/umbrellaplug/umbrellaplug.github.io/tree/3baead15cc75e6a17a708e1a4f884342d2e58295/matrix/plugin.video.umbrella).
This revision is a reference, **not a verified installed phone version**.

| Stage | Owner/file | Observed contract |
| --- | --- | --- |
| Title scrape, source list and resolver | `resources/lib/modules/sources.py` | Invokes `SourceResultsXML('source_results.xml', addonPath, ...)` and `WindowProgress('source_progress.xml', addonPath, ...)` |
| Results controller | `resources/lib/windows/source_results.py` | Primary list ID 2000; Back button 2051; cached/uncached, source-info, context and resolver actions are provider owned |
| Results presentation | `resources/skins/Default/1080i/source_results.xml` | 1920×1080 backdrop; 1350×800 source list; 100-unit rows; wide labels and a separate artwork/info region |
| Resolver progress/controller | `resources/lib/windows/source_progress.py` | Closing actions dismiss the provider window and set `closed`; `iscanceled()` exposes that state |
| Progress presentation | `resources/skins/Default/1080i/source_progress.xml` | Fixed 1920×1080 backdrop and oversized absolute-position text block |
| Closing action IDs | `resources/lib/windows/base.py` | 9, 10, 13, 92, 511; selection IDs 7, 100 |

The provider's sources module checks `iscanceled()` in several resolver paths.
That does not establish that every network operation is interruptible or that
the Android gesture reaches the callback during a freeze. No provider Python
rewrite is made from an assumed installed version.

Seren's [b4f4b63b source](https://github.com/nixgates/plugin.video.seren/tree/b4f4b63bf59b38b93bd565a8503e121f64c91e30)
independently uses `resources/lib/gui/windows/source_select.py`,
`resolver_window.py`, and `resources/skins/Default/1080i/source_select.xml`.
Its controls differ from Umbrella (including list 1000, cache action 2001, close
2999), confirming that providers must not share an unverified action-ID override.
Its installed version is also unverified. Fen/Fen Light and POV/Diggz installed
packages have not been authenticated in this pass; no per-provider completeness
claim or blind resource replacement is made.

## Shared native defect, proven against the locked engine source hashes

[Pinned Kodi WindowXML.cpp](https://github.com/xbmc/xbmc/blob/a3a448d26b8d560a65655dab2cd122994dc4e146/xbmc/interfaces/legacy/WindowXML.cpp)
first resolves against the active skin, then temporary provider skin folders.
The inherited 2103291 patch makes Android `UsesNativeWindowAdaptation()` true for
those temporary skins as well. `GetSkinPath` rewrites the returned resolution,
but not the fixed provider XML. A 1920×1080 XML is then mapped against a tall
logical canvas. This explains clipping/top-only coverage at the source boundary;
it does **not** prove ownership of a native SIGSEGV or Back freeze.

The inherited window reflow rejects absolute `xmlfile` paths, which provider
windows use. Changing Home.xml or VideoOSD.xml would not repair their fallback
coordinate ownership. The candidate explicitly preserves declared provider
coordinates while leaving active-skin responsive adaptation intact.

## Add-on Browser focus

Exact skin 196 `unified/AddonBrowser.xml` has SHA
`2d4ac50b8f92dcc1b5cc8dd7e39eacb58d01a810cf6847be49156177d4ebd16c`.
Its resting label is `InfinitySmall` (28 units), but its focused label switches
to `InfinityBodyBold` (34 units) inside identical bounds, with hard-white text.
That is an evidenced focus-size jump, not proof that a tooltip is created.
The candidate keeps the size/bounds stable and uses existing theme palette and
transparent-centered cyan rim assets. Actions, IDs, tile bounds and primary
click/long-press policy are preserved.

## Device evidence needed to finish

Capture an exact installed provider inventory and debug log during title select,
results, source activation, Android Back, rotation, fold and recovery. Candidate
logs identify XML, provider ownership, logical dimensions and Back queuing. A
missing Back log points before WindowXML; a queued Back without completion needs
Python/worker/thread evidence. Do not assume either is solved by geometry.

Verify cover/inner portrait and landscape, split-screen/pop-up/live resize,
Light/Dark/OLED, touch/long-press/scroll, IME open/closed, background/foreground,
active/inactive playback, and one-layer Back unwinding. Record cold/warm launch
and immediate/delayed relaunch separately. No physical matrix cell is marked
passed here.
