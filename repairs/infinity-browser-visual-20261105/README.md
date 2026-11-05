# Signed2103456 failure investigation and isolated correction candidate

**NOT ACCEPTED. No successor APK built, signed or installed.** The user physically confirms only drawer height and Power placement. Device-installed versionCode is **UNVERIFIED**. Signed451 and all19 recovery locks remain unchanged. Signed456/457 artifacts remain preserved, without promotion.

## Actual APK audit

The actual original-signed456 artifact from run41988386798 / artifact13397163155 was downloaded. Full APK SHA256 is `81aed468bcdf4031f3186fa7c5aa73e396a38f27837581fbcc54f56cbbc94696`; original certificate is `d7adeb68e9341596a02bd3262b737a0f45fc6e771ed7e60285437e833b58c6d7`. All278 targeted extracted source hashes match the signed member inventory. [Actual receipt](results/signed456/ACTUAL-PAYLOAD-AUDIT.json). This is evidence about the delivered APK, not proof it installed or its assets became the active skin on the phone.

The expected drawer XML, helper and their protected-manifest hashes are present. The failure is therefore not explained by simply omitting those packaged files. Installed Umbrella/SportHD source and phone add-on/profile state are not present in the APK. No fresh installed-provider verification is claimed.

## Navigation: complete static call chain, bounded execution evidence

| Visible button | Signed456 callback and real destination | Current isolated correction |
|---|---|---|
| Movies1198102 | Raw skin helper → existing eligible/title-navigation inventory → installed Umbrella router AST/pins → `movieNavigator` → native Videos activation | Same functions through existing authenticated Command Center `default.py`, `library-navigation,movies` |
| TV1198103 | Same guards → `tvNavigator` → Videos | Same existing entry, `library-navigation,tv` |
| Sports1198110 | Raw helper → enabled reviewed SportHD identity, manifest/version/publisher/entrypoint → provider root | Same guards/functions through existing entry, `library-navigation,sports` |
| Favorites1198301 | `ActivateWindow(favouritesbrowser)` → native registered Favorites window → `favourites://` → existing FavouritesService/profile collection | Unchanged; no new collection or migration |
| Browse Files1198112 | Raw helper → JSON-RPC Videos, `files`, `return` → native `sources://video/` mapping | Existing entry, `library-navigation,browse`; no ZIP selector |
| Downloads1198113 | Existing readable Downloads check and recoverable permission/access explanation | Same function through existing entry; no new permission |

Kodi's native RunScript builtin resolves an enabled add-on ID to its registered script library, sets argv0 to the filename, then submits ExecuteAsync with that add-on owner. Thus the new callback reaches `default.py`, `direct_command`, unchanged `run`/route functions, existing JSON-RPC, then the native window/provider destination. `direct_command`'s True means *handled*, including a visibly reported refusal; it does not claim successful provider results.

**Confirmed integration gap:** frozen native first-party classification recognizes the authenticated Command Center entry but not the raw new skin navigation script. The latter has no registered clean first-party owner. **This does not prove it caused the phone's failed tap.** Unknown persistence obligations remain blocking. No native contract/checkpoint gate was changed.

Only five callback strings changed. The entire drawer otherwise compares byte-for-byte with the actual signed456 XML, including height, row order, Power, focus/Back/scrolling and loading notifications. Command Center bootstrap and all previous code compare byte-for-byte except the one new dispatch branch. Its library helper is an exact copy of the already-packaged helper. The old skin helper remains unchanged and uninvoked by these five rows. A successor must authenticate the added Command Center file in the original module manifest before execution.

[15 focused checks](results/NAVIGATION-ENTRY-CHECKS.txt) pass for this source chain, exact bootstrap/geometry preservation, guarded dispatch, wrong source/provider/version/disabled/missing-entry refusal and failure handling. The dispatch test executes the real function isolated from its AST; **it neither executes nor mock-passes the authenticated Android bootstrap**. Provider inventory/platform boundaries are fixtures. Actual Fold button → trusted loader → installed provider → visible destination remains **NOT RUN**.

## Browser corrections

Confirmed source defects include overlapping/unbounded nested coordinate spaces, selected-art `stretch`, generic Icon fallback into large poster variables, and the uncolored white-pixel panel texture in the normal media List. These are specific mechanisms; neither a model nor a Linux fixture proves every coordinate observed on the phone.

The isolated skin correction bounds the existing normal/Slim List columns, uses real selected artwork with proportional keep scaling, restores title/year/runtime/MPAA/genre/rating/synopsis bindings, maintains focused-only loading ownership, and delegates Play/Trailer/Info to existing native actions. Missing posters remain absent rather than becoming an Apple/Trailers icon. Only supported actions appear, with current capability/loading checks on invocation. No media content is hardcoded.

