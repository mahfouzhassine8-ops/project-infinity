# Infinity consolidated implementation — five workstreams retained

Authorization: continue the full consolidated implementation. This checkpoint
extends the protected 2103377 TEST4 and skin 1.0.5.223 foundations. It does not
replace the consolidated handoff or authorize a final lock.

| Workstream | Current concrete work | Remaining acceptance gate |
|---|---|---|
| 1. Native Android stability | Exact physical OnJobComplete cycle corrected and baseline/candidate mutex regression passes. Complete TEST1 and first combined watched/touch native builds and permanent-signer packaging pass. Callback retirement remains byte-identical in the expanded build. Scoped-identity TEST3 rebuild and permanent signing pass from native source 093323fbc0ae87cbe2fa2a21abab0c357fdaf754 and signing source 6f585cb5e02fd1c93dfb548dd758a5e4dad7b764. | TEST3 original fresh/loaded Close pass; cold and core-initialized fail at the unchanged checkpoint deadline. The online helper integration also exposes a protected-durability Close failure during automatic scraper updates; all remain open. Physical background return, screensaver, playback, PiP and shutdown remain open. |
| 2. Watched / Resume Hub / Watchlist | Read-only native immutable row index, guarded helper and existing CC .20 writer integration implemented. Blue presentation supports explicit Unwatched over native playcount. Watchlist/Collection never seed Continue. 13 state, 26 actual CC runtime/action, 2 installed-producer guard checks pass; 22 native identity cases and concurrent publication pass. | Final Kodi before/after 16x9 renderer, exact helper ZIP and menu/store gate pass in all three themes, including the Light focus contrast refinement. Actual Android native-row/helper/index-recovery cases and independent offline strict Close/reopen/persistence pass, including exact runtime helper source hashes. Current installed provider versions need hash checks. Historical unproven episode scopes are withheld until explicit verified replay; unknown anime numbering and provider-native actions without callbacks remain limited. |
| 3. Add-on touch and recovery | Custom 1193/50 long-press now preselects the hit row before the original single right-click dispatch. The production branch test reproduces baseline first-hold failure and candidate first-hold success, plus transforms/edges/scroll/visibility negatives. Original Home rail method remains exact. Recovery 1.0.0 previously passed real Kodi enable/reappearance/settings-retention tests. New skin has a native Manage add-ons route. | Physical long-press, Movie/TV rails and actual Otaku enable/recovery. Capture reports Rails .026; no newer phone inventory exists in this environment. No provider or Rails replacement has been made. |
| 4. Infinity skin refinement | Full forward .224 candidate built from exact .223: 2916 original files unchanged, 139 changed, 16 added, none removed; all 2149 XML parse. Approved blue checks and theme-aware watched text added without changing existing actions, control IDs, animations or scroll times. Protected Home/native browser/FileBrowser/ZIP preview/player boundaries stay byte-identical. | Final production 16x9 row projection passes in Light/Dark/OLED; the targeted focused-label contrast correction was visually reviewed. Full-skin all-screen and Fold cover/unfolded acceptance remain open. Broad animation changes remain gated. |
| 5. Integrated verification | Scoped TEST3 native producer 39004549623, permanent-signer producer 39004584047, original Android preservation run 39004611791 and separate actual Android row fixture are coordinated. Matching observational capture 1.0.2 passes its ten unchanged inherited tests. Same-code TEST4 rollback and exact native debug match are verified. | Bind the exact APK/skin/helper identities and all passing/failing results into one experimental diagnostic package. Do not treat the offline helper fixture as resolution of the three open shutdown failures. Physical 5/20/45/90-minute, playback/PiP/session/screensaver/Close/persistence/provider/theme matrix and explicit user locking approval remain required. |

## Immutable inputs

- TEST4 APK lock commit: `9dea86a7bf1896993e33ab885aa678a25eddaa0f`.
- TEST4 APK SHA-256: `bcdcbed5aeaed0bf30e6e590d9ceda7c0177d780b12e98773fa9503beb793286`.
- TEST4 packaged engine SHA-256: `2f1597ecc4f8a0ee09f24e399aa738b96a876c7760eaec0ee0ad1a18bafd6929`.
- TEST4 exact native source: `f5e3d9434d8a8c0918d1f4cc6758cf3704eb873c`.
- Skin lock source: `3cc1e1d5e0d5a21db9d19dd6882bd1c647603488`.
- Skin .223 full ZIP SHA-256: `557003afc83a2661fec6ccef921979e264ff28e93595fb633340c618ab69bd56`.
- Saved Rails .026 ZIP SHA-256: `5e4ff64592d6f8660d17db1077ed85a368c02f4eb14442760797b1d133c08179`.
- Permanent APK signer SHA-256: `d7adeb68e9341596a02bd3262b737a0f45fc6e771ed7e60285437e833b58c6d7`.

