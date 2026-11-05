# Continuation from a7f65029 — source candidate, not acceptance

Signed2103458 is unchanged and remains the immutable working base. This continuation changes two existing skin XML files; it adds no native code, scripts to the application, controls, providers, services or permissions. No APK was built/signed/installed/promoted/locked.

## Implemented visual refinements

`Includes_InfinityMediaLists.xml`: selected synopsis98064 now uses the native textbox's content-driven height (`top0`, `height min40 max0 auto`) inside the existing scroll group. Previously max30% clipped the text itself: scrolling the parent could not expose lines clipped inside the textbox viewport. Explicit top0 avoids the factory's missing-position height fallback. GUITextBox uses its measured text height when m_height is zero; its existing render viewport, page-control and all input routes remain unchanged. Empty/short text keeps the established minimum. This is not the withdrawn arbitrary max4000 experiment.

`DialogVideoInfo.xml`: long existing title/metadata/cast labels use native label overflow scrolling, without changing label types, IDs, content or fonts. Existing Cast cards use a wider1.6 aspect ratio rather than1.03448; artwork remains proportional and native selection/cast ownership is unchanged. Plot400 uses14% of height, fitting between its existing top27.037% and the unchanged action-row top42.4074%; this uses available portrait space without moving buttons or changing the existing autoscroll=false. All existing actions, loading notifications, colors, visibility, enablement, themes and data bindings remain exact.

Exact diffs are adjacent. POLISH-PRESERVATION.json in the parent directory records the current four-file cumulative overlay against signed2103458: prior drawer cleanup, Info, shared List include, prior season-variable correction. Drawer/Power and Variables are byte-identical to a7f65029. Only Info and the shared List include changed this turn.

## Proposals — unapplied

- Back/Trailer: the existing parent INFO-CONTROL-PROPOSAL.patch was rebased onto the new visual bytes only. Back10-to9011 and Trailer15-to9012 substitutions, preserved actions and separate approval requirement are unchanged. Native ID10/15 conflicts remain in the running source; no workaround concealed them.
- Details: DETAILS-NAVIGATION-PROPOSAL.patch changes only Up on98070/98071/98072. It selects existing scrollbar98066 when visible, otherwise list50. Frozen GUITextBox cannot focus; native GUIAction supports ordered conditional numeric targets and the existing scrollbar hides for one-page content. The review describes exact scope and regression tests. This proposal is outside the overlay and has not been executed.

## Verification and actual visual review

Five focused host cases PASS: exact substitutions, nonvisual/data/theme preservation, native auto-height declaration, Info plot/action separation, cast width and label overflow. Before failures are preserved in BEFORE.txt; AFTER.txt records the result. Earlier evidence remains source-bound to its historical hashes rather than relabelled as a new pass.

Actual upstream Linux Kodi fixtures with explicit responsive projection, synthetic media and the existing full skin:

| Fixture | Selected checks | Result |
|---|---:|---|
| 564x540 final content sequence | 53 | PASS |
| 540x1260 cover-shaped portrait | 43 | PASS |
| 1260x540 cover-shaped landscape | 61 | PASS |
| 540x564 inner-shaped portrait, including short/empty plots | 25 | PASS |

The first three exercised movies, shows, seasons and episodes in Light/Dark, native Info/Cast where supported, Back and selection restoration. The fourth exercised movie rendering/Info and short/empty synopsis selection in both themes. Exact source and executed probe hashes are in EVIDENCE-BINDING.json and each fixture's CONFIG/EXECUTED-PROBE. This is not the frozen Android engine, real providers, physical display dimensions or Fold acceptance. No playback or unrelated shutdown suite was executed; only disposable fixture processes were disposed of.

Visually inspected actual screenshots show the final synopsis endpoint for movies and seasons on the short viewport; episode text endpoint also remains accessible. Cast names are readable on the widened cards; narrow titles use the existing native marquee rather than losing their text. Portrait Info displays more plot text without action-row overlap. Short/empty plots retain the title, metadata and actions. The original brief's full provider/all-view/pixel-equivalence acceptance is NOT claimed. Existing fixed Info slots still reserve Cast space when the native dialog hides Cast, and long Info plots can exceed their fixed region; no new scrolling/navigation behavior was added to that dialog.

