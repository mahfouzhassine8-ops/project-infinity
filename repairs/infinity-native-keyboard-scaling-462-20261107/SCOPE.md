# Native keyboard/scaling engineering scope — 2026-11-07

Protected correction checkpoint: 86d5b5e2b65acb878632d407c3a3a07dd1af3b6d. Separate Search candidate 72fefa8fe2554eb3fa7181027d6b9b2f05d7dd75 is not merged or modified. Installed reference is APK2103462 / skin268 / Command Center0.3.5.61.

Allowed native runtime candidate: Android-only keyboard-modal ownership in xbmc/guilib/GUIKeyboardFactory.cpp, prepared under this folder's native/ tree. Restore exact compiled APK462 sources before applying; exactly one native file may differ. Reentrant input/filter requests return false before replacing editor/filter state; normal cancellation and worker drain remain unchanged.

Selected checks: source-map binding against all9411 APK462 native inputs; before/after host ASan using the actual pinned keyboard method bodies; selected real Android ARM64 keyboard translation-unit compilation with the original toolchain; NDK libc++ symbol reconciliation; bounded host ThreadSanitizer probe of pinned graphics origin/scaling methods; read-only graphics dispatch/payload/checkpoint dependency tracing. Host platform boundaries and unavailable Android/Fold results must be stated.

Read-only graphics work must not be represented as a repaired device crash. No speculative locks, origin-stack resets, or gesture-mask substitutions. No checkpoint/durability or settings-retirement changes.

Execution infrastructure changes are confined to this folder and branch-specific read-only/compile jobs in the existing controlled-native workflow. Its original native build job remains unchanged; permissions are contents:read/actions:read. No signing keys, release authorities, APKs, installations, shutdown suites, user data, Cobra, Preview or provider modifications.

No complete engine link, APK packaging, signing, installation, promotion or lock has been performed. Release remains held for graphics safety, shared Search consistency, combined integration and Android verification.
