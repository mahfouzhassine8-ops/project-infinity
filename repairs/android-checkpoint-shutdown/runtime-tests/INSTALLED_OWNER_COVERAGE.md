# Observed add-on owner coverage

This is a bounded source/evidence audit, not a complete installed-add-on inventory or a persistence certificate.

## Evidence and limits

- Inspected `Infinity-Diagnostics-20261007-230918.zip`, SHA-256 `5a861e65f4a6297e30aab54557f5bc6644b90cd7d5017b6ec4c7d3ae6b2c26ca` (146,604 bytes).
- The native trace contains 34 `services.stop_one` begin/end pairs with add-on IDs and invocation handles. `xbmc/addons/Service.cpp` populates this service map after `ExecuteAsync` returns a valid handle. These are **historical launched service invocations**, not proof that all 34 remained live at Close.
- `plugin.video.umbrella` additionally appears in three `directory.result_wait_cancelled` events, with invocation handles 35, 36 and 37. Cancellation of a directory result does not acknowledge the provider's persistent state.
- The inspected trace records no exact installed add-on versions, executed script paths, source/dependency hashes, dirty-state manifests, transaction outcomes, or add-on persistence acknowledgments. Invocation handles are local evidence labels, not stable owner identities.
- Neither a returned Stop call, a completed interpreter, a missing thread nor a cancelled directory result proves persistence. An add-on ID is not a code contract.
- The second requested archive, `Infinity-Diagnostics-20261007-224919.zip`, was not available as local bytes during this audit and contributes no findings here.
- Raw diagnostic contents, account data and private device paths were not copied into this repository.

## Observed services and source availability

“Source missing” means exact installed source was not found in the audited repository add-on trees or parent APK embedded add-ons. It does not assert what the add-on does, whether it was dirty, or whether it is safe to discard.

| Add-on ID | Available source / persistence coverage |
| --- | --- |
| `context.seren` | Source missing; unresolved writer contract. |
| `plugin.program.autowidget` | Source missing; unresolved writer contract. |
| `plugin.video.jetproxy` | Source missing; unresolved writer contract. |
| `plugin.video.otaku` | Source missing; unresolved writer contract. |
| `plugin.video.pov` | Source missing; unresolved writer contract. |
| `plugin.video.redlight` | Source missing; unresolved writer contract. |
| `plugin.video.seren` | Source missing; unresolved writer contract. |
| `plugin.video.thecrew` | Source missing; unresolved writer contract. |
| `plugin.video.themoviedb.helper` | Source missing; unresolved writer contract. |
| `plugin.video.tidb` | Source missing; unresolved writer contract. |
| `plugin.video.tmdb.bingie.helper` | Source missing; unresolved writer contract. |
| `plugin.video.tmdbmovies` | Source missing; unresolved writer contract. |
| `plugin.video.umbrella` | Source missing; service and directory invocations observed; unresolved writer contract. |
| `plugin.video.youtube` | Source missing; unresolved writer contract. |
| `plugin.video.youtubek` | Source missing; unresolved writer contract. |
| `repository.zeus768` | Source missing; a service invocation was observed despite the repository-prefixed ID. |
| `screensaver.atv4` | Source missing; a service invocation was observed despite the screensaver-prefixed ID. |
| `script.bingie.widgets` | Source missing; unresolved writer contract. |
| `script.common.plugin.cache` | Source missing; its name alone does not establish reconstructible-cache semantics. |
| `script.cu.lrclyrics` | Source missing; unresolved writer contract. |
| `script.extendedinfo` | Source missing; unresolved writer contract. |
| `script.infinity.commandcenter` | Exact parent embedded controller source available; runtime overlay has an explicit participant. This historical trace does not prove that installed code matched it. |
| `script.kodihealthcenter` | Source missing; unresolved writer contract. |
| `script.module.acctmgr` | Source missing; unresolved writer contract. |
| `script.module.slyguy` | Source missing; unresolved writer contract. |
| `script.module.viperscrapers` | Source missing; unresolved writer contract. |
| `script.skin.helper.service` | Source missing; unresolved writer contract. |
| `script.trakt` | Source missing; unresolved writer contract, including any pending remote synchronization semantics. |
| `script.xenon.casthelper` | Source missing; unresolved writer contract. |
| `service.infinity.chooser.weather.snapshot` | Exact parent shell-generated source available; bounded cache classification candidate described below. No production exemption added by this audit. |
| `service.infinity.compat` | Exact parent source available; runtime explicit participant covers its critical history, marker and changed legacy files. Installed identity must still match the full source contract. |
| `service.infinity.refresh` | Exact parent source available; audited derived policy cache contract depends on native add-on settings persistence and exact executed code identity. |
| `service.kodi.favourites.sync` | Source missing; unresolved writer contract. Native favourites persistence does not establish this service's private synchronization state. |
| `service.multistaller` | Source missing; unresolved writer contract. |