Short-window screenshot review caught clipped actions even though focus/activation checks passed. The correction now keeps that same action row outside the separately scrolling details region. Existing native grouplists, fonts, palette variables and resources own the UI; no new engine, theme system, gesture tracker, worker, preference store or provider adapter was introduced. Existing metadata remains reachable through details scrolling/native Info. Shared poster-variable changes are Videos/media-scoped; original non-media fallback values remain in exact order.

[14 source checks](results/CURRENT-SOURCE-CHECKS.txt) plus the [exact Videos-window preservation check](results/MYVIDEONAV-PRESERVATION-CHECK.txt) pass (15 distinct browser checks). Initial baseline geometry/stretch failures and fixture failures remain under results; the original test requiring wrapped left-row text was superseded by single-line overflow/selected-row scroll plus full selected-title wrapping. That earlier expectation is not a separate proven phone defect.

Linux Kodi21.2 rendered the full skin and original signed assets with synthetic local media at cover/inner portrait/landscape representative sizes. **Upstream lacks Infinity's responsive native extensions.** Fixture coordinate projection is explicitly documented/source-bound in each PROJECTION.json. These are not Android engine, real-provider, native-touch or physical Fold tests. Native Info, Play and Trailer were activated through real focus/Action Select; the generated silent clip actually decoded/advanced, Stop returned to the same browser. Missing-art/trailer and nonplayable TV-folder cases were checked. Screenshot existence/boolean checks alone are not visual acceptance; [manual review](results/VISUAL-REVIEW.json) records the clipped-controls failure and remaining reference differences.

## Exact reference access

The materialized21581 JPEG was opened directly and retained unchanged with SHA256 `13fbcfe29a21b6f9f73788da13d5921ed4f58741056b9a46a0996c03cea08f82` in the existing design-lock folder. The lock document is copied unchanged from745b542a. The original canonical PNG (`6786b5cadb7153bb0036a651dcfba889a58f2a5acd79a759a798302e2d70c0ad`) and the named broken-Light JPEG/ZIP are **not exposed to this executor**. Their inspection, exact checksum comparison and original-pair commit remain blocked. No replacement image was generated or mislabeled. `import_references.py` is ready to verify/import the original bytes when a supported reference becomes accessible; it has not run.

The supporting JPEG guides the two-column corrections; it is not a substitute for canonical exact-match verification. Individual genre pills, the native parent row and responsive short-window action placement remain disclosed differences/verification limits. The universal multi-view design and physical acceptance are **not complete**.

## Search and Favorites stay unresolved where evidence is missing

Search's confirmed Nixtoons settings/history self-invalidation and identical-rewrite acceptance still have **two required FAIL results**, retained unchanged. The existing shared revision correction remains present; this branch does not weaken meaningful configuration/source/pin, cancellation, profile or request-ownership checks. Endpoint XML equality cannot safely distinguish a legitimate temporary configuration change restored to its original bytes. Additional mutation-history authority is outside the two-file touch authorization; the blocked settings-retirement prototype is untouched. Crew's real rejected request has not been attributed to Nixtoons' mechanism. The user's successful direct-provider searches are retained as capability evidence, not evidence that Search All publication is repaired.

Favorites already uses the native registered route and service. Source review confirms system/profile XML loading and existing lock filtering; it does not establish which explains the reported missing collection. No phone Favorites file/API/container snapshot is available. The previously delivered read-only count/status diagnostic remains the smallest observation, with no actions/URLs/titles or user-data writes. It has not run on the Fold. Do not clear/rebuild Favorites or substitute an add-on collection.

## Preservation and release boundary

[Source delta](results/SOURCE-DELTA.json): **five existing source members + one new helper** versus actual signed456. Protected native/touch sources, Search/global-view service, original signer/workflow/authority/accepted pointer and19 lock refs compare unchanged. Cobra, Preview, DEX, libraries, providers, databases and user files have no new edits. No successor APK exists, so **no new APK-member/certificate/install-over PASS is claimed**.

[Release preflight](results/RELEASE-PREFLIGHT.json) is BLOCKED: existing trusted preparation/authority admits only the old456/457 branch/source/version pair. Calling its generator with458 refuses `ONLY_CONTROLLED_AND_RECOVERY_VERSIONS`; the fixed12-source checkpoint guard also cannot authenticate this six-member correction. User instructions freeze signing infrastructure and require stopping a failed authority/recovery gate. No guard, key, accepted pointer or old issued artifact was altered.

The read-only official workflow survey includes all82 runs and every readable successful-source authority; greatest recorded authority is457, with no missing source authorities. [Survey](results/VERSION-SURVEY.json). Proposed458 testing /459 forward recovery are **not reserved or issued** and must be rechecked before use. A concrete successor allowlist/recovery registration is provided separately; a new original-signed recovery must exist before installation. Existing457 is lower than a proposed458 and cannot be described as its install-over recovery.

Android/Fold tests are **NOT RUN**: no compatible connected target/control route is exposed and adb is unavailable. No known-broken emulator was retried. No installation, uninstall, data clearing, shutdown suite, promotion or lock occurred. Scudo, pending settings obligations and unrelated stability work are unchanged.
