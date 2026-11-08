# Infinity 2103464 Search All crash — Gemini second opinion cross-check (Nov 7, 2026, EST)

**READ-ONLY SOURCE/TRIAGE REPORT — NOT A FIX OR APK ACCEPTANCE**

## Source/evidence used
- Exact signed Android17 failing run **42437719318**, artifact **13601500225**, `release-android-results/LOGCAT.txt`, `KODI-LOG.txt`, and `ANDROID-VERIFICATION.json`.
- Exact signed 2103464 isolated Umbrella heading replay **42441430136**, artifact **13602196512**, recorded `PASS_SINGLE_HEADING_REPLAY_ONLY`, process PID unchanged, same `plugin://plugin.video.umbrella/?action=tvSearchterm&name=SpongeBob`.
- Source snippets from connected fork `mahfouzhassine8-ops/xbmc` on branch `master`: `xbmc/interfaces/legacy/ModuleXbmc.cpp`, `xbmc/GUIInfoManager.cpp`, `xbmc/guilib/guiinfo/GUIInfoHelper.cpp`, `xbmc/guilib/GUIListItem.{h,cpp}`, `xbmc/utils/Artwork.h`. The EXACT provenance/hash equivalence of these fork files to signed 464 `libkodi.so` is not yet proven; do not claim a signed binary patch location from source alone.
- User's Gemini response is an independent hypothesis, not primary crash evidence.

## Confirmed from actual crash data
1. On the eighth Search All operation, after seven successful cycles, the TV query **SpongeBob** produced Umbrella heading (7 results) and WatchNixtoons2 heading (1 result); clicking the Umbrella heading entered test `select-row`.
2. Android logcat at **2026-11-08T02:36:12.944Z** records `SIGABRT` on Kodi PID 4925/thread 5135 and `Scudo ERROR: invalid chunk state when deallocating`. Kodi exited; the observer reply loop subsequently timed out.
3. ARM64-translated backtrace: `std::__ndk1::pair<const std::string,std::string>::~pair` -> `std::__ndk1::__tree<...>::destroy` -> `CGUIListItem::~CGUIListItem` -> `std::__ndk1::__shared_ptr_pointer<CFileItem*>::__on_zero_shared` -> `CGUIInfoManager::GetMultiInfoLabel` -> `XBMCAddon::xbmc::getInfoLabel` -> Python invoker. A CFileItem shared pointer released its final reference during a Python info-label read, and destruction encountered a bad allocation state. Exact earlier memory misuse is not identified.
4. The GUI focus warning `Control 50 in window 10025 has been asked to focus, but it can't` appeared **seven times** before the crash, including earlier passing cycles; last logged at **02:35:17.155Z**, ~56 seconds before SIGABRT. It does **not** by itself prove an empty container or explain the crash.
5. The same heading was opened successfully from a freshly launched single-search run **42441430136**. This excludes an unconditional heading failure but does **not** prove accumulation or eliminate a nondeterministic race.

## Gemini assertions requiring correction / careful qualification
- It labeled cross-thread C++ memory lifetime as a settled "classic" bug and assigned 65/25/10 percent probabilities; evidence does not support quantitative probabilities.
- `GetMultiInfoLabel` in the connected fork (and Kodi Omega upstream) keeps a local `std::shared_ptr<CGUIListItem>` from `GUIINFO::GetCurrentListItem`, not an unprotected long-lived raw list pointer at the indicated step. This protects reference-counted lifetime **after safe acquisition**, but does not prove thread-safe acquisition or concurrent mutation.
- The crashing stack destroys a **`std::map<std::string,std::string>` pair**, whereas `CGUIListItem::PropertyMap` in the connected fork is `std::map<std::string,CVariant,...>`; `m_art` and `m_artFallbacks` use `KODI::ART::Artwork = std::map<std::string,std::string,...>`. Thus **artwork or art-fallback map teardown is a more specific candidate** than general property teardown. Need exact binary/DWARF offset to distinguish the two.
- The connected fork `xbmc.getInfoLabel` function has no explicit `XBMCAddonUtils::GuiLock` in that routine, unlike `getCondVisibility`; missing function-local lock does not alone prove a data race. The full locking protocol, Python GIL/DelayedCallGuard, GUI execution/thread affinity, and potential deadlocks must be audited before any patch.
- Scudo invalid deallocation state supports a double free / invalid free or prior memory corruption, but the point of corruption may precede the destructor by many operations; stack is the **detection point**, not necessarily the bad writer.
- The script-only QA uses `xbmc.getInfoLabel('Container.ListItemAbsolute(...)')` repeatedly in a background Python invocation and `Container(50).ListItem.FileNameAndPath` during result activation. This is a concrete stress path which can be a race amplifier; it has not been proven the root cause of real Fold crashes.

## Ranked lines of investigation (no numerical confidence)
A. **GUI list artwork map thread safety and ownership**: trace `GetCurrentListItem` acquisition and `CFileItem`/GUI list art writes and destruction across GUI and Python threads; use exact 464 source map and debug symbols when available.
B. **QA stress-specific race**: change only disposable test observer in an isolated diagnostic experiment to avoid querying live `Container.*ListItem*` labels during GUI transition; compare crash incidence across same eight searches and identical signed APK. Do not change users' search interface for this experiment.
C. **Repeated search invoker lifecycle**: inspect background Python/GUI operations and addon writer ownership over eight cycles; note 47 Python invokers appeared in Kodi log in failing run vs 17 in one-query run, not inherently an abnormality or proof of a leak.
D. **Translational/emulator effects**: failing environment is Android17 x86_64 with an ARM64 native bridge; real Fold is ARM64. Reproduce or inspect direct ARM64 evidence before generalizing device-specific reliability.

## Safe next action
- Keep both prior PASS checkpoints immutable. Do not edit provider native searches, Trakt, regular Movies/TV, Cobra, skin, original signing, or prepared signed APKs.
- First try to obtain precise matched 464 native source/dSYM or ELF/DWARF map and identify the actual Python label expression in thread 5135; write a bounded QA-only diagnostic patch if evidence supports it.
- A **global GUI lock or raw-pointer lifetime patch is NOT approved** on these facts alone. Validate lock ordering and graphics-thread ownership before any native C++ change; regress known UI controls and repeated Search All if a surgical patch is ultimately demonstrated.
- Isolated pass != eight-query pass; final release remains gated. No installable ZIP produced by these QA runs.
