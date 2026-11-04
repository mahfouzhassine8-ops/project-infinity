# Global media view and first-entry List correction — source only

Continuation of `ca5153cbeac5a4a35f5c41a13c53ac0e83f0b3b2` on
`work/infinity-kodi-2103453-ui-navigation-source-20261104`.
The preceding report is retained verbatim in
`results/list-continuation/CA5153CB-REPORT.md`; its failures and evidence remain
available. No APK/component was built, signed, installed, released or locked.

## Result and confirmed mechanisms

The source candidate retains one explicit movie/TV view preference across
providers, categories, pages, Back, refresh and reopening. Unsupported views use
a registered fallback without replacing the saved preference. Unclassified
folders and unrelated windows retain native behavior.

1. **Native preferences were directory-specific.** Kodi stores views by full
   path/window/skin, so another page/provider can restore a different view.
   Providers can also issue `Container.SetViewMode` after supplying results.
   The earlier synthetic-provider test reproduced Posters changing to Icons.
   The global policy is an explicit user-requested change; neither that fixture
   nor the original recording establishes Red Light's exact historical URL or
   override. No provider settings, source or native view database is changed.
2. **First-entry List registered the wrong implementation.**
   `CGUIMediaWindow::Load` expands includes and registers containers before the
   new directory has supplied its content type. Changing a content-based include
   condition alone could therefore leave generic folder rows registered as 50.
   `CGUIViewControl::UpdateViewVisibility` reevaluates registered controls; it
   does not instantiate an omitted include. This is reproduced by the retained
   failing host case and the prior Linux first-entry capture.
3. **Candidate refresh race, found and corrected here.** The global observer
   previously treated an unchanged context as indefinitely pending. Kodi can
   process its request and a provider can replace the view before the next
   observation. The initial and diagnostic Linux runs fail after Refresh with
   saved List 50 but visible Icons 500. The bounded trace remains `pending`;
   a host counterexample proves the missed-observation ordering. This was a
   candidate defect, not a claim about the signed baseline's implementation.
4. **View Options geometry and close handling** remain as previously corrected:
   narrow selector columns and the redundant, small off-panel close target are
   replaced only in Videos by scoped wider panels and explicit close/Back
   actions. The original shared selectors remain unchanged. View 54 was ruled
   out: it is excluded from Videos; the existing movie ShowCase is 53.

## Exact source correction

Detailed VideoList/SlimVideoList is registered as canonical **50** before any
provider result arrives. Existing core/plugin/compact folder lists receive
internal IDs **65050/65051/65052**, below Kodi's 16-bit view-ID limit, with
separate scrollbars. Runtime content predicates expose exactly one List family.
No user-facing view is added, removed or renumbered. Existing Cinema remains its
original implementation. The original List artwork, text, dimensions, metadata,
actions and saved settings are retained in Videos-scoped copies; the shared
`View_50_List.xml` is untouched. Native fallback resolves legacy List choices in
folders, and native focus redirection returns to the current internal container.

Videos-only header/background/letter-navigation compatibility copies preserve
List semantics for those internal IDs. Existing loading-frame bindings include
them. No skin reload, provider rerun, refresh action or native change is used.

The observer now posts a unique acknowledgement to a transient Home-window
property after its `SetViewMode` command. Both use the existing FIFO GUI builtin
queue; native SetViewMode completes message dispatch before SetProperty runs.
The acknowledgement means **processed**, not successfully displayed. The next
ordinary foreground tick still checks the visible view. An old acknowledgement
cannot release a newer request. An unprocessed request remains coalesced; a
processed request that lost to a provider override can be reapplied. There is no
new timer, synchronous GUI wait, worker, persistent setting or diagnostic log.
Existing checkpoint/background guards and all original service bytes are
preserved after removing the three previously declared observer hook lines.

### Proposed members relative to exact signed 2103453

All paths below are under `assets/addons/`.

| Member | Authorized change |
|---|---|
| `script.infinity.commandcenter/service.py` | Existing three additive observer-hook lines; unchanged from ca5153cb |
| `script.infinity.commandcenter/media_view.py` | Global media preference observer; transient GUI acknowledgement added in this continuation |
| `skin.infinity.diggz/unified/MyVideoNav.xml` | Scoped menus, static List registration, internal folder IDs and compatibility/loading bindings |
| `skin.infinity.diggz/unified/Includes.xml` | Two include declarations; all original bytes retained |
| `skin.infinity.diggz/unified/Includes_InfinityMediaLists.xml` | New Videos-scoped existing List variants and compatibility includes |
| `skin.infinity.diggz/unified/Includes_InfinityVideoOptions.xml` | Scoped menu/settings definitions; logical List conditions include folder IDs |
| `skin.infinity.diggz/unified/custom_1136_InfinityVideoViews.xml` | Explicit global media choice, compatible folder List target, close/Back/focus behavior |
| `skin.infinity.diggz/unified/custom_1137_InfinityVideoViewSettings.xml` | Prior scoped settings panel, unchanged from ca5153cb |
| `skin.infinity.diggz/unified/custom_1138_InfinityVideoDisableViews.xml` | Prior enabled-view panel, unchanged from ca5153cb |
| `skin.infinity.diggz/unified/Custom_1198_InfinityNav.xml` | Prior Navigation/Library destinations, unchanged from ca5153cb |
| `skin.infinity.diggz/resources/lib/infinity_library_navigation.py` | Prior on-demand native routing helper, unchanged from ca5153cb |

Four existing members and seven new source members. Compared with ca5153cb,
five proposed members are byte-identical and six are changed/new. Exact hashes
are in `SOURCE-PLAN.json`, `results/LIST-SOURCE-PRESERVATION.json` and
`results/list-continuation/EVIDENCE-BINDING.json`; continuation diffs are beside
that binding. Original shared layouts and menu implementations are untouched.

