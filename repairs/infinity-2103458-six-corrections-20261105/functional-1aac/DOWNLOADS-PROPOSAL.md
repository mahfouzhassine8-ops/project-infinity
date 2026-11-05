# Downloads-only filtering: final minimum proposal, NOT IMPLEMENTED

This is a narrowly scoped implementation proposal, not evidence that a native patch is safe or authorized. Current active458 drawer/helper identity and row classification must be verified first. No source records, native code, helper, permissions or settings were changed.

## Proposed file and function boundary

1. `xbmc/video/windows/GUIWindowVideoNav.h`: private, in-memory Downloads entry context only; any helper declarations/overrides necessary for the functions below. No persistent setting or global manager.
2. `xbmc/video/windows/GUIWindowVideoNav.cpp`: explicit entry recognition in `OnMessage`/`GetStartFolder`; apply a filter to the copied native video-source root in `GetDirectory`; ensure `Update`/reentry restores the correct original directory and context. No changes to playback, Add-source handlers, source-context callbacks, general source enumeration or other windows.
3. Existing `script.infinity.commandcenter/library_navigation.py`: Downloads action only, using the existing JSON-RPC activation helper to request the separately recognized Downloads context. Movies, TV, Sports, Browse and the existing failure/permission behavior remain unchanged. The current helper routes directly to an accessible Download folder, otherwise offers the native files browser; a native-only change would not affect every current Downloads entry, so this helper dependency must be part of any approval.

No drawer XML change is required. No changes to SourcesDirectory.cpp, GUIMediaWindow.cpp, MediaSourceSettings, URIUtils, manifests, Android storage permissions, providers, databases, native authentication or installer code are included. If the implementation cannot pass the constraints below with these three files, stop and identify the extra dependency before editing it.

## Entry and result invariants

- Use a reserved explicit Downloads activation intent/alias understood only by the existing VideoNav window. Gate it on the Infinity skin and current profile. Ordinary `files`/`sources://video/` calls remain ordinary source browsing.
- Filter the returned copy at the native source root only. Child folders, video selection, playback return and source context ownership remain native.
- Preserve the actual native root identity `sources://video/` in the returned item list. GUIMediaWindow::Update inserts native Add videos only when that identity is present. Do not append a query flag to the path and assume the exact-path checks/history still work. Do not synthesize a replacement Add videos item or emulate its action in Python.
- Retain each visible native source item's original path, source/drive flags, lock information, art and context actions. Never edit the source registry to hide a row.
- A filtered copy must not overwrite a cache used by ordinary source browsing. Mark this copied result non-cacheable using existing item-list semantics; do not clear or delete any existing cache. Reentering normal sources must fetch/display its original full result.
- Native Add videos respects existing profile/source-management restrictions. The proposal must not force the button to appear when Kodi intentionally disables source editing.
- Do not add a Download directory to sources automatically. If an existing readable Downloads location is presented as a temporary folder row, it must retain ordinary folder access/permission behavior and must not impersonate a registered editable source. Whether that row is needed depends on the verified current root contents; it is not permission for an additional control.

## Required context lifecycle

| Transition | Required result |
|---|---|
| Explicit Downloads entry | Open the filtered root, not a stale child folder |
| Root to a user video folder | Original directory/playback/source actions; no child filtering |
| Back from that folder | Same filtered root and selected row |
| Fullscreen/PiP/Info/settings and back | Existing native history and Downloads context restored |
| Explicit ordinary Files or another destination | Clear Downloads filtering; full normal sources unaffected |
| Profile or skin changes | Discard old context; never reuse another profile's classification |
| Refresh/Add videos/source rename/remove performed by user | Re-read native result, preserve native permissions and apply only current Downloads classification |

The existing `return` behavior can preserve a prior path when it matches m_startDirectory. A bare boolean filter or query parameter is therefore insufficient proof of correct entry/history behavior. Preserve this as a required implementation test, not a justification for altering global Back/history. No global reset/history clear is approved.

## Classification rule and remaining gate

CMediaSource stores name, paths, drive type, locks and other source data, but no reliable creator/origin field. A source name, network protocol, `m_ignore`, or plugin scheme alone cannot prove that a row is a bundled unrelated provider rather than a user-selected video folder.

The minimum safe rule is **hide only positively verified provider-navigation roots; retain ambiguous rows**. Establish that set from current native source rows plus installed provider identities/entrypoints. No label substring or blanket network/plugin blacklist. User-created local/network folders, removable sources and ambiguous/mixed multipaths remain. Source identities/credentials remain private; public evidence needs only classifications and counts. Do not add a second persistent source database or classification worker.

This conservative rule may leave an unclassified provider visible. That is a remaining acceptance gate, not permission to guess. A sanitized current-source classification inventory is missing; therefore no unconditional “hide all unrelated providers” guarantee is made. If product behavior requires hiding an ambiguous row, its classification requires evidence or an explicit user decision before implementation.

## Approval-stage focused verification

Before implementation: capture exact source/native hashes, active drawer/helper identity and the finite classified-root set. After a separately authorized patch, compile only the changed native source/engine stage as authorized and test:

- Explicit entry from Home and from an already open child folder; repeated entry.
- No configured folders; one folder; multiple folders; no eligible provider; mixed/unknown multipath; renamed sources.
- Accessible, empty and inaccessible Downloads; cancel/error recovery using existing permissions only.
- Native Add videos and context menus, including restricted profiles, locked shares and user-driven edits.
- Root/child/Back/history/focus, Refresh, Info, playback Stop/return, fullscreen/PiP/settings return and profile/skin transitions.
- Normal Files, library Movies/TV, provider navigation and normal source enumeration as preservation controls.
- Exact sources.xml/database hashes before/after passive browsing; no automatic writes or cache purge. User-requested Add/edit actions are verified separately and must remain native.
- Light/Dark and Fold front/inner/orientation; actual Android tests, not only host fixtures.

No implementation, build, signing or installation is authorized by this document. The native boundary and classification/history tests remain blocking gates for this correction alone.
