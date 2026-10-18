# Infinity — binding 1–16 completion tracker

**Status:** OPEN. **Current step:** #1. **Fully completed:** 0/16.
**Repository:** `mahfouzhassine8-ops/project-infinity`.
**Development branch:** `work/infinity-post-2103384-feature-restoration`.
**Protected user-approved APK:** 2103384, SHA-256 `b571676731bb9bdccb25134c557be613e15cc9adaf77d6675dabc8e0586e54af`.
**Locked skin:** 1.0.5.223; preserve user's later installed 1.0.5.225 and all data.
**Final acceptance device:** Samsung Galaxy Fold, One UI 9, Android 17/API37.

## Governing no-exceptions instructions

- Fix **only** the specific numbered requirement under examination; use verified prior implementation rather than recreate it.
- **Cobra is off limits:** no changes to Cobra code, features, player path, assets, settings, dependencies or runtime behavior, including via shared services. Any unapproved Cobra impact blocks the item.
- No unrelated changes, regressions, silently removed APK files, feature deletions, compatibility downgrades, redesigns, rollback, uninstall, data clear, or false success.
- Test change scope against exact protected versions **before** claiming an item complete. Preserve signed/native identities and produce exact source and artifact checksums.
- Green host checks and generic emulator checks are limited evidence; do not claim Fold acceptance without physical testing. A failed Close or missing crash cause remains failed/open.
- An item gets `[x]` **only when all its explicit functional, preservation, and required acceptance gates pass**. Partial work stays `[ ]`; write progress separately. After checking an item, report “#N COMPLETE” and show the updated list.
- Complete **one numbered step at a time**, in order; do not begin the next until the current item's required gates are resolved. Stop and ask approval for any shared-component conflict rather than touching Cobra.
- Only after **all 16** checkmarks and the full binding audit may the approved work be packaged into **one** permanently signed install-over APK. Signing, testing, and user final lock are separate gates. User must approve final lock.

## Live checklist

- [ ] **1.** Player Rotate button; white Follow Device / cyan Infinity-controlled; Playback Display Mode removed; all unrelated playback preserved — **IN PROGRESS: existing .226/.227 Work Rotate patch under preservation verification; not Fold-certified.**
- [ ] **2.** Home Continue Playing context menu; complete actions and persistence without normal-tap regression
- [ ] **3.** Video Sources exact first-tap select / second-tap launch / selected-hold menu; both columns and focus
- [ ] **4.** Exact approved context menu order and relevant actions; Hide is reversible and never Disable
- [ ] **5.** Universal blue watched indicators, Resume Hub and Watchlist/Collection correctness; durable identity
- [ ] **6.** Home Movie/TV rails long-press, touch parity and correct options with no black ghost popup
- [ ] **7.** Safe add-on recovery and physical Otaku re-enable with all settings retained
- [ ] **8.** Full approved Infinity skin refinement, themes, Fold layouts, animation, ZIP preview and navigation
- [ ] **9.** Native stability / OnJobComplete deadlock correction / background return, screensaver, PiP, session continuity
- [ ] **10.** Essential-First Close and durable save-state; zero blocked essential writers; genuine exit and reopen
- [ ] **11.** Android Version Check correction; preserve service and strict native writer safeguards
- [ ] **12.** Original abnormal native exit status 139; evidence-grounded root-cause fix and regression proof
- [ ] **13.** Preserve ALL existing Infinity and Cobra behavior; Cobra completely off-limits; shared components unchanged unless approved
- [ ] **14.** Include every required hash-pinned component in one APK with original dependency/compatibility parity
- [ ] **15.** Install-over activation and preservation of user data, installed Diggz build, settings, add-ons and skin
- [ ] **16.** All sixteen acceptance gates + binding preservation audit; Android17 and physical Fold verification; final user-approved lock only

## Proof required before checking #1

- Pin **exact existing** signed APK/skin identities; reuse Work's already implemented rotation patch from the exact .225 source. Verify the white/cyan state and the actual platform orientation actions rather than a cosmetic icon swap.
- Preserve correct player OSD controls, original independent Repeat functionality outside Rotate (where approved), Video Settings, zoom/aspect, audio/subtitles, PiP/background, and all **Cobra** assets/code and dependencies byte-for-byte.
- Verify only approved player OSD and Playback-menu skin entries differ; no unrelated XML/navigation or shared-service changes. An unanticipated difference blocks acceptance.
- Require direct Android 17 gameplay tests and Fold orientation/fold/unfold evidence before the final #1 checkmark. Generic emulator is not the user's One UI firmware.
- No candidate build or signed APK promotion at this stage. The rest of the list remains unchecked.

## Current factual context (not a completed-item claim)

- Work's skin `1.0.5.227` implements the approved Rotate/Playback layout and has source and emulator evidence; that **does not** establish physical Fold parity.
- Locked 2103384 remains protected. Previously attempted all-in-one 2103388 has unapproved Compatibility-service file loss and is **rejected** as a final candidate.
- Original native crash, Essential-First Close and complete single-APK install-over remain **OPEN**. Source-only 2103389 is not a verified signed build.

**Updating rule:** Add dated source/CI/device receipts under the relevant numbered item when evidence passes; keep remaining checkboxes unchecked. Do not turn a risk, assumption, or source-only assertion into a checkmark.
