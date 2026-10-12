# Independent corrective implementation review

Status: source ready for Android runtime gates; not an APK acceptance, promotion, or physical-device claim.

## Baseline and cause

All 24 Cobra-owned files were independently compared byte-for-byte between the approved 2103324 export and retained 2103369 transport export. Runtime edits started from new copies of the two approved 2103324 files. No rejected 2103370 implementation/test code was copied or cherry-picked. The requested image was inspected only as a Stats presentation reference; its arrows, Status label, cue text and decorative extras were not implemented.

The old Sports predicate read saved `guide_view_mode`. Mobile deliberately writes only its primary-view preference and retains that saved guide preference. Normal fullscreen launch and preview promotion retain actual Pro ownership; full preview destruction clears it. New decisions therefore use actual phone/live-mode/Pro ownership and, for new Stats, current Sports section or Sports hero pane. Existing optional Pro score alerts remain unchanged; no new non-Sports Stats or scores were added. Their old shared predicate is corrected only to prevent actual non-Pro leakage.

## Contracts

| Item | Runtime boundary |
|---|---|
| 1 | Actual fullscreen Channels row/broadcast callbacks only. Transfer existing explicit `CobraMediaAudioState.userMuted` and requested volume during synchronous replacement construction; clear in `finally`. Temporary focus/call suppression is not reclassified as user mute. |
| 2 | Phone-only PiP additions call existing promotion/PiP and same-session return. Non-Pro original mini six-control row remains intact; PiP is a separate corner target. Pro original indices 0–7 remain unchanged; PiP uses 8 and has a separate muted-preview target. Fullscreen non-Pro stays a single non-scrolling row with PiP added. |
| 3 | Actual Pro fullscreen only: horizontal native scroll container, original four-column button width and existing visual/button callbacks. No arrows, cue text, or renamed original controls. |
| 4 | New fullscreen Stats requires actual Pro Sports. It uses the existing Pro mini Stats glyph implementation and shared existing Stats entry. Available metadata and player statistics are added to the original repository response; original team/stat/leader lines remain. Spoiler, stale and unavailable states are explicit. |
| 5 | Only Pro Sports fullscreen Channels broadcast-choice layout is replaced. Original resolver/matching remains. Old drawer is detached before the chooser is attached. Real selectable ListView rows are >=48dp; at least four fit at the specified sizes; small windows put Close beside rather than over the list. Below 192dp usable height for four rows is a geometry hard failure. |
| 6 | Pro header only: same structure, location and callbacks; existing theme text/muted tokens and existing glass surface. No global ambient, video, Night Cinema or theme-setting changes. |

`source_scope.py` enumerates 27 method/class contracts and rejects changed Java tokens outside them and explicitly enumerated added fields. Other source files must remain byte-identical. Its two-file local token check passes; the parent packaging gate must also run it over the complete retained source export.

## Tests and boundaries

`CobraCorrectiveContractsTest` contains 27 tests. It uses approved Navigation/Handoff fixtures, attached production views and actual control callbacks, not rejected acceptance tests. It emits `RUNTIME-CONTROL-INVENTORY.json` only after six-context assertions pass. This artifact does not exist until that Android test runs successfully; it is not pre-written evidence.

The 167 inherited cases remain. The only inherited override is four exact PiP-addition expectations in `CobraProControlsRefinementTest`: callback storage 8→9, Sports/regular label lists gain PiP, and visual index order gains index8. No inherited test case or assertion is removed.

The new tests cover direct Channels filters in all six contexts and both mute states; Sports resolver/broadcast callbacks; non-Sports Pro's existing Sports category; unrelated Previous/Next/Last/direct tunes; requested volume and transient focus/call suppression; enabled local-rewind initial proxy construction; actual mode-card transitions with dirty saved focus; fullscreen Back; actual Activity recreation; mini/fullscreen PiP buttons with controlled Android API boundary and both states; exact rail/order/geometry; Stats data, spoilers, stale/upcoming/null summaries and late callbacks; and Pro header theme/ambient variants.

Initial local-timeshift construction is synchronous: `cobraStartLocalTimeshift` calls `session.start()` and `buildPlayer` on the same invocation; direct fallback in that method's catch is also inside the scoped transfer. Later provider-failure recovery is a different original retune policy and remains byte/token unchanged, as do phone-call/focus/volume/background policies. Tests do not claim provider decoding, acoustic continuity, real Android PiP lifecycle, or physical foldable acceptance. Those remain pending.

No Infinity/native/backend, health/Command Center/Resume Hub/shutdown/Dual Infinity changes were made. The existing sports repository gains only parsing of already-returned summary fields for the requested Stats presentation; its URL, transport and matching are unchanged.
