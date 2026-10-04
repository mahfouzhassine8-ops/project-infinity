# Skin 196 physical test gate — pending

Use APK 2103305 with Infinity skin 1.0.5.196 and Command Center 0.3.5.20.
Keep the locked 195 ZIP and existing add-on/user configuration for rollback.
No device test is represented as completed by the source-contract workflow.

For each combination below, repeat the drawer and preservation checks in
light, dark and OLED modes, with Android keyboard closed and open where the
underlying screen permits it:

- Cover portrait and cover landscape.
- Unfolded square, inner portrait and inner landscape.
- Split screen, pop-up window and live shrink/grow resize.
- Cold and warm launch; background/foreground.
- With and without active playback.
- Exit/immediate relaunch and exit/delayed relaunch. Native shutdown is still
  an open gate; this skin does not change the engine teardown policy.

## Drawer checks

1. Before touching it, the collapsed capsule is not a white filled button.
   The logo and hamburger retain their proportions and separation from the
   header. Tap/remote focus shows only the approved cyan outline treatment.
2. Open the drawer. It remains anchored top-left, without shifting the home
   layout. Where vertical room permits, Power is the last initial row and
   Explore is not already exposed beneath it. Short landscape/pop-up windows
   retain readable rows with scrolling rather than tiny targets.
3. Scroll down to Explore and every later entry, then back up. No destination
   is removed and rows stay touchable throughout.
4. Tap UI Theme immediately above Power: it opens Interface Settings, not
   Performance & refresh. Scroll to Performance & refresh: that still opens
   its original performance panel. Test each repeatedly after dismissal,
   navigation, fold, rotation and resize. Focus must not highlight both rows.
5. Tap all visible parts of Power. The Power menu must open once. Close Kodi
   and Force Close remain separate explicit choices; normal exit is not
   silently changed to Force Close. Capture Health Center if shutdown stalls.
6. Movies opens Infinity Movies and TV Shows opens Infinity TV. Back returns
   one layer at a time with no generic empty Videos hub or route crossover.
7. X and Android Back dismiss the drawer and restore home touch immediately.

## Preservation checks

- Confirm the 12-button horizontal player rail, vertical volume mode,
  percentage, inactivity dismissal, scrubber ownership and repeat state are
  unchanged from installed 195. Playback must not pause during drawer checks.
- Confirm weather snapshots, add-ons/providers, Resume Hub, artwork, settings,
  theme switching and Android IME remain intact.
- Do not use changed movie-video framing as an acceptance criterion; that
  issue is explicitly deferred and not modified.

## Remaining ownership evidence to collect

For the source/resolver freeze and idle takeover, record installed add-on
version, current Kodi window/dialog, geometry, timestamps and relevant Kodi /
Health Center logs. A screenshot alone does not identify native crash ownership.
The upstream Umbrella files were located, but neither that freeze nor the
idle takeover is fixed or device-accepted by skin 196.
