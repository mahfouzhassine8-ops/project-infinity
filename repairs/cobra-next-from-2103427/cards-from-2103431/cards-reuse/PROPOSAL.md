# Bounded retained Cards browser proposal

This proposal, scope and exact source budget were saved before implementing
`patch.py`. Parent/root approved this bounded source composition. The patch is
not compiled, executed or runtime-verified by this subtask. Parent owns the new
`CobraCardsReuse` runtime and its focused tests separately.

The sole cache candidate is the currently installed Cards Grid and adapter,
owned weakly by the current UI. Eligibility requires Cards, non-Pro, channel
route, the same attached shell/Grid/adapter, and an inactive directory. Groups,
sources and a shown directory continue through the original renderer and its
fresh counts. Existing selection, scroll and focus stay on the retained Grid.
The helper must perform current metadata/style work and rebind current visible
rows through actual adapter `getView`; EPG publications/ticker remain original.
A true `tryReuse` result therefore returns from Render without another layout
hook. No control, playback, source-authority or persistence behaviour changes.

## Exact Activity hooks

| Method/site | New helper call | Placement |
|---|---|---|
| `cobraRenderGuideBrowser` | `tryReuse(Activity)` | Entry, before original body; true returns, false resumes exact original body |
| Same method | `installed(Activity)` | Immediately after each of its two existing `CobraCardsLayout.afterRender` calls; Render only |
| `cobraRestyleGuide` | `beforeShell(Activity)` | Immediately after its existing `CobraCardsLayout.beforeShell`; leave its other hooks untouched |
| `applyLoadResult` | `inventory(Activity)` | Immediately before actual owned-list clear; owner `p0`, list `v0` |
| `restoreCobraLibraryCache` | `inventory(Activity)` | Immediately before successful cache publication clear; owner `v0`, list `v2`; failed cache reads do not invalidate |
| `lambda$confirmRemoveSource$96$...` | `inventory(Activity)` | Immediately before actual clear; owner `p0`, list `p1`; not the whole callback entry |
| `lambda$loadAllEnabledSources$54$...` | `inventory(Activity)` | Immediately before actual publication clear; owner `v0`, list `v7` |
| `persistSources` | `sources(Activity)` | Entry |
| `toggleFavorite` | `favorites(Activity)` | Entry |
| `reloadProfileCollections` | `collections(Activity)` | Entry |
| `hideCobraChannel` | `hidden(Activity)` | Entry |
| Custom-group lambda 74 | `custom(Activity)` | Entry before existing put/remove semantics |
| `addRecent` | `recent(Activity,Object)` | Entry using original `{p0 .. p1}` arguments |

The source-removal spelling is **confirmRemoveSource**, not showSourceActions.
All ten mutator method bodies match original signed-431 canonical source before
these additions. Render/Restyle pins refer to the staged Cards implementation.
The input contains 1,802 methods; only the twelve selected method bodies may
change. No field, method set, class metadata or register-count changes are
allowed. All exact preimages and owner/list aliases are in `SOURCE-BUDGET.json`.

## Complete freshness boundary

Inventory/source publication and hidden/custom/collection mutation revisions
are synchronous Cobra-owned observations. Hooks allocate no state unless a
current UI-owned cache record already exists. `recent` affects RECENT only and
may ignore a channel already first when the list has at most forty entries;
it must not invalidate ALL membership for an ordinary playback recent update.
Shown directory/group/source routes always fall through for fresh counts.

A reuse attempt also checks fresh active-profile ID and raw `profiles` and
`source_meta` values; raw tokens validate render ownership and do not replace
original policy decisions. Same-profile adult-policy/source edits therefore
cannot hide behind an unchanged profile ID or delayed preference callback.
Current effective visual-theme identity and palette are required: the renderer
object itself survives static active-theme publication. UI contract,
configuration/density/font/geometry changes reject reuse. A detached or replaced
UI record is invalid; listeners, if used by the helper, must be weakly owned and
unregistered without adding shutdown responsibilities.

This proposal introduces no preference/file/worker write, policy cache, TTL,
20k-channel hash, new worker, cross-mode redesign or protected-source edit.
Focused actual-source preservation, stale-publication/favorites/recents/hidden/
custom/profile/theme/geometry and visible-rebind tests belong to the parent’s
next verification step; no PASS is claimed here.
