# Cobra 2103160 — Visual Theme Runtime v2 candidate

## Status and immutable baseline

This is a TEST CANDIDATE, not an official or visually accepted final release.
Baseline: locked 2103159 run 10, commit `257a49d742890acf0c7d3e0220bded5a8aa80c57`.
The baseline branch, APK, native engine and historical recipes are not edited.
The later run 11 chooser text-padding fix is carried forward in the new candidate;
its source preimage remains exactly run 10. No locked reference is moved.

The workflow must reconstruct and compare every baseline source receipt, and
preserve the exact 2103159 APK, matching UI 1.4.0, receipts, repository snapshot,
generated Android source and native patch BEFORE applying the new delta.
Device userdata is NOT backed up. Do not uninstall or clear app data to force a
downgrade; Android may reject a lower versionCode. Theme rollback is separate
from installed-APK rollback.

## What the implementation adds

- Actual local raster assets for Cobra's internal combined badge, menu/action
  icons, drawer ribbon/footer, chooser background/card emblems/footer, and
  image-backed component surfaces. This is not a color-only JSON package.
- Shared styles and 822 explicitly catalogued visual resource sites covering
  copy, colors, bounded sizes, typography, image fill, focus/pressed/selected
  surfaces and supported animation durations. Unknown tokens fail validation.
- Existing-view geometry controls: dimensions, margins, padding, weights,
  orientation, gravity, opacity and text line limits. Custom List/Grid/Table
  LayoutParams are not downcast or replaced by the generic geometry adapter.
- Declarative chooser scenes made of raster art, native text, and four mandatory
  native action slots: enter Infinity/Cobra and their settings. The ZIP cannot
  specify intents/classes/URLs/executable handlers. Native action targets may
  not overlap; undersized targets fall back before any native view is attached.
- Seven-region layouts for each of the five existing guide modes. An override
  must retain usable toolbar, video and browser regions and avoid overlap;
  otherwise the original geometry is retained atomically. This resizes existing
  containers; it does not create, prepare or reparent a video player.
- Independent Light/Dark/OLED and cover/portrait/landscape/tablet/TV overrides.
  Missing values use native defaults. System font families and optional valid
  user-supplied TTF/OTF are supported; this source/package bundles no font files.

The source-site catalog is not a promise that arbitrary new app functionality,
new Android screens, or literally every possible visual transformation can be
injected by data. Functional actions, native rendering, provider/player ownership,
permissions, identity, signer, background/resume, and Kodi/Infinity skin are not
ZIP-owned. Actual coverage and visual equivalence require rendered evidence.

## Package safety and persistence

The existing Cobra UI picker recognizes a separate data-only visual ZIP format:
`script.infinity.cobra.theme/resources/visual-theme.json` plus declared assets.
A v2 visual ZIP must not contain addon Python, Java, executable code or unlisted
files. Legacy UI ZIPs continue through the established legacy installation path.

The loader enforces canonical local paths, duplicate/case-collision rejection,
entry count and compressed/decompressed budgets, manifest schema and runtime,
asset SHA-256, supported image/font types, bounded dimensions and decoded-image
budget. It performs decoding on a serial worker, never in onDraw. Active and
previous content-addressed private generations use an AtomicFile pointer.
Failed validation cannot replace the active snapshot. Reset and rollback preserve
playlists and playback preferences. Native Settings includes an intentionally
unthemed reset/previous control; the drawer header also opens it on long press.

TextureView, SurfaceView and WebView are excluded from generic style traversal.
Existing click handlers, tags, accessibility descriptions and dialog on-show
callbacks are retained. No theme controls playback, network, decoder or native
library operations. Changes that require rebuilt menu geometry/copy take effect
when those menus reopen rather than restarting playback.

## Tests and delivery gates

Local source and Java policy recheck: 63 source guards and 24 executable archive/
path/read assertions passed. This includes exact preimages, reapplication refusal,
protected static/EPG/player policy comparisons and reversible visual substitutions.
Java syntax parsing is not a substitute for Android compilation.

CI requires actual Android compilation and permanent signing; byte-identical
native, asset and Android resource payloads relative to locked 2103159; and
release DEX checks. It retains all 19 inherited Android cases and adds 17 package/
bitmap/storage/style tests plus 10 scene/geometry/native-action tests. Failed or
skipped tests cannot count as delivery acceptance. Inherited guide and playback/
layout algorithms run on the generated source. Audit evidence and exact rollback
are preserved even when a later gate fails; an unaccepted APK is not published.

The new Android cases exercise corrupt/future/executable packages, retained
snapshots, true custom-badge pixels in the production CobraBrandMark, native
clicks/tags/accessibility, image/font mismatch, protected video views, guide/player
identity, unthemed recovery controls, dialog callbacks, custom chooser native
routing/settings, atomic guide geometry, layout restoration and run 11 padding.
They use Robolectric Android native graphics and fixtures, not hardware playback.

## Remaining acceptance

The two user-approved master images remain the visual targets: cinematic gold/
blue Infinity-Cobra chooser with HM identity, and the light frosted Cobra drawer
with a combined badge and ribbon. The final artwork ZIP must be installed into
this runtime in the Android tests and rendered at phone/Fold/landscape/TV sizes
before it is described as photo-equivalent. No screenshot-only UI facade may
replace real controls, guide content or player surfaces.

Physical-device update install, provider video/audio, actual surface recovery,
all five modes, PiP/background/rotation/Fold, touch/D-pad and user visual approval
remain separate checks. The workflow must not mark these passed merely because
compilation or host tests passed. No automatic official release or baseline lock.
