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

Latest owner authorization now permits invocation handoff integration and reuses
only existing local Kodi successor proof. Corresponding source has changed, so
the 17 projection cases are selected again to verify their affected functions.
New missing host integration cases are selected in `test_watchlist_handoff.py`:

- `test_direct_click_rechecks_offset_after_render_and_binds_exact_item`
- `test_url_without_native_selection_or_changed_snapshot_cannot_dispatch`
- `test_confirmed_popup_play_has_fresh_oneuse_descriptor_not_render_authority`
- `test_actual_receipt_admits_route_but_same_title_ordinary_play_is_unchanged`
- `test_stale_profile_source_mismatch_and_conflicting_id_withhold_admission`
- `test_folder_episode_parent_proof_preserves_raw_identity_and_exact_season`
- `test_actual_start_seek_rechecks_nonce_exact_item_and_uses_current_progress`
- `test_changed_item_invalid_clock_seek_failure_and_zero_replay_are_safe`

These use real helper and extracted actual overlay functions with controlled
native-receipt/player boundaries. They do not claim native or Android behavior.
Command: `python -m unittest -v test_watchlist_progress test_watchlist_handoff`.

Final source-binding correction retains existing `resume_verified_ids` when no
new canonical scope is proved and checks the arming identity kind/coordinates.
Add two selected cases before the rerun of affected functions (27 total):

- `test_exact_runtime_emitter_pins_and_cached_stamp_detect_tampering`
- `test_changed_emitter_or_typed_coordinate_withholds_receipt_enrichment`

The source-pin case copies only reviewed public/exported source files into a
disposable temporary directory; it does not execute provider code or mutate any
installed provider. Runtime installed-U identity remains a real-device gate.

After the 27-case pass, add only the previously missing chained integration
case `Handoff.test_actual_av_arm_existing_writer_series_resume_completion_and_replay`.
It exercises actual AV arming/identity/writer functions, provider-only conservative
Next Episodes, completion/replay, and confirms arming performs no history write.
Run this one new case; do not repeat the already passing 27 without a new change.

The first chained-case run exposed misplaced test-fixture lines (`entry` was not
in that new method's scope). Move them back to their original negative case;
production source is unchanged. Rerun only that corrected negative case and the
new chained case, retaining the fixture error in the receipt.
