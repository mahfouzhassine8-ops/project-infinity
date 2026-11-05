# Signed2103456 failure investigation and isolated correction candidate

**NOT ACCEPTED. Original-key testing 2103458 and higher-version recovery 2103459 are signed, independently downloaded/verified and available. Neither was installed.** See [current delivery, exact comparisons, recovery and limitations](DELIVERY.md). The user physically confirms only drawer height and Power placement. Device-installed versionCode is **UNVERIFIED**. Signed451 and all19 recovery locks remain unchanged. Signed456/457 artifacts remain preserved, without promotion.

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

The current [17 canonical browser source checks](results/CANONICAL-SOURCE-CHECKS.txt), [six presentation cases](results/GENRE-PRESENTATION.txt) and [17 existing view-preference cases](results/PREFERENCE-REGRESSION.txt) pass. Earlier source checks and the exact Videos-window preservation check remain recorded. Initial baseline geometry/stretch failures and fixture failures remain under results; the original test requiring wrapped left-row text was superseded by single-line overflow/selected-row scroll plus full selected-title wrapping. That earlier expectation is not a separate proven phone defect.

Linux Kodi21.2 rendered the full skin and original signed assets with synthetic local media at cover/inner portrait/landscape representative sizes. **Upstream lacks Infinity's responsive native extensions.** Fixture coordinate projection is explicitly documented/source-bound in each PROJECTION.json. These are not Android engine, real-provider, native-touch or physical Fold tests. Native Info, Play and Trailer were activated through real focus/Action Select; the generated silent clip actually decoded/advanced, Stop returned to the same browser. Missing-art/trailer and nonplayable TV-folder cases were checked. Screenshot existence/boolean checks alone are not visual acceptance; [manual review](results/VISUAL-REVIEW.json) records the clipped-controls failure and remaining reference differences.

## Exact reference access — resolved

The canonical PNG and actual failing Light JPEG are now SHA-verified and directly inspected. Originals and transport are preserved in evidence-only commit630e4009. See [verified continuation and precise Apple-case cause](VERIFIED-REFERENCE-CONTINUATION.md). Earlier access-failure records remain historical evidence, not a current blocker. Physical visual acceptance is still pending.

## Search and Favorites stay unresolved where evidence is missing

Search's confirmed Nixtoons settings/history self-invalidation and identical-rewrite acceptance still have **two required FAIL results**, retained unchanged. The existing shared revision correction remains present; this branch does not weaken meaningful configuration/source/pin, cancellation, profile or request-ownership checks. Endpoint XML equality cannot safely distinguish a legitimate temporary configuration change restored to its original bytes. Additional mutation-history authority is outside the two-file touch authorization; the blocked settings-retirement prototype is untouched. Crew's real rejected request has not been attributed to Nixtoons' mechanism. The user's successful direct-provider searches are retained as capability evidence, not evidence that Search All publication is repaired.

Favorites already uses the native registered route and service. Source review confirms system/profile XML loading and existing lock filtering; it does not establish which explains the reported missing collection. No phone Favorites file/API/container snapshot is available. The previously delivered read-only count/status diagnostic remains the smallest observation, with no actions/URLs/titles or user-data writes. It has not run on the Fold. Do not clear/rebuild Favorites or substitute an add-on collection.

## Preservation and release boundary

[Source delta](results/SOURCE-DELTA.json) is the immutable source-stage snapshot: six existing runtime source changes plus one new helper versus actual signed 456. It is not the final APK receipt. Current signed 458 changes 14 existing payload members (six runtime source and eight authenticated/version metadata) plus the new helper; 7,607 existing members, all 47 native libraries and all five DEX files are unchanged from 456. Cobra, Preview and unrelated payload remain frozen. [Independent downloaded comparison](packaging/signed458-evidence/INDEPENDENT-SIGNED456-COMPARISON.json).

The initial authority preflight rejection is historical and resolved through distinct controlled 458/459 registration in the existing original signer. Preparation, official review, both signings and actual download/component catalog verification passed. Original key, security/durability algorithms and accepted pointer remain unchanged; all 19 recovery locks are preserved. [Signing status](SIGNING-GATE.md). The original 456/457 artifacts remain available, but 457 cannot recover higher 458.

Signed 459 restores frozen 451 functional code with higher authenticated generations. The 21 original-key host recovery checks passed; actual Android install-over and recovery are NOT RUN. Follow [the forward-only recovery procedure](DELIVERY.md) and [physical checklist](FOLD-CHECKLIST.md). No installation, uninstall, data clearing, shutdown suite, promotion or lock occurred.

Current focused evidence is 17 browser source cases, six genre-presentation cases, 17 existing preference cases, 15 navigation-entry cases and 11 packaging contracts. The two required Search tests remain FAIL; missing Favorites attribution and universal browser/Fold acceptance remain unresolved. Earlier source, geometry, clipping and fixture failures remain historical evidence. Android/Fold is NOT RUN; no compatible connected target is exposed and the known-broken emulator was not retried. Scudo, pending persistence obligations and unrelated stability work are unchanged.
