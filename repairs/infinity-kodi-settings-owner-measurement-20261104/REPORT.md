# Infinity Kodi settings-owner memory measurement — 2026-11-04

One bounded, host-only measurement pass is complete. It demonstrates two distinct mechanisms: retained settings owners accumulate when successive changed owners are created for the same settings path, and clean XML serialization can produce a substantial temporary allocation peak. It does **not** identify the historical crashing add-on or establish which mechanism caused the Galaxy Fold's Scudo failure.

No production repair was made. No Kodi/Android engine or APK was rebuilt, installed, signed, released or locked. Infinity Preview 2103451, Cobra, user data and all recovery checkpoints remain unchanged.

## Scope and evidence binding

- Starting repository checkpoint: `8b25b7d425e644d5af559580665d2499c61814b9`.
- Isolated diagnostic branch: `work/infinity-kodi-2103452-settings-owner-diagnostic-20261104`.
- Protected baseline remains signed 2103451; 2103452 remains an unapproved testing build.
- The measured registry and serialization source files are identical in the authenticated 451 and 452 source maps. This path is not an identified 452-only regression.
- The existing extracted-function host test infrastructure was reused. The measured bodies include the owner registry helpers, `CSettingsManager::Save`, `CSettingsBase::SaveValuesToXml`, `CAddonSettings::Save` and the settings XML serializer. The serializer entry was wrapped with counters/timing, without an additional serialization call.
- TinyXML is the exact existing build pin, `tinyxml-2.6.2_2`, verified against its original SHA-512. No application dependency changed.
- All 9,411 restored native source files still match the preserved 452 source map. The primary branch, tracked files and pre-existing untracked files remain unchanged.

See [SOURCE-BINDING.json](evidence/SOURCE-BINDING.json), [DEPENDENCY.json](evidence/DEPENDENCY.json), [PRESERVATION.json](evidence/PRESERVATION.json) and [FINAL-SOURCE-PRESERVATION.json](evidence/FINAL-SOURCE-PRESERVATION.json).

## What was actually measured

The selected plan was saved before execution. A single pass ran 24 fresh host processes: four scenarios, three paired observer-off/on repetitions each, with counterbalanced order. The pass had a 120-second overall bound and a 30-second per-process bound. All 24 planned cells completed; none was retried. These are test-execution bounds, not production timeouts or memory limits.

The host uses synthetic settings-manager/tree peers and synthetic ASCII values with the real pinned TinyXML pipeline. It does not construct all native Kodi setting classes, execute providers, invoke derived add-on serializer overrides, or reproduce Android Scudo allocation behavior. The ordinary file-save success boundary is supplied by the fixture; actual filesystem persistence and final checkpoint durability were **not** tested or claimed.

One synthetic add-on, `diagnostic.synthetic.settings`, owns every fixture. Numeric owner IDs distinguish its settings instances. No real add-on setting, profile, credential, media path or user file was accessed. Results contain only numbers, booleans and allowlisted synthetic identifiers. XML values are never emitted. The synthetic path used as the registry key is never opened or logged.

Memory snapshots and output occur after settings and registry locks are released. Counters collect existing serialization results; they do not request more XML. There are no background workers, extra serializers, cache purges or shutdown calls. Fixture process destruction is not a Kodi shutdown test.

## Retention and temporary allocation results

All small cases use 16 synthetic settings of 4,096 bytes each: 64 KiB of value payload per owner. The large case uses one 4 MiB value. Final counts are recorded before process exit. The table uses the first observer-on repetition for sizes/counts; these functional values agree across the paired repetitions.

| Scenario | Operations | Core XML serializations | Live / dirty owners | Destroyed owners | Retained baseline XML | Final C++ live bytes | Peak C++ live bytes | Final process RSS |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| Fresh clean owners | 128 loads | 128 | 0 / 0 | 128 | 66,233 B | 66,602 B | 403,995 B | 2,204–2,208 KiB |
| One reused changed owner | 128 edits, plus initial load | 129 | 1 / 1 | 0 | 66,233 B | 200,764 B | 536,735 B | 2,460 KiB |
| Fresh changed owners, same path | 128 load/edit/save operations | 256 | 128 / 128 | 0 | 8,477,824 B | 17,245,942 B | 17,581,913 B | 19,260–19,264 KiB |
| Fresh large clean owners | 4 loads | 4 | 0 / 0 | 4 | 4,194,380 B | 4,194,749 B | 29,361,925 B | 14,272 KiB |

