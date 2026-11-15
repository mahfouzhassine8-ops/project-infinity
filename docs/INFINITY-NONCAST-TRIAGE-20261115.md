# Infinity non-Cast triage — November 15, 2026

**Source-only investigation handoff. No production edits, APK build, reset, acceptance claim or user-data mutation is authorized by this document.**

## Owner decision / priorities

Cast has **not** been properly accepted or rejected on the user's TV. The Cast selector also omitted expected devices. **Defer both Cast playback and Cast discovery.** Preserve the current signed Cast candidate and its forward recovery; do not label Cast working, failed or fixed based on an incomplete test.

Use three **separate** investigation tracks, with the current active focus in this order:
1. Protect & investigate **Movies → Continue Playing** saved entries.
2. Fix **shutdown persistence checkpoint** after tracing exact owners.
3. Restore **Infinity Search → existing Infinity Trakt / Add to Watchlist** option universally.

No speculative combined repair. Existing working Kodi, Cobra, search-provider engines, Trakt state, playback tracking, Cast, UI/skin and profiles stay unchanged. No install/uninstall, data clear, forced shutdown or migration.

## A — Movies Continue Playing (MOVIE-CONTINUE-04): protect state first

Owner screenshot, November 15: existing **Saved destination unavailable — open with** safety dialog offers **Seren**. The owner reports missing saved movie cards in Movies Continue Playing. **The screenshot proves the recovery safeguard appeared, not that saved progress/history was erased.**

Verified source seams on existing branches:
- `resume_hub.py`: `CONTINUE_FILE = "continue-watching.json"`; `load()` reads the canonical JSON; `load_view()` uses a checked read-only cache; `_entries_projection(..., media="movie", bucket="items")` filters by `media`, `resume_visible()`/ `resume_hidden`, and identity-grouping. `save()` can atomically rewrite the store and invalidates display cache.
- `plugin.py`: `navigation_target()` / `saved-recovery` can present a verified alternate provider when a saved destination has expired; source recovery must not replace, remove or invent historical progress.

**Already uploaded diagnostics checked read-only:** `Infinity-Diagnostics-20261114-201813.zip` and `Infinity-Diagnostics-20261114-214040.zip`, which predate the November 15 screenshot. Neither ZIP contains the canonical `continue-watching.json` itself. The newer ZIP's `resume/timing-current.jsonl` contains two explicit **TV** requests (n23, n24; 3 and 5 directory rows) but **no explicit movie request**. These timings therefore **cannot prove a movie-record deletion, a movie display defect, or a movie recovery fix**. They also do not establish the current user's active profile.

**Next evidence gate:** using the existing user data in a private/consented environment and **read only**, count valid movie records in `items`, movie entries after `resume_visible`, hidden/completed flags, profile and revision, and items after grouping; contrast with Home and Movies Continue UI. Reconcile exact source/recovery ID and known provider adapter availability, without raw URLs/titles in the public repo. If the canonical state is unavailable, state **BLOCKED: saved state not accessible**. Do not guess deletion.

**Never:** clear data, toggle hidden flags en masse, write `continue-watching.json`, invent resume history, substitute provider source based on title, perform migration or dismiss checkpoint errors.

## B — Shutdown (SHUTDOWN-01): after state is protected

The existing November 14 21:40 ZIP has checkpoint result `CHECKPOINT_FAILED` around 25.2 seconds, `native_admission: checkpoint_deadline_exceeded; owner proof incomplete`. The report identifies Playlist Browser `buffer_flush_failed` / `ValueError`, TMDb Helper `ItemQueries.db` pending SQLite transactions in `service.py` / `script.py`, and owner-proof discrepancies. Eleven owner blockers are **not** eleven proven live writers; process death was not confirmed by these diagnostics.

Trace the actual writer/retirement proof and transaction lifecycle. Verify valid commit or rollback and safe release. Never bypass essential durability, pretend Exit passed, or alter Cast/Watchlist to fix shutdown. Run focused persistence tests and separate actual Android process-death verification **only after** a justified source-only patch.

## C — Infinity Search / Watchlist (SEARCH-WATCHLIST-02): distinct later fix

Otaku search returns a title and metadata. Its aggregate Search context menu showed **Open in Otaku** / **Information**, not the expected **Infinity Trakt** action. Existing first-party Command Center `show_item_menu()` / `_menu_rows()` already support Add to Watchlist; the missing seam may be aggregation context visibility, validated identity, or menu routing, **not confirmed provider failure**. Trace exact selected ListItem, verified IDs, and context selection path. A recognized TV show must reach the existing Watchlist workflow without provider-specific search changes or fake playback. Use the same universal contract for movie results.

## Deliverables / status protocol

- One root-cause report per issue, supporting lines/log proof and clear uncertainties.
- Safeguard and preserve original movie state before considering any write.
- Minimal, independently approved defect-only patch and tests **per issue**. Reuse existing implementations, no new search engine or second playback tracker.
- Keep Cast deferred and Cobra locked.
- A signed candidate requires causal reproduction, scoped regression verification, preservation receipt, original signing continuity, and explicit later release action—not this handoff.

**No new phone test requested by this analysis.** Existing screenshots and November 14 diagnostic archives have been considered within their evidentiary limits.
