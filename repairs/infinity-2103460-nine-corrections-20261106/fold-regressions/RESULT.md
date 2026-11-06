# Physical-regression pass: release blocked, not complete

The four user PASSES remain authoritative: Power last, Infinity Movies menu,
Infinity TV Shows menu, Downloads/Add videos/user folders. No runtime overlay,
native source, provider, profile, authentication or signing file was modified.
No installer was built, signed or installed. Nothing was locked.

## Direct evidence and isolated corrections

`READONLY-BINDINGS.json` binds eight inspected native files to BOTH the signed
2103460 native map and the delivered 2103462 native map. The unchanged older
451 tree's GUIBaseContainer.cpp is **not** the compiled 460/462 input; the exact
reviewed touch overlay with SHA cb0e262c9cb58c56f6655955b6dc2999a2608523be9de582dabd82d3a0dfe0ae
was used when tracing heading touch. The six Info geometry/dispatch sources
do match the frozen restored tree and both signed build maps.

The original-key delivered quick ZIPs are read directly to record CC Search,
context/menu, module/bootstrap and skin file hashes. This proves artifact
identity, **not installation or activation on the phone**.

Two skin files have isolated, unapplied corrections in `SKIN-CANDIDATE.patch`;
`SKIN-CANDIDATE.json` records their exact input/output hashes. The preparer can
reconstruct the candidate files into a fresh temporary directory:

1. `DialogVideoInfo.xml`: horizontal group 9000 has four percentage-width
   buttons but no minimum width. Frozen GroupList starts total/min size at 0;
   GetWidth returns 0, and Window::LoadControl uses it as the children's parent
   width before loading those children. The candidate uses
   `<width min="86%" max="86%">auto</width>` to establish the intended viewport
   before creating buttons. The original dimensions and actions of Play8,
   Trailer9012, Cast9013, More106, Back9011 and Cast50 are otherwise unchanged.
2. The final Info video window overlaps the buttons and Cast. Native group
   touch dispatch traverses last-rendered children first; GUIVideoControl
   consumes a left click during video playback. Move the EXACT video control
   before group9000 so buttons and Cast receive touch first. No video rectangle,
   condition, playback handler, trailer route or native code changes.
3. `Includes_InfinityMediaLists.xml`: the shared BrowserRow watched image is
   hidden for overlay-only or ResumeHub-property-only watched state. Include
   the existing OverlayWatched.png and Infinity.ResumeHub.Watched=true in
   visibility. Existing ListItemOverlay still resolves its real state/override;
   no new state, new checkmark source or persistence writer is introduced.

Native Play8 already receives GUI_MSG_CLICKED and calls Play(); adding an
onclick PlayMedia would risk dispatching twice. The candidate deliberately
adds no Play command. Trailer availability/bridge behavior is preserved.

## Focused checks

`HOST-RESULTS-bound-native.txt`: **6 host checks PASS**, including compiled
actual frozen GetWidth/SetMinSize method bodies in a small platform boundary,
failing-before and passing-after initial widths in four logical viewport
fixtures; reverse touch z-order; all actions/IDs; existing watched menu
choices; and complete-file preservation for all fourteen delivered overlay
sources and the four final Downloads native sources.

The first two runs exposed test-fixture mistakes (a nonexistent control60 and
XML indentation tails). Original output is retained in HOST-RESULTS.txt and
HOST-RESULTS-corrected-fixture.txt. The corrected fixture passed, and the final
binding check independently ties all tested native method files to signed maps.
No failed application or device result was relabeled PASS.

This is a compiled method/source proof, **not** a full engine build, actual
skin render, Android touch test, playback test or physical Fold acceptance.

## Remaining mandatory gates

**P0 Search:** the delivered `_publish_result` still publishes the original
provider URL as a folder, even for state_changed, exactly as the signed460
base. The native Downloads filter is restricted to sources://video/; generic
provider search URLs do not meet that condition. The 460/462 touch controller
handles non-media folder headings through normal native item activation;
the older 451 media-only controller is not the current compiled input.
There is no demonstrated source change yet explaining the reported lost
heading navigation. Replacing that path without its active-device binding
or an actual failing dispatch trace would be speculative.

Known independent false positives remain: strict settings.xml metadata rejects
Nixtoons searchHistory/requestTimes writes and byte-identical rewrites. The
existing meaningful-change and change-then-restore safety cases must remain
protected. A final-document-only hash or relabeled warning is not a safe
correction to that contract. No Search guard was removed or relaxed.

**Watched action:** source still contains Mark Watched and Mark Unwatched in
the existing verified menu. Their source availability is tested, but it does
not establish device reachability, the selected item's identity or durable
state changes. The badge correction does not claim to repair missing actions.

**White graphic:** existing suppression identifies the Live icon only for
ListItem.Icon. The last Files/Add videos bottom-left rendered owner is not
identified from an accessible current render/control trace. No spinner,
progress control, source action, shared add-on or artwork was deleted on a
guess. The QA screenshot's text description is not texture ownership proof.

**Repeated Search stability:** NOT RUN on Android/current installation; no
current faulting stack is available. Historical 2103456 exit summaries and
host loops cannot establish current crash cause or stability.

## Exact stop boundary and next required evidence

The QA branch explicitly leaves active APK/add-on identity unverified. A
single read-only current component/runtime record is required to bind this
candidate to the installation: APK versionCode, Kodi's selected/resolved skin
version and component digest, Command Center authenticated manifest digest
(its version remains .61 across different payloads), and existing Search
rejection/dispatch errors for the two failed heading activations. Do not use
the clean-core .243 export as active-skin proof. Do not ask for a new install,
reset, source deletion, repeated version guesses or another old diagnostic ZIP.

The existing user-input request for current component identity remains pending.
No new evidence upload is requested by this file. If the existing report lacks
the necessary runtime identity/dispatch fields, a narrowly scoped read-only
observer is the next step; changing Health Center or native Search is not
silently authorized by this finding.

Apply/repackage only after that binding and the functional P0 correction are
verified. A coordinated release must use the existing original-key quick
installer path, preserve the working menu/Downloads/native payload, advance
skin generation, and carry a forward recovery to the *current physical-pass*
configuration. The earlier 460-functional recovery is not a suitable new base.

All user physical results remain: PASS 1/2/3/5, FAIL 4/7/8/9, UNTESTED6.
The isolated source proof does not change those acceptance results.
