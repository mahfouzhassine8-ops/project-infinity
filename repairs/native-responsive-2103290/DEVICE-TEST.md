# Infinity 2103290 — Native Responsive Layout RC1

## Purpose

Move resize ownership into Kodi while keeping the skin responsible for presentation.

The Android current usable window is authoritative. Kodi creates a logical GUI canvas whose short
axis is always 1080 units and whose aspect matches the current usable window. This prevents the
legacy independent X/Y stretch. A skin opts in with
`resources/infinity-native-responsive-v1.json` and supplies complete presentation files under
`responsive/<class>/`.

Infinity skin 1.0.5.181 is the matching presentation package. It preserves the complete 1.0.5.178
legacy profile tree for rollback and adds full responsive coverage for every XML window.

## Preservation

- Parent Android/data baseline: 2103288 Evidence-First Health.
- Parent native stability: 2103285 FD repair.
- No uninstall, data clear, Start Fresh, account reset, provider reset or database migration.
- Existing playback, PiP, background, Python hardening and FD polling repairs are preserved.
- 2103286 and the rejected 2103287 profile-reload design are not parents.

## Install

1. Install the 2103290 APK directly over Infinity.
2. Install Infinity skin 1.0.5.181 over the current skin.
3. Do **not** uninstall or clear data.

Either order is safe: the APK ignores the responsive path until the skin marker exists; older APKs
ignore the new responsive tree and continue to use the preserved legacy profile matrix.

## Physical Fold acceptance

Exercise the same active screen through:
- inner display portrait
- inner display landscape left/right
- close to cover display
- reopen
- split-screen / resized window
- Movies / TV browse
- Settings
- Home/drawer
- video OSD and return from playback

Expected:
- content/focus stays on the same logical screen;
- no 16:9 fallback takeover;
- no stretched/fat/thin controls from independent X/Y scaling;
- no giant-card chooser redesign;
- no hidden long-press theme menu;
- Kodi log shows `Infinity responsive viewport:` and `Infinity responsive window:`.

Health Center Responsive/Fold Trace now records the installed skin version and whether the native
responsive marker is present. Physical Galaxy Fold acceptance remains required before lock.
