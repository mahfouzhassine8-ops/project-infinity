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

## Preservation follow-up

Failed native run 37242471978 and successful locked native run 37189319805
have identical hashes for all 9,336 non-PNG files. The remaining 36 differences
are generated branding PNGs. The original locked receipt was recovered from
artifact 11298923388 (archive SHA-256
`aa68d284a14887b1a13d2f54de9ac6b88b7677a812bb5a54a684ef1a7cb73880`)
and its raw SHA-256 remains
`b870052cc344b8d419ed8fb29eb5dbc019fdbc9a528219a576576dcc4332b82b`.
The compressed fixture stores that exact receipt, not a replacement source map.

The follow-up attempts to restore only wall-clock PNG timestamp chunks to the
original run's bounded generation interval. Every resulting PNG must match its
original complete file hash, with all other chunks identical. All proposed
restorations are validated before any source file is written. If this cannot
reproduce a locked hash, the job stops and archives the unmatched PNG evidence.
No image is regenerated with different pixels and no asset is exempted.

The original 9,372-file source-map constant and three native preimage guards
in `native_patch.py` are unchanged. The new source tests cover exact-byte recovery,
altered-pixel rejection, CRC rejection, already-identical files, and receipt
authentication. Their passing result is not proof that runner-generated PNGs
have been recovered or that the complete native engine has compiled.
