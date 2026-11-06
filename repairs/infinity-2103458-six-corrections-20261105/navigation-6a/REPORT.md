# Direct-library execution finding and bounded correction

Continues 6a26f34d. Signed 2103458 is the immutable base and the user-confirmed device version. The production candidate is unchanged. `UNAPPLIED-NAVIGATION.patch` is a concrete review candidate, not an applied correction or an APK.

## Which drawer and which route

The signed 2103458 skin manifest selects `skin.infinity.diggz/unified`. Its `Custom_1198_InfinityNav.xml` contains:

| Control | Visible label | Existing action |
| --- | --- | --- |
| 1198104 | Infinity Movies | `ActivateWindow(Videos,videodb://movies/titles/,return)` |
| 1198111 | Infinity TV Shows | `ActivateWindow(Videos,videodb://tvshows/titles/,return)` |

These are native title-library destinations, separate from the main Movies/TV provider entries. The completed drawer removals do not change these actions. The screenshot's separate buttons cannot have come from the exact supplied .243 drawer, which instead has one Library control. This identifies the matching packaged definition; it does **not** cryptographically identify the currently loaded on-device XML.

The supplied export's .243 version and drawer hash are user-provided evidence, not a new direct archive inspection here. Signed Health Center `default.py::export_infinity_skin_package` reads the fixed `special://home/addons/skin.infinity.diggz` directory. It does not ask Kodi for the loaded skin's resolved path. Therefore exporting .243 while packaging .256 is not evidence that .243 is active. The unchanged native add-on resolution examines packaged and persistent copies and ignores a lower persistent version when the higher packaged version is available. No installer, Health Center, skin-selection setting or source copy was changed.

## Confirmed source conditions

1. `GUIBuiltins.cpp::ActivateWindow` calls `IsSameStartFolder`. `GUIMediaWindow.cpp::IsSameStartFolder` uses **PathHasParent**, not exact path equality. If Videos is already active in a child of the requested title library, the builtin can return without activating or loading the root. A third flag added to the same builtin would not fix this guard.
2. `GUIMediaWindow.cpp::OnMessage(GUI_MSG_WINDOW_INIT)` intentionally retains the current nonempty directory when `return` is requested and the requested root equals `m_startDirectory`. Re-entry from another window can therefore refresh a retained child rather than the explicit drawer root.
3. `OnInitWindow` refreshes the resulting path. If GetDirectory fails, existing Update logic can fall back to a prior/root directory. The proposal neither changes that failure path nor fabricates successful loading.
4. `InfinitySavedNavigation` is restricted to its existing saved-entry/provider paths and does not rewrite these `videodb://` title roots. The inspected VideoNav skin onload actions contain no competing library redirect.

The host fragment proof reproduces conditions 1 and 2 for both movie and TV paths. It does not establish which condition, load failure, or resolved skin produced the original device screen. It is more specific than attributing the defect to an old active skin or changing the already-correct URLs.

## Exact proposed correction, NOT APPLIED

Three files, no new service, worker, setting, cache or navigation system:

1. **Existing drawer XML:** change only the two dispatch actions to `RunScript(script.infinity.commandcenter,library-navigation,library-movies)` and `library-tv`. Labels, ordering, geometry, Power, Close and all other actions remain byte-identical.
2. **Existing `library_navigation.py`:** map those two actions to the same two original URLs. Use its existing `GUI.ActivateWindow` JSON-RPC route with `[original_url, return, infinity-library-direct]`. The native JSON-RPC route already posts window activation directly, so it avoids the builtin's descendant-path suppression while retaining native activation/permission/modal checks. All existing provider, Downloads and ordinary Files branches are unchanged. An RPC acknowledgement is explicitly not directory-completion evidence.
3. **`xbmc/video/windows/GUIWindowVideoNav.cpp`:** immediately before the existing base WINDOW_INIT handler, set the current path to the requested title root **only** on Android, with an actually loaded Infinity skin, exactly three parameters, the exact `return`/entry flag, and one of the two exact title URLs. Native initialization, directory retrieval, failure fallback, selection history and Back-start handling then continue through their existing code. No history clear, retry, forced activation, permission bypass, new callback or file write is added. Only the existing `addons/Skin.h` header is included. The .h file, GUIBuiltins, GUIMediaWindow and GUIWindowManager remain unchanged.

