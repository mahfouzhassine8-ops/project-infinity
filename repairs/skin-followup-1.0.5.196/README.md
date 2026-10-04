# Infinity skin 1.0.5.196 — Drawer Follow-up RC1

This is a separate, unlocked skin candidate over the exact user-supplied locked
1.0.5.195 ZIP. APK 2103304 and skin 195 remain the locked rollback checkpoint.
Use APK 2103305 for its already-built conditional Power-route installer repair;
that APK does not establish native shutdown-hang resolution.

## Actual changes

- `unified/Home.xml`: the hamburger's focus texture is the approved cyan rim,
  not a filled field. Resting uses an existing genuinely transparent texture.
  Its geometry, logo, menu icon, actions and focus-return behavior are retained.
- `unified/Custom_1198_InfinityNav.xml`: cap the expanded panel at 1050 logical
  units instead of 1120. With the existing 132-unit header inset, 18-unit bottom
  inset, and 900 units of rows through Power, Explore starts below the initial
  viewport. In shorter windows, full-size rows remain reachable by scrolling.
  The top-anchored contraction ratio is updated to the new maximum height.
- The newly added UI Theme button is `1198310`, with the same focus marker.
  Skin 195 incorrectly reused `1198305`, which already belongs to Performance
  & refresh. That legacy button retains its ID and destination. Both rows now
  have unique IDs; all routes and row order are retained.
- Only those two XML files and the three release/integrity metadata files
  change in the complete ZIP. All other files are byte-identical to 195.

The player, volume mode, repeat actions, artwork, providers, Python observers,
weather bridge, add-on configuration and disabled native profile marker are
not changed. The internal ID stays `skin.infinity.diggz`. The visible name is
Infinity. Deferred movie-video framing is not changed.

## Reproduction and acceptance boundaries

Required full baseline SHA-256:

`c5290ee4352ba8b0b60af9222b4e7b032c40c2d1ccef4d1a4387699f9a5c83f9`

```sh
python3 -m pip install lxml Pillow
python3 repairs/skin-followup-1.0.5.196/test_delta.py
python3 repairs/skin-followup-1.0.5.196/package_skin.py \
  --baseline /absolute/path/skin.infinity.diggz-1.0.5.195-Responsive-Repair-RC1.zip \
  --output-dir /absolute/path/new-candidate196
```

The package command requires the complete original ZIP, refuses an incorrect
baseline or existing output ZIP, validates protected hashes and every XML,
runs the 19 new drawer contracts and all eight preserved source contracts,
checks the actual alpha of the existing focus/rest textures, and verifies every
file through final archive readback. Preservation counts are in
`package-proof.json`. The copied eight-test suite changes only the erroneous
UI Theme ID expectation and strengthens uniqueness and exact hub-route checks.
It does not delete inherited assertions or change the original repair tests.

The GitHub workflow deliberately runs **fixture/source contracts only** and
produces **no APK and no complete skin ZIP**. Its three immutable XML fixtures
come from the exact supplied 195 archive. The complete archive was checked
locally; a workflow green check is not full-bundle or device acceptance.
The XML geometry model covers portrait, landscape, square, short/pop-up bounds
and a resize sequence. It does not emulate Kodi rendering, Android touch or
native fold callbacks. Theme tests inspect light/dark/OLED variable branches;
they are not screenshots from the user's phone.

## Still open — not claimed fixed

- Native graceful Close Kodi completion, immediate/delayed relaunch, shutdown
  stalls and the historical native crash cluster.
- Umbrella source/resolver sizing, cancellation and native Android Back freeze.
- The idle movie/screensaver takeover; exact installed owner and active window
  must be established before changing decoding, timers or user configuration.
- Other settings/dialog refinements and full physical validation matrix.

## Umbrella ownership audit

Read-only upstream audit pinned to
`umbrellaplug/umbrellaplug.github.io` commit
`3baead15cc75e6a17a708e1a4f884342d2e58295` (2026-09-25).
This is not evidence of the installed Umbrella version.

The source list belongs to:

`matrix/plugin.video.umbrella/resources/skins/Default/1080i/source_results.xml`

Its controller is:

`matrix/plugin.video.umbrella/resources/lib/windows/source_results.py`

The scraper/resolver progress presentation belongs to:

`matrix/plugin.video.umbrella/resources/skins/Default/1080i/source_progress.xml`

Its controller is:

`matrix/plugin.video.umbrella/resources/lib/windows/source_progress.py`

They inherit `BaseDialog(WindowXMLDialog)` from
`resources/lib/windows/base.py`; source list control ID is 2000 and progress
text control ID is 2001. The upstream XML uses fixed desktop geometry, including
a 1920x1080 progress background. These files are absent from the complete skin
195 ZIP. Editing `DialogMediaSource.xml` or `DialogSelect.xml` alone cannot
establish that Umbrella's own windows are repaired. No provider/add-on files
or credentials are substituted by this skin candidate. A generic native or
version-guarded integration fix still needs the installed/runtime contract.

## Installation

Install the 196 ZIP as a Kodi add-on upgrade over Infinity 195. Do not install
it as an Android application, rename the skin ID, reset the add-ons, clear app
data or replace providers. Keep the exact 195 ZIP for rollback. See
`DEVICE-TEST.md` for the checks required before locking this candidate.