The latest recorder manifest reports skin .223 and Rails .026, but cannot query
Command Center. Earlier physical installed-code hashes verify Command Center
.20's six principal files. Those older hashes are not a fresh device audit.
Before controller/helper replacement, require a current installed preimage check;
never silently downgrade or overwrite unknown/newer installed code.

## Native correction and proof limits

`OnJobComplete` formerly replaced its vector of shared GUI items while holding
the directory mutex. Final item release runs GUIListItem::FreeMemory, layout
FreeResources and texture cleanup; TextureManager::ReleaseTexture acquires the
graphics mutex. The GUI processes the directory while already holding graphics.
The physical capture proves both owners and reciprocal waits across five samples.
It does not contain the worker's full stack or identify an exact destructor.
Source tracing and the extracted-callback OS-mutex test establish that this item
retirement path can produce the observed cycle.

The correction copies incoming references and swaps the old list into a local
declared before the directory guard. Reverse destruction order releases the
directory guard before retiring old GUI items, including exception paths.
Stale-rail rejection, job identity, update-state transitions and failed-job
semantics are retained. No force-unlock, timeouts, save waivers or lifecycle
restarts are added. The isolated TEST1 native source comparison allows exactly this one callback
file to change from TEST4. The expanded watched/touch candidate separately
enumerates six changed and two added native files; all other native sources,
the corrected callback, original Home rail hold, and shutdown/admission gates
remain byte-identical to the completed repair stage.

The first native candidate uses versionCode 2103380. The scoped watched/touch
candidate uses 2103382 TEST3; the superseded first combined build used 2103381
TEST2 and is not the delivery candidate. A separately signed compatibility
rollback uses that same code and restores TEST4's functional payload, avoiding
Android downgrade installation. The exact locked 2103377 APK remains unchanged.

## Required physical gate

Each 5/20/45/90-minute background duration must record candidate identity, live
process versus OS-reclaimed restart, screensaver state and navigation outcome.
Repeat cover/unfolded, rotation, split/pop-up, no-video and playback variants;
check PiP, background audio/video, session restoration without autoplay and a
real Essential-First Close/reopen with persisted data. Test screensaver on/off,
screen off, Home/Recents, network changes and immediate navigation on return.
No host or emulator observation is a physical Fold result.

Final release is one coordinated APK/skin/helper package with separate source
commits and verification gates. No protected ref, original APK/skin, provider,
profile, settings, database or credentials may be replaced by development tools.
Final locking and promotion require the user's physical Galaxy Fold validation
and explicit approval.

## Continuation identities and limits

The first native verification bundle remains preserved as historical TEST1
proof. Work has continued into watched, touch and skin code; this project is
still the complete five-workstream project.

- First combined native success: run 39002607563, source c4f0e315f4595b9f7cb3446ed5ad04a6f490b07b.
- First combined permanent-signer success: run 39003451792, source a4d9b1272691b1ba9734dcabe6d85c16e95c2e18. Superseded by the episode-scope correction.
- Scoped native TEST3 producer: run 39004549623, source 093323fbc0ae87cbe2fa2a21abab0c357fdaf754; SUCCESS.
- Scoped TEST3 signer: run 39004584047, source 6f585cb5e02fd1c93dfb548dd758a5e4dad7b764; SUCCESS.
- Original four Android cases: run 39004611791; no probe changes or skips.
- Skin .224 full ZIP SHA-256: e23d5d08c7737f317c2d55ae3f27e8746a019afd02dc20f6fbc73dc48c0c994e.
- Recovery .1.0.0 source: 2d5df339c0a32b678df80852b94e878b1752a8e7.
- Recovery real Kodi success: 38998654474 / 117296699964, two harmless video fixtures, not actual Otaku/Fold.
- Recovery ZIP SHA-256: dba95ad2a74bc220aeb2d6b045ef303ec2b83ec819ae72a09f3d470c9acf4ae8.

