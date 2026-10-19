# GROUP #1 / TASK #19 — REPEATED CATEGORY-DIRECTORY JOBS, READ-ONLY ROOT-CAUSE EVIDENCE

**Status:** USER SYMPTOM CONFIRMED; REPEAT DIRECTORY LOADS MEASURED; **SOURCE FIX NOT IMPLEMENTED**; no Fold acceptance. No native or addon code altered under this task.

## Grounded user symptom

User video `19049.mp4` shows MOVIES↔TV SHOWS category navigation during one Infinity session, with top Umbrella latest-release and Continue Watching rails temporarily blanking while unrelated add-on tiles remain visible. User explicitly requires content to stay visible **after first successful population in current session**, but accepts normal reload after full Close/reopen. Protect all Home sections and frame/performance features.

## Actual built-in diagnostics analyzed

Read-only collector `repairs/2103390-bugfixes/group1/category_load_diagnostic.py`, git source commit **2d488752644dac901f45cacd79b7d4f2c90aa172**, processed the user-supplied `Infinity-Diagnostics-20261019-000835.zip` → `resume/timing-current.jsonl`. This user attachment remains private and is NOT committed to GitHub. The saved helper emits **aggregate counts only**, no titles, source links, account identifiers, or raw logs.

Result for same process recorded in `resume/timing-current.jsonl`:
- **20** fresh native directory starts for Continue Watching in approximately **49,584.04 milliseconds**.
- **9 movie** jobs and **11 TV** jobs.
- Every directory result remained under **the same saved revision `1792382779737`**; no revised Continue Watching data needed to trigger these requests.
- All **20** snapshot loads reported **cache_hit = 0**.
- In this captured session the 9 movie queries returned zero cards and 11 TV queries returned two cards. **Do not generalize these counts to the user's later screenshots**; results reflect one diagnostic session.
- The local saved-state read typically completed quickly after a plugin job began; longer delays were observed in directory queue/scheduling and skin binding, NOT proof that Kodi's persisted watched database is slow.
- Such repeat loads with unchanged revision are consistent with visible-content repopulation after tab switching, **but the data alone does not prove the exact invalidation event**.

## Related source evidence: read-only ONLY

- Exact 1.0.5.228 Home skin uses category-gated `visible` expressions (`Container(9000).ListItem.Property(section)`) for separate Movies/TV Shows panels. Both Continue Watching controls 8830/8831 are originally horizontal and have plugin-backed content. The **latest-release Umbrella rails are a separate third-party provider**, not Command Center, so fixing only one Continue Watching cache is insufficient to claim task19 complete.
- Kodi's existing native `CDirectoryProvider::Update` can schedule fresh directory jobs on URL, sort/limit or browse changes or `INVALIDATED` announcements. Its `Reset` clears remembered items. No evidence yet proves WHICH actual trigger happens on every category switch.
- **Never change shared native DirectoryProvider**, global GUI engine, Cobra or Umbrella merely because a reload was observed. First isolate the real group1-only Home lifecycle/visibility/refresh interaction. Avoid introducing a second unbounded cache or storing playback history in a new database. Preserve original dynamic revisions/manual refresh and native memory bounds.

## Still required for a legitimate #19 fix

1. Correlate a controlled physical Fold replay of Movies→TV Shows→Movies with Home section, active panel IDs, widget URL/revision, actual provider instance/invalidated reason, and elapsed time; distinguish ordinary post-start population and accidental duplicate panels.
2. Prove minimal Infinity-ONLY fix prevents rendered content blanking for top releases and Continue Watching in both categories, while maintaining correct provider refresh, real user updates, no stale cached source or unintended memory/ANR behavior.
3. Run >=6 fast and normal category transitions, both Fold displays/orientations, photo/video proof, original providers and other controls, Essential-First Close, Cobra strictly untouched.
4. Save actual code/tests commits, provenance and Android/Fold result if/when a proof-backed fix exists. Current record is diagnostic ONLY and **does not count #19 as passed or Group #1 complete**.

**Group #1 status remains IN PROGRESS. Existing source corrections #02, #04, #01 are separately staged/host-tested, and #03 horizontal rail source orientation is checked but touch/vertical chooser remains unproven.**
