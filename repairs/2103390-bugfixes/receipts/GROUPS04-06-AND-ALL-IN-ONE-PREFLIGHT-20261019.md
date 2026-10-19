# INFINITY 2103390 — GROUPS #4–#6 SOURCE GATE + ALL-IN-ONE READINESS

**Date:** 2026-10-19. **Proven state: three individual source-test gates green; full all-in-one gate NOT READY.** This receipt is not a user-facing APK, not a compiled Android-native engine, not physical Fold acceptance and not a LOCK.

## Immutable user preservation contract

Protected signed original **APK 2103390** SHA256 \`778b84a5f0d8712f250c538bacfa3c01e1352a936e0b7b9aa79cbaada9b22dbb\` (7,430 members). The fully locked shutdown fallback **2103384**, original Cobra/source/Android UI, player/PiP/background, Kodi profiles, installed Diggz and Infinity skin ID, original installer/provider databases and user data must remain. Never uninstall or clear data. These source stages were tested against **that exact original 2103390**.

## Green isolated source gates

| Group | Approved code | Real GitHub Actions verification | Proven scope | Still red |
|---|---|---|---|---|
| **#4** | \`group4/player_glass_patch.py\` commit \`55df2ad96f6704aba9746917d1b2718e483e09e5\`, tests \`11087495f6da9efd175d0017bdf0dd3b1c2fc285\` | **Run 39265841878, 10/10 PASS**, no skips | 41 existing Infinity-only skin XML members across 14 layouts; existing OSD Display button #255 rebinds to real OSDVideoSettings, redundant Playback row #274 removed and focus adjusted, native Video/Audio settings use original controls with conditional glass surfaces | Device visual/behavior and actual AspectRatio shortcut preservation not verified. Original #255 had \`Action(AspectRatio)\`; new binding removes its original single-tap behavior. Prove user's approved intent and retain the original capability via real native Video Settings. Android renderer not tested. |
| **#5** | \`group5/final_native_identity_patch.py\` commit \`079b6b3249ca8c1849d00d0583fb4ae3e3a939fa\`; ELF SHT_NOBITS corrective commit \`cecb049cb66733deca395ddbd4a3713f01c92a17\`; tests \`44782f018809c98c7988d69eb3d3f1f8446160ba\` | First run 39266729693 **failed 7/10** due source-only ELF .bss parser bug; repaired and **run 39267576509 10/10 PASS**, no skips | Fail-closed one equal-length identity-field replacement in the original \`libinfinitycrash.so\` recorder, dynamically calculated from actual final \`libkodi.so\` SHA/ELF text rather than hardcoded legacy 2103229 hash. Zero native crash handler instruction change. | Actual October 19 06:44 **SIGSEGV/139** root cause still UNKNOWN: no stack/tombstone/mappings from crashing PID 29396. No cause-based crash fix. Native compiled/final collector identity not installed. |
| **#6** | \`group6/silent_mode_patch.py\` commit \`e9c83cf16783f307331b2f9ace1f10cc5a8ea10d\`, corrected minimal layout preservation commit \`6b79ac88963e9e61fe6c7429ab3bd9f21b8747ff\`; tests \`d2a0888d770a3e19aa18993757f3edbf03226c05\` | **Run 39269926154, 10/10 PASS**, no skips; upstream original Kodi Omega KaiToast source Git blob \`2f8ca00cd765dff09720ee002d6dc390a240fd32\` verified | 13 original existing System Hub XML files only, one persistent skin toggle named Silent Mode. All original System Hub button XML/actions/positions unchanged; only informational footer and glass envelope make room, unified grouplist appends exactly one toggle. Native proposed sole \`xbmc/dialogs/GUIDialogKaiToast.cpp::DoWork()\` Infinity-skin-gated presentation-only toast queue drop; no edit to third-party addons, logs, player sound, native interactive dialogs, Cobra or shutdown. | Native source not compiled into Android \`libkodi.so\`; on/off runtime, persistence after close, blocking script-error dialogs, real Fold/theme/popup suppression not verified. Non-KaiToast blocking modals are OUTSIDE silent notification scope. |

### Integration collision corrected and independently green

Groups #1 and #3 both modify \`assets/addons/script.infinity.uirepair/runtime.py\`. Original isolated scripts were **not composable** by their earlier exact-text anchors. \`group3/runtime_option_b_patch.py\` commit \`fe0e5f7f2e99dda373bf9edadc14a56ffaa5364d\` now accepts **only original signed runtime or exactly the separately staged Group #1 \`home-choice\` runtime**, then adds the Group #3 guarded \`option-b\` action while preserving both original and Group #1 actions. Test commit \`7628081245ff165828a52c1432b4547a317bc773\` verifies coexistence. **GitHub run 39270553998 26/26 PASS**, no skips; no actual Android build or combined APK.

## All-in-one phase must NOT be called green yet

The user's latest wording was conditional: **“if everything's complete, it's time to go to all-in-one phase.”** We may record a preparation/readiness audit; this is **not** unconditional authorization to ship an unverified APK or claim all requested fixes completed.

1. Group #1 source checkpoint **accepted**; #19 Movies↔TV reloading explicitly **DEFERRED/UNFIXED** until matched Fold replay/in-app diagnostics. Never invent #19 change or relabel it fixed.
2. Group #2 source-stage host 20/20 pass; scoped native source still **not rebuilt into the final Android engine**.
3. Group #3 signed source+isolated C++ peers and now 26/26 host green; exact poster hold still **not built into final Android engine**.
4. Group #4 source green, actual player XML/native Video Settings semantics and device visual acceptance not yet tested.
5. Group #5 exact crash-recorder fingerprint correction **source green**, but physical SIGSEGV/139 itself **still lacks causal stack; no root-cause fix exists**. A diagnostic candidate with that known open fault cannot be labeled crash repaired.
6. Group #6 source green; native notification rendering suppressor still **uncompiled/unverified**; real interactive script error dialogs not automatically suppressed and must be reported if observed.
7. Final Group #7 must integrate native patches on a **source-matched reconstructed 2103390 engine**, compile \`libkodi.so\`, merge narrowly scoped skin/preimage fixes, enforce exact signed payload diff and unchanged Cobra/Essential-First/skin/addon/user-data, permanent signing and Android tests. Physical user's Fold tests, user explicit **LOCK**, and all unresolved/accepted-deferral labels remain separate gates. **NO COMBINED APK YET.**

**Source-stage tests are evidence, not APK readiness or physical success.** Preserve all tested commits and known red items; do not roll back, regress or reimplement previously green unrelated features.
