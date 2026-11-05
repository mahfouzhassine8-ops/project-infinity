# Search All rejection versus successful direct-provider results

New evidence is the user's physical Fold report: Crew and Nixtoons show State changed under Search All, while selecting their provider headings opens real provider results. This establishes reported working search capability; it does not establish the first collected RPC's original status or precise changed field. The supplied recording's bytes/file reference are not exposed in this executor, so **no video playback inspection is claimed**. The phone's installed version remains unverified; the source candidate is not installed there.

## Exact source paths

`search_all → _search_results → _bounded_results → _provider_result` collects through the existing request-owned `Files.GetDirectory` lease. The route is verified before/after collection. `_provider_result` compares before/after state signatures; if different, it replaces the original answer with `{}` and returns `state_changed` plus the original provider URI.

`_publish_result` then creates a provider heading pointing to that URI and labels it State changed; search again. Because status is not completed, it publishes no collected child rows. The heading remains a folder and can open the provider's normal GUI search. That path executes the existing provider interface through Kodi; it does not run aggregate collection/result publication. The host case proves the heading retains the **same exact generated query route**, with one original collection and no automatic retry.

Selecting a provider **inside the Search form** is a different path: `search_provider → _search_results`, still using the common aggregate validator. Do not conflate that option with opening a provider heading in the results. The user's description fits the latter path, but the exact recording sequence has not been inspected.

Thus a state rejection is not a finding that a provider cannot search. No compatibility classification, provider adapter, source verification or provider code is changed.

## New bounded diagnostic source

The candidate now emits one existing Kodi-log record only when an aggregate result is rejected:

```text
INFINITY_SEARCH_STATE {"event":"aggregate_result_rejected", ...}
```

It records provider ID, original status, original result count, cache/fresh flag and changed-component names, retaining the original provider route. It never logs the URI, query, result titles, paths, settings values, key names, hashes or request tokens. Components use the same metadata/file reads as the actual validation snapshot; there are no additional reads, XML serialization, provider calls, workers, retries or persistent stores. A trace failure cannot change publication, cancellation or source decisions. Ordinary successful results do not produce diagnostic spam.

This identifies whether an actually completed response with rows was discarded for provider/dependency settings metadata, a profile/source-contract change or a cache revision race. It deliberately calls the field `provider_settings_metadata`, not meaningful configuration: a filesystem stamp alone cannot classify the writer or changed values. Existing host probes can sample field categories, but cannot recover a complete mutation history or attribute writes to a request.

Ten new publication/trace cases pass cumulatively; the15 affected source/guard cases remain passing. The two required settings/Nixtoons acceptance cases are explicitly rerun and **still FAIL**. This diagnostic is not called the settings repair.

## Proven safety boundary and Crew independence

Native `CAddon::SaveSettings` notifies `XBPython::OnSettingsChanged(ID)` only after successful persistence, and suppresses those notifications during checkpoint persistence. `XBPython` delivers only to monitors whose ID equals the provider. `xbmc.Monitor` gets that ID from its own invoker's LanguageHook; Python exposes no provider-ID subscription. Command Center cannot safely turn its monitor into a complete provider-write journal. Do not spoof the provider identity or substitute callback completion for durability.

Crew also has a separate direct-file repair path (`settings_repair`), including conditional token/default restoration, normalization and orphan removal. These writes need not pass through the native settings notification at all. Its TV search history itself uses SQLite and is not in the state signature. Its conditional Orion initialization writes metadata only when that integration is present. These are independently verified source paths; no current phone writer/account/integration state is inferred.

Ignoring all stamps, comparing final semantic XML only, waiting/retrying or exempting every settings callback would weaken an existing meaningful-change check. A temporary configuration change followed by restoration can leave the same endpoint values; the current stamp guard still rejects it. No such exemption, provider patch, duplicate execution, identity spoofing or persistence change is implemented.

Remaining Search gate: obtain the actual request-local reason/native outcome and a proven way to distinguish permitted bookkeeping from meaningful/intervening changes before accepting those results. Existing callbacks alone are insufficient. A native mutation-observation contract would be a separately reviewed protected change, **not** part of the two-file touch proposal or the blocked settings-retirement work. Crew's actual rejection reason remains unconfirmed. The shared state predicate and Nixtoons reference self-invalidation are confirmed; the safe settings repair remains incomplete.