POV 6.10.06 and Umbrella 6.7.92 public episode producers were traced: their
generic tmdb/tvdb/imdb fields identify shows, plus season/episode coordinates.
The helper requires reviewed installed version AND exact producer source hashes
before applying that scope. These public versions are not a phone inventory.
Unknown versions, Otaku absolute numbering, untyped rows, mismatched namespaces
and historical episode rows without a verified producer attestation are not
silently mapped. Explicit verified actions retain the existing controller key,
route and identity and add a bounded presentation proof within the same
checkpointed progress file. Read-only background presentation never rewrites
that file, providers, settings or databases.

The Linux renderer fixture extracts actual 16x9 provider-row XML, exact source
font files, recursively required palette/includes and artwork. It is not the
full skin or a Fold validation. Failures in fixture activation remain visible
until a real run passes. Actual Android native index testing is a separate gate;
Linux stock Kodi cannot certify a newly compiled Android native implementation.

The helper refuses manual writes unless all 13 installed CC .20 preimages
match. It never installs or downgrades Command Center or Rails. Existing provider
native watched/Trakt controls and data remain intact; callbacks without a
supported adapter are a declared compatibility limit, not an assumed sync pass.

Fresh physical inventory and return-test exports are evidence gates, not a
request for another general implementation authorization. No user device is
connected to this environment. Nothing is merged, promoted, locked or marked
physically accepted. Keep all five rows in the ledger across continuations.

Real Kodi renderer success: run 39006084978, jobs 117318751960 (before) and
117318752116 (after). Startup fixture setup may terminate its isolated Linux
process group after saving the fixture; this is not shutdown acceptance. The
original Android Close probes remain unchanged and independent.

Final helper / renderer verification: run 39007979797, source e15d6e94498e54b97a2769e97fdc392cca0a139d; both versions PASS. The helper strips native DB mutation authority from verified provider episodes, including older saved watched entries, while keeping their keys/routes and unrelated data. Candidate helper ZIP SHA-256: c889693c2572456d0c6a176f5b8425ab0f854678fcd78e76391430f78d37e731.

Actual Android online integration: run 39006400078. All 14 native cases, existing-writer/read-only-helper/native-row pipeline and recovery without data writes PASS; strict Close FAILS for protected_durability_failed on an add-on staging LICENSE.txt during automatic scraper updates. The offline helper rerun 39006924487 controls only automatic updates in its disposable profile; original shutdown probes/settings/deadlines remain untouched, and the online failure remains unresolved.

The final helper additionally refuses a new menu action while an older durable native-library update is pending. It preserves that queue byte-for-byte and never drives or acknowledges the old operation. New writes and their existing checked flush stay in the participant’s reentrant lease. All 26 host controller/action checks pass. Final actual Kodi before/after renderer run 39007979797 passes both versions with this exact helper. The baseline fixture now enables all known test add-ons explicitly and waits for the selected Home-row context before evaluating its unchanged watched predicate.

Current independent offline Android helper verification: run 39008033374, source 39625e8b68e22e9df76b36d32a1a246b1fcac500. It preserves normal first-launch profile creation, blocks only the disposable app UID’s external IPv4/IPv6 while retaining loopback, sets and reads back the fixture update policy via native Kodi RPC, and retains every original strict Close assertion. Earlier setup attempts are retained as history, not inferred passes.

Final offline Android helper result: run 39008033374 / job 117324421178; PASS. Artifact 12091802145 has SHA-256 25c3df6d23636e87fd96f1601410c53abafbed0cbc5d352ed20d6b6c8c8a5add. All 14 real native cases, nine actual helper source hashes, existing-writer/read-only-helper/native-row publication, recovery without progress writes, unchanged strict Close with all owners and Java seals, whole-package death, reopen and watched/list persistence pass. This does not close either original early-start failure or the separate online automatic-update Close failure.

Coordinated diagnostic package: Infinity-2103382-Consolidated-Five-Workstream-TEST3.zip; 462453229 bytes; SHA-256 e6743874b9a4798bd3b81bc7efd9000055373f4eb464895c52d60b6ef55e9f2a. Its 107 bound payloads retain the original handoff, both rollback forms, all five status rows and both passing and failing gates. The package and matching native debug evidence are saved. All five complete flags remain false; user physical Fold acceptance and the unresolved native shutdown gates remain required.
