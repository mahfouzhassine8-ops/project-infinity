# Provider-window coordinate candidate 2103306

Forward base: locked `com.projectinfinity.kodi` APK **2103305** plus authoritative
`skin.infinity.diggz` **1.0.5.196**. The locked pair is not replaced or relocked.
The 3305 APK reuses the byte-identical engine from 3304; the source receipt SHA
is `b870052cc344b8d419ed8fb29eb5dbc019fdbc9a528219a576576dcc4332b82b`.

## Evidenced correction

The Android in-place layout patch adapts every `CSkinInfo` lookup. Kodi's Python
`WindowXML` creates temporary `CSkinInfo` instances for provider fallback skins.
Those instances therefore return an aspect-rewritten logical canvas even though
the returned provider XML still contains its original desktop coordinates.

`GetSkinPath(..., adaptWindow=false)` preserves a provider fallback's declared
folder/default resolution. All three fallback lookups use it. The first lookup
in the real active skin remains adaptive, so an existing active-skin override
does not regress. Temporary fallback constructors use a fresh declared default
instead of the resolution left by a failed active-skin lookup.

Only `Skin.h`, `Skin.cpp`, and `WindowXML.cpp` change. The transform is gated by
the exact locked 3305 source hashes and complete parent receipt. Back logs mark
native callback **queuing**, not Python completion or successful cancellation.
Provider Python, lists, credentials, configuration, playback, IME, native cleanup,
weather snapshots, and the deferred movie-video framing remain unchanged.

## Validation and limits

Host tests compile the real resolver method against a mocked filesystem/window
boundary. They cover active adaptive Home, marker-based Home, provider folder
and default resolution, invalid skin, null resolution output, TV/remote legacy
behavior, preimage rejection, retained callbacks, and diagnostic wording.
Pinned upstream fixtures reconstruct all three exact 3305 native source hashes.
This is not a full engine compile or Android/device acceptance.

The separate native workflow reconstructs the complete inherited engine, proves
the entire parent receipt, applies this three-file delta, compiles ARM64, and
verifies all captured sources after compilation. It has a separate concurrency
group and does not cancel a running 3304 job.

**Neither validation workflow produces an installable APK.** APK packaging must
use the successful candidate engine, exact locked 3305 Android shell/asset base,
the permanent signing certificate, and a separate versioned build. Reusing the
old native library would omit the Source Select coordinate correction.

Skin **1.0.5.197 Browser Focus RC1** is an independently testable refinement over
the exact 196 ZIP. It changes only active AddonBrowser.xml presentation plus
release/integrity metadata. That ZIP alone is **not** a Source Select fix.

## Still open

- Installed provider versions and selected provider/custom-skin resource paths.
- Provider-specific responsive presentation, portrait touch sizing, safe areas,
  artwork/metadata containment, and Light/Dark/OLED visual acceptance.
- Android gesture arrival, provider Back callback completion, resolver worker
  cancellation, observed freeze recovery, and any crash ownership.
- Full physical-device fold/orientation/multi-window/playback matrix.
- Existing slow native shutdown and idle/screensaver takeover investigations.

No freeze, crash, shutdown, or whole-brief completion is claimed.
