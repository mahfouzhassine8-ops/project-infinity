# Cobra Sports live feed and ticker audit — 2103323 candidate

## Exact locked parent

- User locked Cobra Pro **2103322** in this session. It is the sole APK/source parent.
- Parent APK SHA-256: `1e25361e32dad7b7cc5a6470b2a98b1f5bb9942b3241306571c8aea9b6beff64`.
- Parent source commit: `712fd77bf5fa343f543fa8f6a1f042e90ad4f13b`.
- Parent verified run: `37568548449`; 151 passing tests.
- Skin remains `skin.infinity.diggz` 1.0.5.201. Permanent signer and install-over package retained.

## Report and evidence limits

The supplied screenshots show Lakers 82–Warriors 109, Q4 5:55 in the video,
versus 67–93, Q3 2:33 in the Sports card. The user confirms the ticker was on.
These establish the visible mismatch, not which individual network request failed.
The audit covers all 15 supported league configurations: NFL, NBA, MLB, NHL,
NCAA football/basketball, WNBA, EPL, UCL, MLS, La Liga, Bundesliga, Serie A,
Ligue 1 and Europa League.

## Confirmed shared source defects

1. Date polling begins at the current device date. After midnight, ongoing games
   from the previous evening can fall out of the request window; the merge keeps
   their old live state. This is consistent with the screenshot's overnight program.
2. The repository counts a cached future date as success while dropping a failed
   current-day request. That failure is hidden from the caller.
3. The caller always advances its global refresh timestamp. Retained old events
   therefore appear fresh to the ticker even if their own data did not refresh.
4. The full-league decision uses that same rolling timestamp. Continuous live
   refreshes can indefinitely exclude leagues whose games have not yet become live.
5. Repeated UI scheduling moves the next poll 45 seconds from each new call.
6. HTTP requests do not bypass caches or check the server-reported cache age.

## Narrow correction

- Poll the previous/current/next dates on live checks; retain the seven-day upcoming
  window on full checks. Calendar arithmetic handles midnight and DST.
- Apply the 30-second cache TTL to previous-day and active/imminent live data.
- Return partial date errors beside successful data; reject malformed scoreboards.
- Preserve each event's local receipt timestamp across cache hits and merges.
  Missing live data becomes unavailable without stopping the existing broadcast.
- Display `Score delayed` instead of stale points/clock details and suppress its
  ticker entries. Recovery with identical scores does not invent a new alert.
- Track full-league checks independently; include imminent games in fast polling.
  Schedule polls against the existing due time rather than resetting the delay;
  an upcoming start advances an otherwise idle poll. Failed leagues join fast
  retries even if their initial request returned no cached games.
- Request HTTP revalidation and reject scoreboards whose HTTP Age exceeds two minutes.

Local receipt freshness does not prove an upstream provider has updated its own
score. The source does not expose a reliable per-event publication timestamp.
External endpoint snapshots therefore remain observational evidence.

## Preservation gates

Only `InfinityLiveActivity.java.in` changes. `source_preservation.py` requires exact
Java tokens outside the explicit Sports data/ticker methods, fields and helpers.
Every other parent source file must have the identical hash. In particular,
`CobraProUi.java.in` is identical: More remains last and the alert remains beside
LIVE SPORTS. Playback owners, navigation, providers, settings preferences, user data,
Infinity Kodi, native engine, resources, assets and skin remain preserved.

Packaging compares protected compiled classes, resolves D8 helper relocation by
exact instruction bodies, verifies resources and manifest identity, merges the
unchanged parent payload and checks the permanent signing certificate.

## Validation

The workflow runs all nine parent suites (151 tests) plus 16 new tests. The new
suite exercises production parsing, cache hits, partial date aggregation, the real
refresh callback, score presentation and ticker with controlled responses across
all 15 leagues. It also covers midnight/DST/time zones, empty/malformed responses,
same-score recovery, final/period/clock distinctions, polling starvation, disabled
leagues and real HTTP cache headers through a loopback server.

`feed_smoke.py` reads current/previous-day public ESPN endpoints for all 15 leagues
and records actual responses, failures and cache headers separately from fixture
results. No physical device or continuous upstream freshness claim is made by CI.

2103323 remains a candidate until the user's device acceptance and explicit lock.

Initial live endpoint observation: 30/30 requests succeeded on 2026-10-07,
covering current and previous dates for all 15 leagues. Lakers–Warriors event
401898390 was returned by the October 6 scoreboard with a UTC start on October 7,
corroborating the need to retain the previous scoreboard date after midnight.
