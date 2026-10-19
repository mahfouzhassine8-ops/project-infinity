# GROUP #1 / DETAILED REQUIREMENT 01 — TV EPISODE SAVED-ROUTE CORRECTION, SOURCE-ONLY CHECKPOINT

**State:** SOURCE PATCH SAVED AND TARGETED HOST CHECKS PASSED. NOT INSTALLED, NOT FOLD VERIFIED, NOT THE FULL GROUP #1 REPAIR. No new signed APK. No user data touched.

## Scope, evidence, observed source fault

- The user reported **TV Shows → Continue Watching** displaying Infinity Resume Hub's "This source is unavailable or has expired" dialog for some episode cards, with at least one other episode opening the original Resume/Play chooser.
- Exact original signed 2103390 `assets/addons/script.infinity.commandcenter/plugin.py` SHA-256 **11a741a694869eeca6f1fbdac17bb6ab02c9f807c73a3aa95a4b43323fc574fd**.
- Source `_target` did `stable_route(preference.get('route') or entry.get('stable_source', ''))`. A non-empty expired HTTP preference or a plugin route whose addon is absent **masks** an independently saved, still valid original `entry.stable_source`. Result can be the unavailable action after the source's six-hour freshness allowance expires, even if a previously validated provider route exists.
- For TV entries, source previously required `show_ids_verified is True` and `show_tmdb` fields separately, even if existing `hub.entry_identity(entry)` already validates a proper **show_episode** typed identity and series TMDb ID. This can prevent using already verified series identity in a saved legacy record. The independent episode ID (`scope=episode`) MUST NEVER be substituted for show ID.
- These problems are **reproducible against a synthetic verified fixture**. The user's exact failed episodes and saved private record identities have NOT been independently confirmed as the same case; no fabricated routing success is claimed.

## Exact code-only correction

- Patch source file: `repairs/2103390-bugfixes/group1/tv_episode_route_patch.py`, original SHA guard, GitHub source commit `0a2a00b956dc3a98448a6b53e682c77c52c7f330`, later narrowed by commit **9ef345369b999694c944334385b4d77aaefc18f5**.
- For **TV episodes ONLY**, inspect source-memory preference and the saved independently captured stable route **separately**; choose the first valid existing route with available addon. For MOVIES preserve the original single-route preference order verbatim. Respect existing `failures < 2` gate; no retry bypass.
- For **TV episodes ONLY** with no direct verified `show_tmdb`, accept the previously saved `hub.entry_identity` if and ONLY IF its validation passes and `scope == show_episode` with a validated series TMDb ID. Reject `scope == episode`, unknown show IDs, unsupported addon and invalid S/E. Existing synthetic-next proof checks remain unchanged.
- Never rewrite/remove stored data, mutate source memory, touch actual player, provider services, SlyGuy, TMDb Helper addon code, CU LRC Lyrics, Cobra, shutdown or any native/core input path. Existing movie routing is regression-tested unchanged.

## Tests run and saved

- Source tests: `repairs/2103390-bugfixes/group1/test_tv_episode_route_patch.py`, GitHub commit **598f2673bf9d7aa847c6d57672b493c465074106**, narrowed with explicit movie-equivalence regression commit **65e27c93079507895bc88113389b0b786a608a9b**.
- 9 dedicated real-signed-source fixture tests **PASS**, including before/after proof of masked route, fallback for unavailable preferred addon, failures >= 2 not bypassed, typed series identity, rejection of episode-specific IDs, synthetic successor untouched, missing source kept unavailable, original movie route equivalent, no expired HTTP allowed.
- New full signed original APK virtual-scope test: `repairs/2103390-bugfixes/group1/test_group1_scope_apk_12.py`, GitHub commit **af2601ef76cf5b1f0381bb4dc35c46739997171e**. Original exact **7,430 members**, simulated changes to ONLY **12**: ten Home status orb includes, original Resume Hub `resume_hub.py` movie verified duplicate guard, and the original Command Center `plugin.py` TV route guard; **7,418 byte-identical** unchanged members, no added/removed members. This test is NOT a signed APK.
- Combined local **19/19 host tests passed**: `python -m unittest -v test_clock_orb_patch test_movie_identity_patch test_home_rail_contract test_group1_scope_apk test_tv_episode_route_patch test_group1_scope_apk_12`, `Ran 19 tests in 8.439s — OK` after the final strict TV-only narrowing.
- Verified exact local tested source files had the same Git content blobs as saved GitHub scripts: patch blob `b327bdfb67b4ded5a7fe813ebc0b9791f3cd2c9b`, test blob `5c58d733a839d60b66d0bd50a1e689fef972eee3`.
- Exact patched Command Center plugin.py resulting SHA-256: **ded5e435f1db7af205869ae33d9e2eab888825d95f5086095bc4615e09b05b4f**. Original APK remains unchanged.

## Remaining gates (must not mark complete)

- User-specific failing TV episode saved route, installed add-on eligibility and episode ID are unverified from the available diagnostic data. Unknown episodes MUST remain honest unavailable, not silently guessed or pointed at unrelated title.
- No on-device Android17/Fold real-source playback, play/resume, process close and reopen verified; no new component ZIP installed, no signed APK built.
- Group #1 other distinct requirements still open: original task #03 horizontal swipe/hit testing and vertical Resume chooser, original task #19 category switching without rail reloading; clock and movie changes host-tested but Fold pending.
- Original task #16 CU LRC Lyrics and #17 SlyGuy/TMDb standalone service-error repairs **SKIPPED_BY_USER** and untouched.
- All other Infinity functionality, **COBRA**, full native engine, signing, protected 2103384 Essential-First Close, installed data and default service registration must remain unchanged.

**This checkpoint is intentionally partial. Preserve it and resume only remaining authorized Group #1 work, with the same exact source-delta and runtime fidelity tests.**