There are 30 observed services whose exact installed source is missing, three observed services with existing runtime contracts, and one generated weather-service candidate. The diagnostics alone do not prove any installed hash or enable an exemption.

The parent APK also contains source for `service.xbmc.versioncheck`, `script.infinity.audiopolicy`, `script.infinity.live`, and Python modules. They do not appear in the 34 service-owner observations above. Packaged availability must not be substituted for observed installed identity or invocation history. In particular, the audio-policy script writes authoritative configuration directly and is not a nonpersistent service.

## Generated chooser weather service

The exact parent shell source `tools/android/packaging/xbmc/src/InfinityChooserWeather.java.in` generates `service.infinity.chooser.weather.snapshot/weather_snapshot.py` into the extracted APK add-on cache. Its generated bytes match repository `repairs/chooser-weather-snapshot-2103302/weather_snapshot.py` exactly:

`04e64e73d4b0377f9ea0c9acbb4627ede19c66786c4e4166f8aaa196454a5634`

The generated manifest declares version `1.0.0` and entry point `weather_snapshot.py`. That is a parent-source fact; the diagnostic trace does not independently report either value.

The reviewed producer reads already-fetched Kodi weather labels, serializes an optional chooser snapshot, and replaces a temporary cache file. It neither launches a provider nor writes provider settings, add-on settings, native databases, watched state, or user choices. File data is fsynced before replacement; the snapshot is reconstructible and the chooser already tolerates unavailable/stale weather. Loss of an unfinished optional snapshot therefore need not block persistence of required user state.

A safe bounded classification would require all of the following:

1. Capture the exact executed producer hash and canonical generated-cache root at launch; revalidate the contract at checkpoint.
2. Validate the effective `snapshot_config.json` destination as the one expected chooser-cache file. The source obtains its write target from this separate mutable configuration, so hashing the Python file alone does not constrain its write scope.
3. Establish that the configuration used by the running invocation matched that validated destination. A later reread of a changed configuration is insufficient evidence of what was originally loaded.
4. Limit the contract to this source and target, leaving user replacements, altered code/configuration, and unknown scripts unresolved.

No production source was changed to add this classification. The earlier service contracts and native lifetime ledger remain unchanged by this audit.

## Required next evidence

Obtain a source-only snapshot of the actual installed add-ons: each observed add-on's `addon.xml`, exact invoked entry point, imported local/dependency source, and byte hashes. Include dependency manifests sufficient to identify resolved module versions. Do not include account settings, tokens, private media data, or unrelated user databases.

That source snapshot enables a per-owner audit of raw file writes, SQLite connections/transactions, delayed tasks, process-exit hooks and required remote updates. Owners then need a checked persistence participant or a demonstrated exact-code contract limited to native-wrapped writes or disposable derived caches. Historical completed invocations remain accounted for until that contract is established.

Missing evidence must produce named unresolved owners and a failed checkpoint. It must not automatically disable add-ons, delete data, silently omit owners, or turn thread disappearance into permission to terminate.