This native use is outside the prior **Downloads-only** authorization even though it is the same .cpp file. The explicit native boundary must be expanded to this library-entry purpose before applying the patch or compiling it into a successor engine. The marker cannot be shipped with the old native engine and represented as a correction. Source and engine/member guards must bind the integrated result before packaging.

## Focused verification

`RESULT.json`: **53 checks pass**, comprising source bindings, exact compiled native initialization fragments with mock directory loading, mocked Python dispatch, negative cases and byte-preservation assertions. This is not 53 Android tests.

- Before: movie/TV retained-child and builtin suppression reproduced.
- Proposed fragment: both explicit roots selected from Home and a child; initial/empty/sentinel and cross-directory cases checked.
- Ordinary calls, unsupported paths, malformed flags, extra parameters, another/no loaded skin and non-Android behavior remain unchanged in the tested fragments.
- Injected failed loads are attempted once and remain failures/fallbacks; no success or retry is invented.
- Original helper actions and all other drawer bytes are preserved. RPC error remains visible.
- Fragment compilation: C++17, warnings as errors, with and without TARGET_ANDROID. Three initial harness-generation compilation failures are retained (the first duplicate failure preceded stderr capture); newline/token placement was corrected in the harness only. They were not native production failures.
- Full ARM64 compile/link, actual native Back/focus/permission behavior, Android navigation and physical Fold acceptance: **NOT RUN**.
- The existing 23 source checks, 58 Linux changed-control checks and unchanged visual evidence were retained, not rerun. They do not establish Android acceptance.

## One consolidated set of remaining gates

| Correction | Current state / precise dependency |
| --- | --- |
| Direct libraries | Concrete unapplied three-file patch above. Needs navigation-specific native authorization, full compilation and actual integration verification. No more version/export requests are needed to review it. |
| Drawer | Completed Browse Files/Media Sources removal and approved height/Power placement preserved exactly. |
| Downloads | Native/source-helper boundary is approved, but configured source records have no creator attribute. No supplied current inventory positively binds the unwanted rows to provider-only roots while distinguishing user-added or mixed sources. Names, protocol and provider identity alone are insufficient. Keep the explicit classification stop; no guessed filter or source deletion. |
| Browser/Info | Completed visual work and approved Back/Trailer/Details changes preserved. No new independent visual defect established here to justify another speculative patch. Universal Android rendering remains unaccepted. |
| Search validation | Nixtoons history write self-invalidates. A meaningful settings change followed by restoration is indistinguishable from a benign rewrite to the current endpoint validator; dropping timestamps would lose an existing safety check. Crew's changed component remains unbound. Both acceptance failures remain FAIL. |
| Search native crash | The historical two SIGSEGV summaries do not identify a faulting instruction/lifetime owner. RPC completion is not interpreter completion. No safe native crash repair or actual 30-search Android stress PASS is established. No lease or configuration safeguards were weakened. |

No successor APK was built or signed. This is a source-scope/correctness gate, not a newly diagnosed signing-key failure. A new full member comparison, install-over verification and higher-version recovery route remain required when an approved integrated payload exists. No installation, data reset, promotion or lock occurred.

## Preservation

`PRESERVATION.json` rebinds all four completed skin overlays, the unchanged Search source, the proposed-input hashes and the original signed archive. The only new tracked files are this inert proposal, its generator and focused evidence. Cobra, Preview, native inputs, providers, playback, shutdown, settings, user data, signing infrastructure and all existing recovery references are unchanged by this continuation.
