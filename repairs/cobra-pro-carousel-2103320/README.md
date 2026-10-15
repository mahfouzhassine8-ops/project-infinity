# Cobra Pro 2103320 candidate

Working parent: exact 2103319 APK and 254-file source export from run 37538167325, commit 34543c8019a27a782e2c1d4db0d21aabdb4acb2e. SHA-256: 576b60dfd63cd41b8b901db2424a34cc422ba1b991641336a6e00d9c9035ce40.

Release lock remains 2103317 with skin.infinity.diggz 1.0.5.201. Candidate 2103320 is not a new lock. Keep permanent signing, package identity, native engine, assets, resources, providers and data.

User-approved behavior supersedes 3319's independent continuing stream on carousel swipes:
- Main remembers the explicitly played channel. Leaving it releases the stream. Every normal preview pane visit starts that pane's muted preview. Returning to Main is stopped with Play ready. Play from a preview makes that channel Main.
- Sports has a dedicated Main and live-game preview panes. Sports Main retains its game while browsing; return is idle with Watch Live. Broadcast resolution must be confirmed; stale async results cannot start another pane. Empty Sports remains idle.
- Mini controls overlay a constant full video viewport. Hidden controls and their background leave no reserved opaque band. Aspect-preserving fill and Sports tap/hold sizing remain.
- Sports playing controls scroll horizontally and include Stats and Multi-View. Strip gestures do not advance hero panes.
- Pro channel rows reuse the existing actual-playback dot, including its cyan/OLED handoff and Night Cinema amber policy.
- Fullscreen > Channels > Sports > Game Options dismisses the competing drawer before opening an unanchored options sheet. Reopening Channels retains Sports.
- Optional score ticker uses the subtle translucent visual direction. It appears for six seconds then fades fully away. Confirmed score changes, period changes or major status changes trigger another alert; clock-only changes and duplicate refreshes do not. Favorite team games can alert over unrelated playback. Hidden spoilers suppress alerts. Queued updates coalesce per game, expire after two minutes, and do not tune, resize or replace playback. Visibility is independent of player controls.

Validation: updated the 3319 tests whose expectations are explicitly superseded; retain unrelated theme, transport, Sports, teams and Multi-View tests. Added state transitions, late async result, exact drawer path, control-scroll ownership, real playing-dot policy, and event-alert lifecycle checks. The older ticker protection test now expects no popup while spoilers are hidden. Run the production Android/Robolectric suites and preservation gates before packaging.

No physical device or provider-decoder acceptance is implied by controlled tests. Report real verification and limitations with the candidate.
