# P0 CORRECTED SCOPE — Cobra 2103429 NON-PRO player-button action mismatch

**LATEST EXPLICIT USER CORRECTION — OVERRIDES ALL PRIOR PRO-CENTERED ASSUMPTIONS**

**The button defect is in the OTHER COBRA VIEW MODES, NOT PRO. PRO ALREADY WORKS.** This was clarified directly by the user on October 29, 2026. An earlier assistant-authored version of this file incorrectly called the affected strip "Pro-style" and asked for Pro dispatcher investigation. That was a misunderstanding of the user's report, **not user authorization to repair Pro**. This corrected instruction supersedes that language and supersedes any Pro-focused interpretation in FOLLOWUP-2103430.md, FOLLOWUP-2103431.md and related QA notes. Retain the historical work and failing evidence, but do not treat historical Pro-specific successes as proof of a non-Pro fix.

**USER AUTHORIZATION:** Implement and verify the original button-to-action correction in the actual affected NON-PRO view modes on the EXISTING Cobra branch. This is focused production correction, not an audit-only or standalone project.

**Repository:** `mahfouzhassine8-ops/project-infinity`  
**Existing branch:** `work/cobra-only-from-2103427-20261028`  
**Physical Fold report:** installed combined APK `2103429`, private recording `20608.mp4` and user's explicit verbal observations. Do not claim the recording is accessible inside a different Codex workspace without checking.  
**Signed 2103429 reference:** `f2b76fb76ad4edd87197f9521347295b4e612f26`, signing run `40818697397`.  
**Approved, immutable recovery baseline:** `lock/infinity-cobra-2103427-user-approved-20261028` at `782242090483982c39a78f9c4da932a4751bdafc`.

## 1. Correct observed defect and the non-negotiable Pro boundary

The user's reported misrouting in **non-Pro** Cobra view modes:

| Visible control pressed | Reported result in 2103429 | REQUIRED action |
| --- | --- | --- |
| **Fullscreen** | Opens PiP — WRONG | Open Fullscreen |
| **PiP** | Opens PiP — CORRECT | Continue opening PiP |
| **More (⋮)** | Opens Fullscreen — WRONG | Open original More menu |

**Affected scope:** Mobile, Compact, Cards, TV Grid and any other NON-PRO variant that reproduces the problem. Determine the actual affected subset through testing; do not claim all four fail without evidence. All applicable non-Pro control strips must satisfy the correct identity→action mapping. Existing More-last position, button visuals, layout style, and mode-specific control sets stay as approved.

**PRO MUST NOT BE REPAIRED OR REDESIGNED.** The user explicitly reports Pro works correctly. Preserve its existing fullscreen/PiP/More actions, horizontal strip, menu contents/order, all Pro Sports Stats/Sports-only behavior, player, focus, touch, and visual styling. Pro may be checked as an unchanged negative-control reference only. A shared code path may only change if verified to produce **no behavioral regression and no unintended Pro production delta**.

The actual problem is **button action mapping**, not icon size, missing More, wrong Pro button ordering, or a request to modify Pro controls. Previous assistant guesses about those issues are invalid.

## 2. Correct the engineering mistake before proceeding

Work continued on the same branch and yielded signed candidates `2103430` and `2103431`. The source review describes a Pro-dispatcher edit using Fullscreen/More view identity rather than positional lookup. **These candidates have NOT been accepted by the user as fixes for the reported NON-PRO problem.** Their Pro-focused host/emulator tests cannot establish that the non-Pro user reproduction was corrected.

