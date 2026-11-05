# Back/Trailer minimal skin-only proposal — NOT APPLIED

This is a proposal for separate approval. No control ID, click behavior or native file has been modified. INFO-CONTROL-PROPOSAL.patch is inert and outside the APK overlay. It targets the existing unified/DialogVideoInfo.xml overlay only. Its source hash and exact replacements are recorded in INFO-CONTROL-PROPOSAL.json. Future visual edits require rebasing/revalidating this patch before approval/application.

## Exact mechanism and change

CGUIButtonControl::OnClick first sends GUI_MSG_CLICKED to the native dialog, then executes skin click actions. Existing Back ID10 invokes native OnGetArt first; existing Trailer ID15 invokes native OnManageVideoExtras first. Renaming Trailer to native ID11 would invoke PlayTrailer before the existing skin bridge and could create two playback paths. It is NOT proposed.

- Back10 → **9011**, unused in this dialog and outside its native reserved IDs. Preserve PreviousMenu, label, textures, geometry and default focus8. Update its Control.HasFocus animation, loading frame control and registered FrameControls entry.
- Trailer15 → **9012**, also unused. Preserve its existing conditional PlayerControl(Stop), original script.trailer.bridge invocation/arguments, episode visibility, alternate STOP TRAILER label, appearance, and both loading notifications. Update only loading owner.control and corresponding Container references. Keep the existing loading target hash and all request metadata.
- Preserve Play8, Cast5, cast list50, More Info106, all enablement/visibility, AutoExtendedInfo routes and all other controls. Do not replace the trailer bridge or native engine. No scripts, providers, playback code, native source, manifest or permissions change.

The frozen native implementation is a read-only dependency: xbmc/video/dialogs/GUIDialogVideoInfo.cpp and xbmc/guilib/GUIButtonControl.cpp. No changes to those files are requested.

## Inspection performed

The proposal parses as XML, has unique IDs, excludes Back/Trailer from native reserved IDs10/15/11, and reverses byte-exactly to the current source when the documented ID/reference substitutions are undone. Static inspection only; proposed runtime behavior is NOT RUN. Preparation initially caught a reference-count expectation (10 Container references, not12) and an XML-serialization comparison mismatch; the final exact reverse-byte comparison passes. No failed runtime behavior was suppressed.

## Required regression checks after separate approval

1. Actual native Info click dispatch before/after: Back opens no artwork dialog, returns to the exact browser/window/selection; repeated open/close and native Back remain correct.
2. Trailer click with idle player invokes the existing bridge once and never native extras/native PlayTrailer; real supported trailer decodes. During existing playback, the existing Stop action executes once without a second stream starting. Test missing/unsupported trailer, bridge failure/cancel and episode-hidden behavior. Keep error/loading completion truthful.
3. Preserve default Play and Cast focus/actions, More Info conditions, mouse/keyboard/remote/touch behavior, loading owner IDs and focus restoration. No duplicate IDs or dangling ID references.
4. Both themes, cover/inner portrait/landscape and actual Fold transitions. Verify current runtime skin/member identity first. Host inspection is not Android acceptance.
5. Exact whole-file inverse-ID comparison and unchanged native, modules, providers, Preview/Cobra, shutdown, settings/data/signing. No APK/package operation until separately authorized.

The proposal does not fix the separate visual gaps or imply that every existing Info action is correct. Scope remains Back/Trailer only.

## Existing dispatch/loading dependencies (read-only)

The native PreviousMenu action follows Application::ExecuteXBMCAction into ACTION_PREVIOUS_MENU, GUIWindow and GUIDialog::OnBack/Close. The proposal retains that action. The existing signed action_loading.py reads the focused control and registered FrameControls dynamically; the proposed substitutions update those registrations rather than adding another loading system. READONLY-DEPENDENCY-BINDINGS.json records the signed458 script hashes. Runtime loading/focus ownership verification remains required after approval.