“C++ live bytes” counts outstanding requested sizes through the host's overridden `new`/`delete`. It excludes allocation headers and direct C allocator traffic; it is neither complete Kodi native memory nor process RSS. Process figures come separately from `/proc/self/smaps_rollup`. Absolute host memory includes fixture/accounting overhead and is not an Android estimate.

**Accumulated ownership:** with fresh changed owners, live C++ bytes rose from 200,764 at operation 1 to 4,361,398 at 32, 8,656,246 at 64 and 17,245,942 at 128. At the last point, the registry held 128 live dirty trees and 128 baseline copies, although the pending-save map held only **one** entry for that path. Its pending XML was another 66,233 bytes; fixture value capacity was 8,388,608 bytes. This is retained ownership, not just a temporary serializer peak.

**Bounded reuse:** the same 128 edits through one owner retained one tree, one baseline and one pending-save entry. Its live memory stayed at 200,764 bytes after the first operation. This isolates owner creation/retention from the number of edits alone.

**Clean reads:** clean owners were destroyed after use. Creation of the next owner pruned the previous expired registry entry. One final expired entry and its baseline remained: 127 entries were pruned in the 128-load case. Thus these reads showed serialization work and one lingering baseline, but not accumulating live settings trees. “Destroyed” is the measured owner-retirement count here; no checkpoint-retirement procedure was invoked.

**Temporary XML peak:** the 4 MiB clean case reached 29,361,925 requested C++ bytes (about 28 MiB), then returned to about 4 MiB after each load. The peak did not grow across the four loads. The pipeline materializes XML, string output, a parsed document and canonical checkpoint bytes; those overlapping allocations are distinct from the retained final baseline. Final RSS stayed above live C++ bytes because process memory includes allocator arenas and other mappings. No trimming or cache deletion was performed. The experiment does not identify which individual allocation was largest or reproduce Scudo's failed mapping.

Raw `max_rss_kib` values are retained for transparency but are not used to calculate operation peaks: `getrusage` high-water values can carry process-launch history and differ from current `smaps_rollup` RSS. The reported allocation peak comes from the common C++ counter.

## Serialization size, frequency and duration

The counter measures existing calls to `CSettingsValueXmlSerializer::SerializeValues`, the compact serialization entry in the supplied crash stack. It does not count every `TiXmlPrinter` traversal; existing canonical checkpoint printing remains present and unaltered.

| Scenario | Compact bytes per call | Total compact bytes | Median cumulative core serialization | Median operation-loop duration |
|---|---:|---:|---:|---:|
| Fresh clean | 66,151 | 8,467,328 | 26.25 ms | 138.50 ms |
| Reused changed | 66,151 | 8,533,479 | 21.68 ms | 141.59 ms |
| Fresh changed | 66,151 | 16,934,656 | 48.96 ms | 288.19 ms |
| Large clean | 4,194,373 | 16,777,492 | 61.05 ms | 206.69 ms |

Timings are medians of the three observer-on runs. For the reused-owner case, core counts/timing include the initial load; the operation loop excludes that setup. Counts establish one core serialization per fixture load and one per supplied save. They do not measure settings-call frequency on the Fold, Home navigation latency or provider latency. The raw summary's `serializations_per_second_host_median` is throughput during the measured serializer time only, not an observed application arrival rate.

## Observer overhead and deployment limit

The numeric observer uses a fixed **20,480-byte** buffer. No records were dropped. Enabling it added **zero heap allocations** in every pair, and serialization counts, output byte counts and final retention were unchanged.

Median observer-on loop differences were +2.63% (clean), +3.07% (reused changed), -1.18% (fresh changed) and -1.30% (large clean). Individual pairs ranged from -12.32% to +6.95%; negative differences are measurement noise, not a claimed optimization. Three pairs are insufficient for a strict overhead upper bound.

Both arms include the common host allocation counters and final memory snapshots. Therefore the pairing measures **incremental numeric-observer overhead**, not the total cost of all diagnostic instrumentation versus an untouched Kodi process. This host-only allocation override is not proposed for Android deployment. No compatible Android device was connected and no device instrumentation was deployed. Android overhead and the historical owner attribution remain unverified.

## Source mechanism and smallest supported next action

In `xbmc/addons/Addon.cpp`:

