# Coordinated Fold testing update — not completed physical repair acceptance

Established user device evidence: APK2103462, Infinity skin1.0.5.262,
Command Center0.3.5.61. No further identity request is pending for execution.

## Implemented source corrections

- Explicit provider selection in the existing Search form now opens the
  provider's own verified query URI through normal Kodi Videos navigation.
  The previous form path invoked the aggregate collector, whose settings
  stamp check can discard these providers' results after their own writes.
  The shared route verifier runs before and after history persistence; an
  abort or changed source prevents activation. This applies to the existing
  provider inventory, not separate replacement searches. Search All's source,
  settings, cancellation, ownership and publication functions are unchanged.
- Info native Play8 remains the sole playback handler. Establish a nonzero
  button-group viewport at load; render the unchanged video preview before
  the buttons/Cast so it cannot intercept their touches. All existing Trailer,
  Cast, More and Back actions/IDs remain unchanged.
- Shared rows now show existing overlay-only / ResumeHub-property-only watched
  states. For identified movie/show/episode plug-in folders, add direct native
  context entries for the existing Infinity Watched/Unwatched writer. Kodi's
  native file actions deliberately exclude plug-in folders; the new entries
  exclude ordinary files, retain the original exact-item identity checks,
  menu-state recheck, newer-progress rejection, writer scope and pending sync.
  They cannot invert a stale displayed action or authorize unsupported IDs.
- Hide the exact static white skin icon in InfinityMedia_CommonBackground only
  on native Videos/Files/empty-content surfaces. Its bottom-left coordinates
  and packaged PNG match the reported curved graphic. The prior Live-item-icon
  suppression missed this direct texture. No asset, busy indicator, Add videos
  action or folder/source behavior is removed.

Six runtime files differ from the delivered262/CC61 functional reference:
DialogVideoInfo.xml, Includes_InfinityMediaLists.xml, infinity_search.py,
context.py, plugin.py and CC addon.xml (context registrations, version unchanged).
All other runtime sources, four native Downloads files, Power/drawer/menu
bindings, Cast metadata, native playback, Cobra, Preview and shutdown remain
unchanged. Installer assembly advances authenticated skin metadata and CC
manifest/signature only; it does not create an APK or modify the signing key,
workflow, authority, native module bootstrap or production installer.

## Evidence

15 new integrated host cases: ten passed on the initial run; five form-fixture
cases initially errored because the host lacked xbmcvfs.translatePath. The
fixture was corrected, and only those five failed cases were rerun and passed.
Both logs are retained. No production failure was relabeled PASS. The actual
original Hub mark/save/load functions were executed on a temporary host store;
Watched/Unwatched survived reload while unrelated lists/source records remained.
That file-transport boundary is not Android durability acceptance. Existing
writer/identity helper ASTs and aggregate guard functions are unchanged.

The previously passing six native-method/Info geometry checks from9ab8ec01 are
reused, not rerun. Current Info XML matches that candidate's recorded SHA.
Changed Python compiles and addon XML parses. No unrelated shutdown suite,
general campaign, simulated30-search crash claim or device acceptance is used.

Packaging must verify the exact previously original-signed artifact13495017909
SHA3bfb47761e7e2aad2f24c5f24967ec8e8ba1da43b97cdbe299e2cf93703d4298,
all78 module hashes/signature and948 skin hashes, then enforce exactly six
runtime differences. The original owner-gated workflow and Java signer stay
byte-identical. A fresh original-key module signature and signed outer envelope
cover the full normal add-on ZIPs. A six-case real Java installer audit on new
disposable host profiles must reject partial source/manifest pairs and accept
exact current-generation forward recovery before artifacts are published.

## Remaining limitations — do not hide these

The new explicit-provider dispatch addresses that confirmed conditional flow.
The original Search All provider-heading URI was unchanged between signed460
and the delivered262 payload; an actual Android heading failure is not yet
causally reproduced here. Do not claim this source change proves that separate
reported heading regression fixed. The two Search All settings-history / byte-
identical-rewrite acceptance failures remain open. No final-document-only
settings exemption, stale result publication or weakened source guard was added.

Real provider results, control touch reception, watched reachability and 30
consecutive searches on Android17/Fold are NOT RUN in this executor. No
compatible device is connected. Native Search crash cause is not proven; the
historical456 exit summaries are not current462 faulting stacks. There is no
speculative native or memory change, and no crash-fix or full-completion claim.

## Package/recovery intent

Candidate: skin1.0.5.264 plus the matching original-key-authenticated CC61.
Recovery: skin1.0.5.265 restoring EXACT262 functional files plus exact previous
CC61 payload. Recovery does not revert the native462 Downloads implementation,
databases, source settings or user-added folders. It is a forward skin version,
not an APK downgrade. Previous signed releases/locks remain untouched. Once265
is installed, any future corrected skin must advance beyond265.

These are coordinated TESTING installers, not final acceptance. No automatic
installation, promotion, baseline replacement or lock is authorized.
