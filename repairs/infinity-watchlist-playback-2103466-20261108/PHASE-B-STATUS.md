# Phase B outcome — verified bounded patch, release blocked by native source scope

Owner authorization8e83bcb8374dec0ccc646cbe02c3c4249395ba8c was read and retained.
Implementation branch: `work/infinity-watchlist-phase-b-20261108`. The protected
2103466 checkpoint, original APK, existing Search work and installed Fold were
not modified. No new release version was reserved and no build, signing,
installation or recovery artifact was initiated.

## What is implemented and verified

A reviewable candidate overlay fixes the confirmed saved-card resume projection:

- `resume_hub.py` adds an opt-in exact movie/episode progress selector. It reads
  current raw `items`, validates existing identity/proof relationships, rejects
  conflicting aliases and respects hidden/completed state. No writes, title
  matching, global identity relaxation or replacement progress database.
- `plugin.py` uses it only for playable Watchlist card offsets and existing
  Play/Information/recovery dispatch. The saved key, identity, route, membership,
  show/season folders and other saved-list behavior stay on their existing path.
- `service.py` is a byte-identical baseline reference. Its player callbacks,
  occurrence handling, persistence and completion thresholds are unchanged.

The final selected host run passed17 cases. The receipt retains an intermediate
fixture error and its fixture-only correction; the final source hashes are
recorded. Astra independently reviewed the actual final diff and matching hashes.
No material regression was found within this bounded projection scope.

`PYTHON-PROJECTION.diff`, `PYTHON-PRESERVATION.json`,
`HOST-TEST-SELECTION.md` and `HOST-PROJECTION-RESULT.json` make the partial work
reviewable and reusable. It is not an installer or the completed feature.

| Gate | Result |
| --- | --- |
| Exact saved-row projection/identity/hidden/completion host cases | PASS17 focused cases |
| Independent bounded source/preservation review | PASS for the stated two-file candidate diff |
| Fresh direct-click offset recheck after rendering | NOT IMPLEMENTED |
| Actual selected descendant → active-item lineage | BLOCKED by additional native boundary |
| Current installed provider enrichment | NOT IMPLEMENTED; source facts recorded, runtime byte admission remains |
| Complete catalogue/late acquisition integration | NOT IMPLEMENTED; supported API candidate and remaining conditions documented |
| Real AV-start/event ordering and ordinary same-title negative control | NOT RUN |
| ARM64 compile/link and focused Android/restart | NOT RUN; no complete native correction exists |
| Signed successor/recovery/install-over/Fold acceptance | NOT RUN / release blocked |

No host PASS is substituted for Android or Fold acceptance. Saving alone is not
changed to create playback history.

## Exact source-evidence blocker

The supplied actual POV6.11.02 code follows this normal route:

1. `resources/lib/modules/sources.py:254` calls `POVPlayer().run(...)`.
2. `resources/lib/modules/player.py:73,81` constructs a NEW ListItem and calls
   `self.play()` using the resolved media URL.
3. The protected native `xbmc/interfaces/legacy/Player.cpp:89–105`,
   `Player::playStream`, clones only that new item into `TMSG_MEDIA_PLAY`.
4. `xbmc/application/Application.cpp:2442` calls PluginDirectory resolution only
   for plugin paths. The fresh HTTP item bypasses that authorized capture seam.

Consequently none of the four currently allowed native files receives the
initiating saved-origin proof on the actual POV playback item. Exporting a
pending global selection from `PlayerOperations::GetItem` and matching its title,
IDs, URL or timestamp would guess causality and could label ordinary playback of
the same saved title as Watchlist playback. That is expressly forbidden.

At least `xbmc/interfaces/legacy/Player.cpp::Player::playStream` needs a narrowly
scoped observation handoff before its fresh-item clone. It must bind the exact
provider invocation, Watchlist nonce/generation and typed playing identity while
preserving existing playback. Existing addon/invoker getters are useful but do
not alone prove the expected invocation: its script ID is private to the current
ScriptRunner dispatch. That invocation-binding contract still needs review;
one additional hook is not promised sufficient. Umbrella's exceptional direct-
play/playlist branches require the same truthful coverage assessment.

A further read-only source review identifies two concrete observation points for
an expanded-scope implementation, documented in `INVOCATION-SCOPE-ADDENDUM.md`:

- `xbmc/interfaces/generic/ScriptInvocationManager.cpp::ExecuteAsync`: register
  the current saved-resolver scope against the actual invoker ID before either
  new or reused invocation executes; clear stale associations on unrelated reuse.
- `xbmc/interfaces/legacy/Player.cpp::Player::playStream`: snapshot caller identity
  before the existing GIL-release guard, then bind the matching registered origin
  to the fresh playing item before its message copy.

Both files are outside the allowlist. This is a source-supported conditional
proposal, not implemented or tested. Preserve existing admission, return values,
thread startup, locking and shutdown behavior; the observer must perform bounded
bookkeeping only, with strictly one-way lock ordering. No demonstrated need for
ScriptRunner, LanguageHook, GUI or player callback edits was found.

**These two files are outside the owner's seven-file allowlist.** The committed
`OWNER-PHASE-B-AUTHORIZATION.md` explicitly says: “If technically necessary scope
exceeds these files, record the precise dependency and seek new owner scope
approval rather than silently expanding.” No edit to either file or another
unapproved native boundary was made. This is a source-scope blocker, not a missing
signing key, a demand for repeated owner diagnosis, or an excuse to rebuild.

`CONTRACTS.md` and `contract-evidence/NATIVE-BOUNDARIES.json` contain the reviewed
source paths, hashes and reasoning. The POV bytes are from the supplied export;
the inspected native files match the retained466 source map.

## Other contract work retained

The existing GUI hooks can correlate cached and nested directory invocations with
bounded thread-local generations, without editing GUI source. Existing signed
Python selection/capsule/confirmed Play supplies a defensible popup-intent
boundary when its fresh one-use handoff is carried on the actual item. These
contracts are documented; no native implementation was begun after the POV
bypass disproved complete path coverage.

The raw TMDb Helper6.20.6 NoCache metadata API is a concrete complete-catalogue
candidate with explicit root/season/episode/count/ID/availability validation.
Filtered directory rows and E+1 are rejected. Actual installed dependency pins,
request bounds and nonblocking acquisition/late-completion consumption remain
integration gates. No installed helper version, catalogue completeness or
successful next-up transition is claimed from source feasibility alone.

## Release decision and continuation boundary

Retain the bounded patch and its passing evidence. Do not apply it to the owner,
ship a partial feature, replace the original signer, reuse2103466, move the locked
baseline, or merge unfinished Search work. The next required scope review is the
two-file native invocation registration and Python Player item-origin handoff. Continue
full implementation only once any additional production files are explicitly
authorized and the remaining corresponding contracts are proven.