Navigation retains Home/Movies/TV actions, adds the existing configured Sports
route and native Favorites, and exposes Infinity Movies, Infinity TV Shows,
Browse Files, Downloads and Media Sources. Missing Sports configuration and
inaccessible Downloads produce recoverable messages, not invented destinations
or permission bypasses. No scanning, importing, deletion, new player or new
library database is introduced.

## Focused verification

Tests were selected before execution in `LIST-CONTINUATION.md` and
`CONTINUATION-SCOPE.md`.

| Current evidence | Result | Meaning |
|---|---:|---|
| First-entry host counterexample on previous source | Failed as expected | Generic folder List remained registered after movie content arrived |
| List registration and preservation cases | 9 passed | Exactly one runtime family, static registration, original subtree semantics, IDs, folder actions and compatibility |
| Affected skin contracts | 13 passed | Preserved view actions, menu/close contracts and drawer structure |
| Refresh-race host counterexample on previous observer | Failed as expected | Processed request plus unobserved override stayed pending |
| Updated global preference host cases | 17 passed | Provider/page/category policy, replacement, fallback, restart, stale acknowledgement, queue coalescing and exclusions |
| Linux Regular continuation | 42 assertions passed | Cold Files entry registers detailed List; movie metadata; real Next/Back/Refresh; files-to-TV; episode fallback/restoration; focus; no provider rerun on view choice |
| Linux Slim continuation | 26 assertions passed | Detailed Slim List and folder/TV transitions |
| Linux Compact continuation | 26 assertions passed | Detailed media List plus existing compact folder variant |
| Linux Cinema preservation control | 25 assertions passed | Existing Cinema List and folder/TV transitions retained |
| Final folder-visibility compatibility check | 26 assertions passed | Raw Videos List conditions recognize internal folder IDs; source equivalence preserves media/Cinema conditions |
| Exact signed-source preservation | Passed | 11-member source allowlist/preimages, protected APK and engine hashes |

This continuation executes **39 distinct focused host cases and 145 Linux assertions**.
Assertions include setup/state checks, not 145 independent workflows. The
11 navigation and five privacy-probe cases are reused: navigation bytes and
probe privacy/database functions are unchanged; the probe only adds the three
internal IDs to its observed ID list. There are **55 distinct host cases** in
the cumulative source evidence, not 55 newly executed cases.

Earlier native Linux pagination/other-view, restart and mouse-close evidence is
retained with its original source binding. The persistent Skin.SetString action,
key, native storage implementation and pointer geometry are unchanged. Those
results are not relabeled as new executions on every current byte. The updated
observer is covered by the 17 host cases and new Linux List/fallback scenarios.
The final folder-visibility delta has its own source equivalence check and
26-assertion runtime run. Earlier media/Cinema runs retain their tested XML hashes.
The real Command Center service/authentication lifecycle is not started in this
fixture; the candidate helper runs through actual Kodi APIs at the existing
0.5-second observation cadence, with other production services stubbed.

The two initial refresh failures, bounded trace, first-entry/refresh host failures
and the folder-visibility source counterexample are retained. The acknowledgement correction passes that same Linux
scenario. No timeout was increased and no failed assertion was suppressed.

## Preservation

Signed 2103453 remains untouched:
`08ca19e9ff01e3830253980028dbcdbfb36056fd71b06a18cbfb922158ceaac8`.
Protected ARM64 engine remains:
`d0b6f115e839fbe39e764e2fecad47418c501ab1ece853294578652cd0b80b98`.

The source gate excludes all **7,613 other baseline members**, including all
**5 DEX and 47 native members**, from modification. Preview, Cobra, providers,
playback, native/shared components, manifest/permissions, databases, user files,
shutdown protections, signing and recovery locks are unchanged. This compares
a proposed source overlay with the actual signed APK; it is not a candidate-APK
comparison, because building one is not authorized.

## Remaining evidence and device requirements

- The original ZIP was independently inspected by another reader, not opened
  on this executor. Its reported SHA-256 is
  `eecf9f10f1c2a0c6356b9f28f6dffaa7df7d50d2133cf784ae19e1ffa08c7701`.
  Attributed observations and their limits are recorded in LIST-CONTINUATION.
  No direct video playback or visual acceptance is claimed here.
- Current Linux screenshots were inspected. They visibly misrender percentage
  row heights/aspect geometry, including overlapping List text and stretched
  artwork. Upstream Linux lacks the protected Infinity Android percentage/auto/
  aspect implementation. **These screenshots do not pass visual acceptance.**
  No speculative geometry rewrite compensates for the different renderer.
  First-entry container ownership is now verified; full movie-detail layout,
  proportional art and spacing require the preserved Android engine on cover,
  inner display and both orientations.
- Actual Red Light and other installed providers, fast repeated navigation,
  Android restart, fold/unfold, touch/remote use and display reflow remain
  untested on the physical Fold. Directories that omit usable movie/TV content
  retain native behavior; the candidate does not guess from private URLs.
- Android Downloads authorization, real local playback/return, native library
  collections and configured Sports require accessible device sources. API
  fixture passes are not physical storage or playback evidence.
- Optional bounded `view_probe.py` remains outside the production overlay and
  has not been run on the Fold. It records no raw URL, private media title,
  credentials or arbitrary setting value, and never changes a database.
- A later separately authorized packaging step must regenerate existing trusted
  source manifests and verify full service integration. No guard is bypassed.

Source-level corrections and available focused checks are complete as described;
Android visual/functionality acceptance remains pending. No APK build, signing,
release or lock is authorized or performed by this continuation.
