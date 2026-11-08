# OPEN — Infinity native Search crash / Gemini follow-up

**Status: UNRESOLVED. Priority: HIGH.** This item must not be closed merely because the QA-only eight-search replay passed. GitHub Issues are disabled for this repo, so this file is the enduring production tracker.

## Evidence and preserved PASS results

- Umbrella/POV source compatibility: commit `16af10e42265f9f5155efd54849b25871c50aa0f`, [run 42435806833](https://github.com/mahfouzhassine8-ops/project-infinity/actions/runs/42435806833), preserved branch `locks/umbrella-pov-native-search-host-pass-20261107`. No installer has yet been produced.
- Native Search crash: [run 42437719318](https://github.com/mahfouzhassine8-ops/project-infinity/actions/runs/42437719318) on exact signed Infinity 2103464. After seven successful Search All cycles, eighth TV search `SpongeBob` returned Umbrella and Nixtoons2 headings; activating Umbrella heading preceded `SIGABRT` and `Scudo ERROR: invalid chunk state when deallocating` in native list-item destruction reached through `XBMCAddon::xbmc::getInfoLabel` / `CGUIInfoManager::GetMultiInfoLabel`.
- Isolated unchanged-APK Umbrella heading passed: [run 42441430136](https://github.com/mahfouzhassine8-ops/project-infinity/actions/runs/42441430136).
- **All eight Search All queries and two real Umbrella heading activations passed**: [run 42443988873 attempt 2](https://github.com/mahfouzhassine8-ops/project-infinity/actions/runs/42443988873), commit `2759febb289f9e1eebf4b122f78bdf802646efac`, artifact `13603118981`, checkpoint `locks/infinity464-eight-search-qa-pass-20261107`. Same signed APK, with only the disposable QA observer changed to avoid `xbmc.getInfoLabel('Container(50).ListItem.FileNameAndPath')` during heading activation. Real provider folder navigation and unchanged Kodi PID checked.
- Attempt 1 of that run failed in emulator startup before Search (`SIGSEGV` / `talloc_lib_init`); do not confuse this with the search crash.

## Gemini-derived lead, checked against code

- Possible C++/Python GUI list-item lifecycle / synchronization issue. Existing connected Kodi fork `mahfouzhassine8-ops/xbmc` has no explicit `XBMCAddonUtils::GuiLock` in `getInfoLabel`, whereas `getCondVisibility` does.
- `GetMultiInfoLabel` does retain a local `shared_ptr<CGUIListItem>`; do not claim there is definitely an unprotected raw pointer.
- Native destructor frame freeing `std::map<std::string,std::string>` is consistent with `CGUIListItem` artwork or fallback map, though precise corrupting writer remains unknown.
- The absence of one function-local GUI guard is not sufficient proof of a defect. Verify actual signed-464 source provenance, full lock ordering, Python GIL / delayed calls and graphics/frame-move guard before any change.
- See [review](https://github.com/mahfouzhassine8-ops/project-infinity/blob/work/infinity464-targeted-crash-diagnosis-20261107/repairs/infinity-final-release-462-20261107/GEMINI-SECOND-OPINION-FORENSIC-REVIEW.md).

## Required completion criteria — do not declare fixed early

- [ ] Audit production Search All/skin/service callers of live `Container.*ListItem*` labels, distinguishing production from the disposable observer.
- [ ] Match exact signed native source/binary and identify the operation corrupting the list item; do not assume the destructor is the bad writer.
- [ ] If proven, implement a minimal production fix on isolated branch, with no broad speculative locking or provider rewrites.
- [ ] Test repeated Search All movies and TV, real heading selection, playback/navigation and provider isolation, and no new Kodi crash/hang; reuse valid earlier passes.
- [ ] Sign through the existing original signing identity with compatible rollback/recovery; require actual Fold confirmation to close.

## Sequencing and isolation

1. Deliver signed Umbrella/POV **compatibility ZIP** if it can be installed safely with the user's real version (last reported APK 2103462 / CC 0.3.5.61). This includes **only** provider-native compatibility adapter changes, NOT the Gemini crash solution.
2. Continue this open production crash investigation; if native C++ change is required, release in a carefully signed combined APK, not a Kodi Python ZIP.
3. The Infinity-only Trakt Watchlist progress addition remains deferred.

**Preserve:** Cobra, Infinity skin/navigation, current search engine/native provider paths, Nixtoons/The Crew/Seren/Otaku, user data, command-center authentication, signing identity, recovery and all out-of-scope components. No unsigned source ZIP or misleading all-clear.
