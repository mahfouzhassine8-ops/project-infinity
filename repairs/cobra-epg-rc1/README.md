# Cobra EPG data repair RC1

Source repair candidate on top of immutable adaptive-view commit `a1166a505696e90cd5032c06877b0bce36dc3c42`. Not an APK, not a final lock, and not proof of real-provider or physical-device behavior.

## Scope

Repairs the 11 acceptance gaps reproduced by the 2026-09-17 EPG audit: current-program fallback hidden by expired XMLTV; stale channel-ID memoization; metadata-only refresh detection; destructive manual refresh; stale disk publication; cross-feed ambiguous aliases; first-feed whole-channel replacement policy; missing optional stop times; visible-guide refresh without playback; coverage-blind freshness; and multiple advertised playlist guide URLs.

Manual refresh preserves the last successful timestamp and snapshot. New snapshots are identity-keyed, serialized, generation-checked, and atomically committed. Legacy v3 snapshots remain readable after identity validation. Source snapshots are bounded to four identities; the inherited short-cache pruning remains in force. A forced short-guide refresh also bypasses stale complete-now/next and cache checks without deleting saved data.

Exact channel IDs retain precedence. Generic ambiguous aliases are unresolved, not guessed. Earlier configured feeds win overlapping intervals; non-overlapping coverage is merged and deduplicated. We do not split provider programmes or fabricate descriptions or durations. Current-time lookup can use a same-channel short record where primary XMLTV no longer covers the requested time. Missing end times remain explicitly unknown, are retained in the channel schedule, and cannot initiate duration-dependent recording/catch-up actions. Unknown-end entries do not assert that a channel is currently broadcasting that programme.

Refresh remains foreground/visible-guide or player scoped, with source freshness and retry bounds. There is no always-on background poll. New guide URLs are bounded, deduplicated, HTTP(S)-validated and included in the effective source identity. No provider endpoint is guessed beyond the existing supported playlist-to-XMLTV derivation.

## Protection and rollback

`apply_epg_repair.py` rejects any whole-source hash except the exact audited 2103153 and adaptive 2103154 sources, verifies every targeted member preimage, refuses in-place overwrite and leaves all non-targeted unique Activity methods unchanged. The six adaptive layout/row classes are checked byte-for-byte. Native code, playback/session methods, credentials, installed userdata, app identity, and signing keys are not changed.

Primary input: run `35180825737`, artifact `10481131761` (`Cobra-2103154-Layout-Evidence`), generated source SHA-256 `923a43943ecdf0ff096eb3206cd7ab70dcb22063d2f23f5856546b62469ff326`.

Exact last packaged rollback: same run, artifact `10481331133` (`Cobra-2103153-Complete-Rollback`), outer ZIP SHA-256 `a5c506d78f51108674b9108a8bb29608722e9f03213281b52bfc784c84fbbca2`. Its embedded `SHA256SUMS` and APK/source/UI/archive files were verified locally. The APK SHA-256 is `dff23c9488ff38790ad116fe6fa0d93f68c7a788e4b78fcffc88a38e247088b6`. A successfully validated installable 2103154 APK is not available from that run; it is not falsely described as the rollback APK. No device userdata backup is included. Never uninstall or clear app data just to downgrade.

## Verification

The original 41 audit cases remain unchanged. They passed 30/41 on the original baseline (11 reproduced failures) and 41/41 after repair. Twenty-five additional integration edge cases and nine production short-request cases pass. Seventeen patcher/protection checks pass. The inherited parser/layout/player-store suite passes 42,339 original assertions and the unchanged adaptive geometry harness passes 12,223 assertions.

These are host tests: StAX XML, fake HTTP, host AtomicFile, simplified URI/widget/visibility adapters, and explicitly structured JSON transport doubles. They are not Android AtomicFile crash durability, actual Android XML/URI parsing, TLS/authenticated provider transport, real playback, sustained memory/battery measurements or visual acceptance. The companion CI separately compiles the complete generated Android Java shell against its matched original source/resources; its status must be read from the actual run, never inferred from host results.

The CI uses no production signing secret, does not assemble/sign/release an APK, and does not rebuild the native engine. Do not bypass the independent adaptive-layout/device acceptance gate to package this source. A release candidate still needs successful Android compilation, matched-APK integrity/signing checks, all pending visual gates, and physical-device guide acceptance.

## Running the tests

Use Python 3 and JDK 21. Download the exact layout-evidence artifact into `inherited154` (its top level contains `preflight` and `engine`). From the repository root:

```sh
python3 repairs/cobra-epg-rc1/apply_epg_repair.py --source inherited154/preflight/2103154-final.java.in --output epg-evidence/InfinityLiveActivity.java.in --receipt epg-evidence/repair-receipt.json
python3 repairs/cobra-epg-rc1/tests/run_tests.py --source epg-evidence/InfinityLiveActivity.java.in --out epg-evidence/host
python3 repairs/cobra-epg-rc1/tests/run_short.py --source epg-evidence/InfinityLiveActivity.java.in --host epg-evidence/host --out epg-evidence/short
python3 repairs/cobra-epg-rc1/tests/run_inherited.py --source epg-evidence/InfinityLiveActivity.java.in --repository . --mode-harness inherited154/preflight/mode-regressions/CobraModesHarness.java --out epg-evidence/inherited
python3 repairs/cobra-epg-rc1/tests/run_guards.py --source inherited154/preflight/2103154-final.java.in --out epg-evidence/guards
```

`ci_compile.py` is for a disposable GitHub runner with the two explicit checkouts and donor/evidence artifacts in the workflow. It is not an installer and should not be run against an installed device.

Device acceptance remains: correct known-channel Now/Next, explicit missing-data states, online launch and offline restart, failed manual refresh, metadata-only source refresh without stream reconnect, changed guide configuration while an earlier request completes, programme boundary, guide browsing with preview stopped, and all five view modes. Diagnostic evidence must redact credentials and credential-bearing URLs.
