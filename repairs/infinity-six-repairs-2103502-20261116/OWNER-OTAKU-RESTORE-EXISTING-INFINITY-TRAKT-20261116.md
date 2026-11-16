# OWNER CORRECTION — Restore EXISTING Infinity Trakt on Otaku, don't rebuild tracking

**Owner's direct question/expectation, November 16, 2026:** Why isn't the existing `Infinity Trakt` context-menu action simply restored on Otaku? **Restore that existing working interface**, including `Add to Watchlist`, within already-authorized Repair #2. Do not defer the entire UI wiring correction merely because the exact failing Otaku item's identity or selected-context diagnostics are unavailable.

**Verified source facts from retained signed502-derived baseline:**
- `script.infinity.commandcenter/infinity_trakt.py` already defines `ACTIONS`, `show()`, and `main(item=None)`. Its `choose('Infinity Trakt', ...)` already includes **Add to Watchlist**, and `show()` routes the verified selected identity through the existing Watched Bridge/controller and persistent store. `main()` already emits a safe explanation if a row lacks supported verified IDs. **Do not create a new Trakt menu, store, bridge, provider adapter or replacement tracking engine.**
- `plugin.py::show_item_menu` and `_menu_rows` provide established saved-title context actions; the first-party native selected-item path/metadata bridge must provide the actual selected `CFileItem`/Kodi ListItem to `infinity_trakt.main` for native result contexts.
- `infinity_search.py` passes native provider row `mediatype`, `uniqueid`, selected route and art through to Kodi ListItem, with existing provider-native search preserved. This does not prove the current Otaku result has valid unique IDs or that the native popup is wired to this exact ListItem. **The selected context route is the thing to inspect and reconnect.**

## Two separate requirements — do not conflate

**A. Restore visible existing menu action (independent of a specific user's failed title).** In Otaku results under the existing Infinity Search/normal title context, verify the existing native `Infinity Trakt` entry appears where it does for working TV Shows / other compatible providers, preserving all other context-menu entries/order/long-press semantics. Trace first-party menu eligibility/registration, selected-item copy and dispatcher; correct the *smallest proven first-party mismatch* and reuse existing `RunScript`/native-selected-item handoff. A missing owner screenshot/ID may leave incident attribution open, but **must not block implementing and testing a demonstrated missing menu-registration path**. Do not patch Otaku internals.

**B. Save only real verified media identity.** Selecting `Infinity Trakt → Add to Watchlist` must use the selected Otaku title's genuine trusted typed movie/show/season/episode ID and the original existing Watched Bridge / Infinity TV Watchlist state. If an actual selected row lacks sufficient verified IDs, keep the menu and existing safe explanatory behavior; **no guessed ID from title/year, no arbitrary different anime, no false success receipt, no silent data mutation**. If genuine IDs exist but are dropped/incorrectly classified by Infinity's UI/selection handoff, fix that minimal universal typed-identity bridge; do not loosen validation or invent a provider-specific engine.

## Acceptance
1. Reproduce the working `TV Shows title → long press → Infinity Trakt → Add to Watchlist → Infinity TV Watchlist` control, and compare Otaku using verified synthetic/provider-native rows without private user data.
2. On a valid-ID Otaku result, existing native context displays the SAME `Infinity Trakt` action; selecting existing `Add to Watchlist` saves correct typed identity in appropriate Infinity TV Watchlist; no progress/history is fabricated.
3. On an unknown-ID Otaku result, native context action and safe no-write explanation remain truthful; no fabricated identity or crash. No provider source or different menus changed.
4. Preserve signed502, all other provider search/results, saved history, Cobra and every out-of-scope control. Astra source/diff review and focused positive/negative tests; integrate with the SAME full-six-repair combined QA APK after all required work is engineering-complete.

**This is not a claim of an installed fix or proof the owner's particular item lacked IDs. It is a concrete existing-feature restoration instruction within Repair #2.**
