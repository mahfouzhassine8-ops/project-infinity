# Current Fold Search trace — FIRST ACTUAL FIRST-PARTY REJECTION EVIDENCE
Date: 2026-11-07 UTC (collection 05:49:26–05:55:27).
Source: User-submitted `Infinity-Search-Trace-before-20261107T055527Z-fe17ee460026ae39.zip`. **Only sanitized summary is committed; no raw trace ZIP, queries, settings, media names, URLs or device paths.** ZIP has valid CRC and all 11 SHA256SUMS entries match.

## Grounded identity
- Kodi selected skin: `skin.infinity.diggz`, version **1.0.5.262** (start and end).
- Authenticated Command Center installed: `script.infinity.commandcenter` **0.3.5.61**.
- Actual `infinity_search.py` SHA256 `245e599843b817bfa7f06b1db212502790a2dca13d229e21367060beb1fa9b6c` — matches the delivered 2103462 quick-update source, **NOT proof 266 has been installed**.
- Signed Command Center `INFINITY-MODULES.v1` SHA256 `7f90cb34e4035b36b670289bbcafa18e596c211527e41adf5ac7820288e8396b`, signature SHA256 `540ca08b74ff1212e2a27702065f11afb7bda2ad758e1faa4c5f4476b8a3a4c7`.
- Selected skin `unified/DialogVideoInfo.xml` SHA256 `3e1323aec4af3121d4283d55bcb77f5b1d05dd892593854835e36e7b64b51460`.
- Providers installed: `plugin.video.watchnixtoons2` **0.14.24**, `plugin.video.thecrew` **3.2.2**. The trace itself cannot read APK versionCode, but the earlier Health Center export established **2103462**.
- Active-file hashes are not proof of dynamic Python invoker load identity; source hash + manifest identity are established.

## Actual observed aggregate rejections
Trace contains four **first-party structured `INFINITY_SEARCH_STATE` rejection records** (each a successful Search provider request subsequently rejected by aggregate):
1. Nixtoons: `native_request_status=completed`, **31 original results**, `cache_hit=false`, changed category `provider_settings_metadata`, original provider route retained.
2. Nixtoons: **31 original results**, same status and category.
3. The Crew: **2 original results**, same status and category.
4. The Crew: **2 original results**, same status and category.

All four are `REJECTED_BY_AGGREGATE`. In this evidence, **neither provider returned zero results**. The rejected path is **the post-response snapshot comparison**, not a confirmed failure to search. The change is specifically **provider settings file metadata**; the trace does **not** prove whether the underlying bytes semantically changed, whether the writer was harmless history/requestTimes, or whether a meaningful intermediate write-and-revert (ABA) occurred. Both writers are UNKNOWN. Preserve all source, configuration, ownership, cancellation and ABA integrity guards.

## What is not established
- Only existing script-invoker log hints were seen; these have **no shared correlation token** with the four rejections and are NOT proven heading-click or native dispatch events.
- Kodi window IDs at the trace start and end were both 10040; these are **snapshots**, not a navigation stream. `provider_heading_actual_pressed=NOT_OBSERVABLE`, `dispatch_call_and_return=NOT_OBSERVABLE`, `provider_directory_rendered=NOT_OBSERVABLE`.
- Rotated Kodi log was used; full cross-layer correlation was not available. In-session 10 sanitized events; no native faulting-thread trace, no crash proof.
- This is **BEFORE-repair** mode, with no matched after session; **no fix or verification PASS** is implied.

## Engineering next action — P0
1. In the **delivered Search All `_provider_result`** (see `infinity_search.py`), investigate how `_query_file_stamp` `st_dev/ino/size/mtime_ns/ctime_ns` changes after completed requests. Add narrow **authenticated, on-demand, privacy-safe** hooks that correlate *the exact provider request*, metadata-change category and actual writer/revision if observable. Avoid logging settings values or query.
2. **Explicit provider** and **Search All provider heading** are separate paths. The 266 package direct-provider handoff is a candidate and **not evaluated by this trace**. Capture the first genuine heading tap/activation and opening of the provider's original directory (native/Kodi callback if exposed). A public Python observer alone cannot prove native touches.
3. For both providers independently, reproduce a benign settings/history write (must accept completed results) and a genuine configuration change/ABA (must refuse) against a correlated request. No timestamp suppression, endpoint-XML equality shortcut or label-only change.
4. Test regression in an isolated fixture, keep the four physical passes #1 Power, #2 Movies, #3 TV, #5 Downloads and all Cobra unchanged. Package original-key authenticated corrections only after proven positive/negative tests; maintain current physical version and forward-recovery protections.
5. The actual Search-crash #6 remains UNTESTED; do not claim it is fixed from this report or force multiple crashes.

**Verdict:** Concrete failure identified: **two Nixtoons + two Crew successful provider results were rejected because provider settings-file metadata changed**. Exact writer/semantics and failed-heading native dispatch still missing. Next diagnostic must instrument *these* remaining boundaries only; do not ask for phone version or reinstall an APK to restate already-proven counts.
