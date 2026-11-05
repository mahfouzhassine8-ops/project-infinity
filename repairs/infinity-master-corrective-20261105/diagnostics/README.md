# One read-only Search/Favorites diagnostic script

[infinity_search_state_probe.py](infinity_search_state_probe.py) extends the previously delivered standalone probe; it is outside the APK overlay and has not been installed or executed on the Fold. SHA256 `5bdf6d38b31446d9c48dfc6a24f367d1bfc8e9d2e1de077708dc32b3cd9ca503`.

No mode argument retains the original60-second Search sampler. Its original sampling, file reading, privacy comparisons, provider identity and report-writing functions remain unchanged, verified by AST comparison with99bd0cdc. It never invokes providers or changes Search decisions.

The explicit `favorites` argument takes one read-only snapshot:

- Active-profile and system `favourites.xml` readability/structural counts, without titles, artwork, actions, URLs or paths. It does not validate or execute saved commands and scans no other profiles, provider collections or backups.
- Existing `Files.GetDirectory(favourites://)` count with one returned item, then `Favourites.GetFavourites` only if the directory count is available and bounded. The latter API has **no supported limits argument**, which is respected. Native JSON/API work may allocate or block before Python can cap a response; no force interruption is attempted.
- Existing Favorites-window/container count and parent-row state only when Favorites is active and no modal owns the UI. Unknown/inactive/modal state is explicit, not silently treated as an empty collection.
- Profile-change flag and ambiguous comparisons such as file entries with an empty API, differing API/directory counts, or nonempty API with a parent-only active container. These observations do not prove data loss or identify locks/loading/profile/filtering as a cause.

The diagnostic never adds/removes/executes Favorites, reloads a collection, changes locks or settings, invokes a provider, navigates the UI, requests storage permissions or touches playback/shutdown. The only explicit write is one **new** mode0600 report in `special://temp`, using the existing exclusive writer. Existing user files cannot be overwritten. The new report contains counts/status, not raw replies or errors. Kodi/provider logs outside this script are not changed and may have their own logging policy.

## Existing authorized launch route only

When an already-authorized Kodi RunScript/console/control route exists and the file is readable by Kodi:

```text
RunScript("/already-readable/path/infinity_search_state_probe.py",favorites)
```

The path is a placeholder, not a claimed Android location. Open the native Favorites browser normally before observation when testing presentation. A remaining console/modal causes UI sampling to be skipped; the script does not close it or add a delay. Retrieve the named `Infinity-Search-State-<UTC>-<suffix>.json` report from `special://temp` through an existing authorized file/diagnostic route and keep it private.

No connected authorized launch route/device is currently exposed. Do not install an add-on, enable network control/unknown sources, change Favorites/keymaps, bypass module authentication or alter an APK just to run this script. Execution on the frozen app remains pending; script delivery is not a deployment claim.

Eleven focused host checks pass cumulatively, including actual RPC/UI adapter behavior, entity/encoding/size limits, symlinks, profile changes, empty/malformed distinctions, no writes or provider actions, no private data and source preservation. [Initial10](../results/FAVORITES-PROBE.txt), [final UI/modal check](../results/FAVORITES-UI-READER-FINAL.txt). No real user collection was inspected, so the phone's missing-items cause is still unconfirmed.
