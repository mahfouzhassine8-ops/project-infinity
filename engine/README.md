# Infinity Engine 1.0 — Foundation

This branch starts the source-built Infinity engine from upstream Kodi 21.2 Omega.

Ground rules:
- Upstream source is pinned to Kodi tag `21.2-Omega` / commit `d1a1d48c3cb3722d39264ffdd8132f755ffecd27`.
- The original working Stable 2 APK remains archived as the legacy reference and is not modified here.
- Engine 1.0 makes no PiP, Fold, renderer, UI, or Python behavior changes. Its only goal is to build stock Kodi 21.2 for Android arm64 from source.
- Every later Infinity change must land one layer at a time and keep the previous verified checkpoint available.

Milestones:
1.0 Foundation — clean stock Kodi 21.2 source build.
1.1 Fold/window lifecycle — native display/fold resize handling.
1.2 Native conditional PiP — Android-side PiP controlled directly by player state.
1.3 Renderer/PiP viewport — native small-window resize path; remove the sliver problem properly.
1.4 Native player controls — real PiP toggle and other Fold controls in Kodi UI source.
1.5 Python/runtime integration — intentional Python environment changes after the core runtime is stable.