1. **Stop any Pro-only corrective activity or Pro-only success claims.** Do not promote/lock 2103430 or 2103431 as the button fix.
2. Compare actual shipped 2103429 Pro behavior/members with the 2103430/2103431 Pro dispatcher change. Since the user confirms 2103429 Pro already works, **restore/retain the known-good Pro path** if the recent edits changed it unnecessarily. Verify parity first; do not blindly revert shared code or discard unrelated approved improvements.
3. Retain verified and authorized 2103429 Multi-View/Pro Sports and performance work. Preserve the independent user-approved theme-aware Infinity launcher icon work introduced afterward, subject to its separate owner verification. Do not start a separate APK or rebuild an icon-only candidate to fix this button bug.
4. Inspect **the actual non-Pro player/preview controls** of the 2103429 signed component and the current candidate, particularly construction order, More-last reorder, click listeners, indexed action arrays, identities/tags, touch-hit rectangles, horizontal scrolling or clipping where present, overlay interception, and mode-switch restoration. Trace the actual displayed button to its invoked action. Do **not** assume Pro's helper or its dispatch indices apply to every other mode.

## 3. Concrete implementation criteria

- Fullscreen pressed from any affected non-Pro strip must enter the supported Fullscreen presentation, not PiP.
- PiP stays mapped to the working PiP handoff.
- More opens the real existing overflow/context menu, not fullscreen or PiP.
- Preserve existing ordering, labels, icons, size, visual themes, animations, selected channel, audio, streams, playback/session, timeshift, PiP return, focus, and Back behavior.
- Do not use cosmetic reordering as a substitute for correct dispatch. Diagnose whether a visual hitbox intercepts a neighbor, the wrong action is attached, stale listeners survive a view-mode change, or a scroll coordinate/index becomes misaligned.
- Do not modify underlying Pro code/behavior as the fix. If shared layout dispatch is involved, isolate the new behavior by actual active non-Pro mode with evidence and Pro-parity tests.

## 4. Required focused verification

**PRIMARY target is NON-PRO real button/touch dispatch.** For each of Mobile, Compact, Cards, TV Grid (or supported applicable mode), record current baseline result before correction, then actual post-correction result. If a mode cannot render the control, mark it NOT APPLICABLE with code evidence rather than fabricate PASS.

- Reproduce at the coordinates of the visibly labeled Fullscreen, PiP and More controls, including the initial viewport and any scroll/clip states where relevant. Exercise actual production view dispatch (touch and supported remote focus), not only direct callback invocation.
- Confirm expected **Fullscreen→Fullscreen, PiP→PiP, More→More**; check no adjacent hitbox captures, event duplication, stale selection or wrong mode routing.
- Verify More-last remains correct across non-Pro modes after returning from Fullscreen/PiP and switching modes.
- Run **Pro negative-control regressions ONLY**: ordinary Pro and Pro Sports remain exactly as already working; menu, fullscreen, PiP, More, Stats and order unchanged. Do not treat passing Pro tests as a substitute for non-Pro tests.
- Source/APK owner checks: frozen Infinity 2103427 exact, Cobra non-target code unchanged, chooser existing Version treatment, approved icon variants and dark original artwork preserved, shared native/DEX/persistence/shutdown protected, original signing certificate and install-over identity unchanged.
- Keep previous failed test evidence. Do not turn old Pro host PASS into non-Pro PASS, or infer a physical Fold PASS from host-only/emulator results.

## 5. Delivery and stop conditions

Do not deliver, promote, or lock the existing signed `2103431` as a **confirmed correction** to this non-Pro issue. It can remain an unaccepted historical candidate with independently verified icon work.

Continue the **EXISTING Cobra task/branch** and, after a genuine non-Pro fix and focused correctness/preservation tests, integrate it into ONE properly signed next-version combined install-over APK with matching component ZIPs and hashes. Retain accepted 2103427 as recovery. No repeated experimental APKs, no uninstall/data wipe, no new shutdown tests, no arbitrary shared/native/Infinity mutations.

If Codex cannot reproduce the non-Pro action mismatch on available runtime, show the exact blocker and preserve the physical user report as unverified-on-CI rather than shifting attention to Pro again.

**Exit condition:** real affected NON-PRO view modes are corrected and proven under applicable focused interaction checks; **Pro is unchanged**; working PiP and all previously accepted Cobra features remain; user's Fold acceptance is still pending.