## Failed evidence retained and bounded follow-up

The initial asynchronous Down loop failed seasons-scroll-preserves-item. Isolated season tests passed before and after. The full sequence then passed both before and after when test input used supported executebuiltin(wait=True), preserving selection across content transitions. The original failure remains in results/564x540-media-a7-content-height; it is not deleted or relabelled. This comparison supports a test-dispatch timing explanation, not proof that rapid physical inputs cannot expose a problem.

The earlier HasNext endpoint assertion remains failed evidence. Frozen GUIControlGroupList sends integer page ranges to the scrollbar but compares a floating total/offset in HasNext; it can remain true at the integer scrollbar endpoint. New tests record HasNext as an observation and inspect the actual endpoint screenshot. This does not repair native rounding or waive missing visible text. No native edit occurred.

The details group also retains scroll across directory/item changes. Later visual fixtures explicitly scroll up using the existing scrollbar before top-of-page screenshots, then inspect the endpoint separately. That QA action is disclosed and is not a production reset. Automatic detail-scroll reset was not added; any such behavioral change needs separate review. The old nonfocusable textbox target remains an open behavior defect pending its proposal.

## Other authorized groups, unchanged protections

**Navigation:** no new current-device runtime export exists. Only the original historical2103456 diagnostic ZIP and supplied image are accessible. The active2103458 skin/XML/module identity remains unverified. Signed drawer destinations already contain full `videodb://movies/titles/` and `videodb://tvshows/titles/` URLs. They were not replaced with guessed aliases. Existing runtime collection instructions remain in RUNTIME-EVIDENCE-PLAN.md: Health Center's current active-skin export, resolved module hashes and actual directory/history observations. No Back/history behavior was changed.

**Downloads:** existing native filtering/classification dependency remains blocked. DOWNLOADS-BOUNDARY.md is unchanged; no shared sources, provider definitions or storage permissions changed.

**Search:** source SHA61501614f0b49b407dea024a27d7cc6698979a8fc56aa00ec786c368b4e63a78 remains unchanged. Read-only ownership tracing confirms one abstract-socket admission per Kodi PID, held until the actual RPC worker exits; cancellation does not detach that worker or clear live tokens. Providers run sequentially. Cache retention is at most four entries under the existing300000-character serialized cap per provider, but these caps do not bound transient native/provider/JSON allocations or prove absence of a leak. No new simulation or crash fix was claimed.

The aggregate publication path validates the response signature after a completed native request; the direct-provider heading preserves the verified route and opens the provider's own directory without that aggregate response-publication check. This explains how the direct search can work while Infinity rejects publication; it does not identify Crew's changed component. Nixtoons' settings self-invalidation remains uncorrected, Crew attribution remains unknown, and both acceptance failures remain FAIL. Source verification, meaningful-change detection, cancellation and ownership checks were not weakened. The archive contains no request-specific rejection log or usable native failure stack. Real30-search Android stress remains NOT RUN.

**Universal view coverage:** VIEW-COVERAGE.json inventories25 registered video view IDs and signed-baseline-bound definitions. Shared Info refinements apply where the existing native Info dialog is used; shared List refinements apply where that include is used. Custom provider dialogs and distinct view designs were not replaced. All-mode Android rendering remains NOT RUN; static registration is not visual proof.

## Remaining gates

1. Separate approval and actual behavioral testing for either navigation proposal.
2. Current2103458 runtime identity plus library transition evidence before navigation attribution.
3. A separately approved Downloads-only native scope and reliable source classification.
4. Real Search rejection/stack evidence and repeated Android searches, keeping both known failures open.
5. Actual Android/Fold visual and touch testing across registered modes, providers, orientations and fold transitions; complete remaining Info/full-text presentation review without changing functionality silently.
6. No packaging until the authorized correction program and all signing/preservation/recovery gates are satisfied or explicitly dispositioned by the user.

Cobra, Preview, native engine, playback, shutdown, providers, real settings/data, original signer and recovery locks have no edits. Exact candidate APK-member comparison is NOT RUN because there is no new APK. The source candidate remains consolidated on the existing work branch.