1. `TrackCreatedAddonTree` removes expired clean entries, then registers a new owner.
2. `TrackLoadedAddonTree` serializes its loaded values and retains canonical baseline bytes.
3. `MarkAddonSettingsManagerDirty` pins a changed owner through a strong `dirtyOwner` reference.
4. `ConfirmAddonSave` updates the baseline and committed generation after the ordinary successful-save boundary, but leaves that strong reference in place.
5. The final successful checkpoint clears the dirty references and pending-save map. That path was not invoked or changed by this measurement.

The native settings manager does not mark clean initialization dirty; actual changed values are required for the tested accumulation. It is incorrect to label every `getSetting` call a leaking dirty owner.

The smallest evidence-supported repair candidate is **settings-owner retention bookkeeping in this file**, specifically whether a superseded, successfully saved owner can be retired without losing a persistence obligation. It is not a global cache, decoder, allocator or add-on replacement problem established by this evidence.

Before any production correction, prove a retirement rule against committed generations, unsaved/concurrent changes, live external references, failed saves, unknown baselines, conflicting owners, derived serializers and final durable checkpoint receipts. An ordinary successful save does not establish final checkpoint durability. Pending bytes and all unverified obligations must continue to block shutdown appropriately. Unconditional `dirtyOwner.reset()`, dropping baseline comparisons, or merging owners solely because their paths match would be unsafe and is **not** recommended. No such change has been made.

To attribute the actual Fold failure, a separately authorized bounded Android observation would need numeric owner/add-on identifiers, existing serializer size/duration counters, live/dirty/retired counts and process-memory samples at safe boundaries. It must use no values or media paths, no additional serialization, no lock-held logging and no new worker. That deployment is outside this pass and would require a supported device and independently validated overhead; this report does not authorize an APK build.

## Historical Scudo correlation and remaining unknowns

The user supplied the decoded stack from `traces/1-1793753186040.tombstone.pb`, SHA-256 `8b44aa904f8728ca60187e6ee85b34cf76e78dffb81a827bf20b48ac5009df11`. A separate private reader supplied archive/RSS correlation. This executor has not directly opened or decoded the raw archive; the provenance remains explicit.

That evidence places the failed allocation in add-on settings XML serialization during a Python setting request, PID 18358/TID 18679, around 2026-11-04 00:46:24 UTC. The exit record reports RSS 3,240,232 KB. Reported PSS zero is unavailable data, not evidence of zero proportional memory. The 2 MiB tombstone may be truncated; complete memory-map coverage is not available.

Neither the supplied stack nor the retained service records identifies the add-on/settings path, request size, number of retained owners, overall heap ownership or exact producer engine. The installed 452 engine and compatible timestamps are not cryptographic attribution of the historical crash. No evidence here assigns blame to Google Assistant, a decoder or a specific add-on.

The host findings show that retained trees and temporary XML peaks can coexist. They do not explain the entire approximately 3.09 GiB process RSS, reproduce the crash, or establish how often the triggering operations occurred on the device. Existing queue-retirement rows with default zero counts do not prove the global worker pool drained, and no retained Home first-card event closes the separate intermittent-loading question.

The checkpoint-aware Pause/Stop ANR and Continue Playing completion mismatch remain separate previously established repair candidates. Their source, tests and evidence were preserved; neither was retested, merged into this task or changed.

## Reproducibility and saved evidence

- [SELECTED-PASS.json](SELECTED-PASS.json): preselected scenarios and exact bounds.
- [SUMMARY.json](evidence/SUMMARY.json): results and paired overhead.
- [ALL-CELLS.json](evidence/ALL-CELLS.json): all 24 numeric process results, including owner observations.
- [MEASURED-TABLE.json](evidence/MEASURED-TABLE.json): report table inputs.
- [PREPARED.json](evidence/PREPARED.json): compiled host binary and generated C++ hashes.
- `run_measurement.py`, `peers.cpp.in`, `measure.cpp.in`: isolated diagnostic source.

The existing source extractor and the matching restored native source/maps are prerequisites. The existing pinned TinyXML source must be materialized and verified first. `--generate-only` prepares the host fixture; `--execute-prepared` verifies and uses that exact binary without recompiling. A `PASS-STARTED.json` guard refuses to repeat the selected pass. Do not run another pass under this completed authorization.

The Python runner's metadata newline encoding was corrected for saved-script reproducibility. The measured generated C++ and binary hashes did not change; no measurement was repeated. Compilation warnings are retained in `evidence/COMPILE.txt`; this was one host fixture compile, not a native engine build. The earlier 21 focused repair tests were not repeated. No signing, installation, shutdown verification or physical Fold acceptance is claimed.
