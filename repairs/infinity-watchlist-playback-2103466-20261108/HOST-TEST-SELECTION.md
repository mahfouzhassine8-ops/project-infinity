# Selected feature host cases — recorded before execution

Authorized by `OWNER-PHASE-B-AUTHORIZATION.md`, with Codex's independent
acceptance of the exact Watchlist projection contract. Initial run selects only
`test_watchlist_progress.py` / `WatchlistProgress` methods:

- `test_movie_fresh_position_and_original_saved_snapshot_unchanged`
- `test_exact_episode_never_selects_newer_other_episode_or_season`
- `test_duplicate_agreeing_ids_choose_newest_persisted_revision`
- `test_transitive_conflicting_ids_quarantine_entire_component`
- `test_similar_titles_and_namespaces_do_not_match`
- `test_newest_hidden_alias_does_not_reveal_old_visible_alias`
- `test_completed_occurrence_cannot_resume_but_new_replay_can`
- `test_manual_watched_hides_older_progress`
- `test_invalid_nonfinite_and_completed_offsets_are_rejected`
- `test_reload_retains_exact_position_and_unknown_extension`
- `test_show_and_season_are_never_playable_progress_selectors`
- `test_existing_exact_provider_proof_can_join_raw_and_show_episode_scopes`
- `test_list_item_watchlist_projection_keeps_original_route_and_key`

These exercise actual overlay `resume_hub.py` and `plugin._list_item` with
controlled Kodi/persistence boundaries. Scope is read-only exact saved progress
and rendering, not native origin, actual AV start, catalogue admission, Android,
build, installation, lifecycle or shutdown acceptance. Those remain NOT RUN.
The optional helper/runtime enrichment is not bound or represented as complete.

Command: `python test_watchlist_progress.py` from this task directory.

Second selected run: add these actual existing service writer cases to verify
the explicitly preserved completion/partial boundary and duplicate semantics:

- `test_natural_end_completion_retains_short_and_unknown_duration_semantics`
- `test_95_percent_completion_is_independent_of_partial_duration_gate`
- `test_new_partial_minimum_and_released_clock_do_not_create_false_progress`

Run the same focused module (16 cases total) because the new boundary cases use
the shared fixture and actual overlay hub. No application tests are selected.

The 16-case run exposed a fixture error in the partial writer case: it expected
an arbitrary fixture key rather than the production identity-derived progress
key. Correct only that fixture key and rerun the same selected 16 cases. Preserve
the first run's error in the result receipt; this is not a production failure.

Final preservation correction: restrict the projection change to playable
Watchlist movies/episodes, retaining baseline show/season popup/Information
behavior. Add `test_folder_popup_rows_remain_exact_baseline_behavior`, which
compares the actual baseline and overlay menu functions. This production
condition correction justifies one final selected module run (17 cases).
