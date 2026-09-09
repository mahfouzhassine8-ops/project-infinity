# Infinity current hook/theme audit — 2026-09-09

Status: staged correction, NOT a new APK release. Base commit:
`b4ecc843c968c733da1c5d9fe142f5dd4f2a0289`. The production branch, installed app,
signing material and native engine have not been modified by this audit branch.

## Inputs

1.0.5 run `34407851662`, artifact `10126049075`, APK SHA-256
`611eb282b2b095acc0341af3ee46fdedd9a97b104b449a8f41df480bd9d8c683`.
Frozen RC3 run `34316336433`, artifact `10091780358`, APK SHA-256
`737511cc666a541939714b4a5e43b7fe3a013614936500dd74a5a5530f860d84`.
Local comparison found all 45 native libraries and classes.dex byte-identical.
The APK manifest still has package com.projectinfinity.kodi, versionCode 2103100
and versionName 21.3-Infinity-Android-First. The 1.0.5 filename is not a newly
assigned Android version code; correct version progression is a release gate.

## Important correction: current v4 already drives skin theme facts

The September 8 G2 #6 audit described an older binary. Current RC3/1.0.5 uses
`patches/infinity-7.1-audited/source.patch` and contract version 4:

Main lifecycle/layout -> InfinityCoreBridge.publishWindow -> Java snapshot ->
_infinitySyncDisplayState -> CXBMCApp::InfinitySyncDisplayState -> queued
CInfinityBridgeState -> CWinSystemAndroid::ApplyInfinityGeometry -> Home properties.

The render-thread consumer sets Infinity.SystemTheme, Infinity.DeviceMode,
Infinity.BridgeVersion and Infinity.ThemeRevision. Current InfinityColor_*
variables already consume the theme property and manual/system policy.
A second bridge, polling loop or forced skin reload is not needed.

Caution: the native equal-size geometry fast path commits the snapshot but does
not republish the Home CommittedWidth/Height properties. The staged presentation
uses actual GUI dimensions updated by the hook, not those potentially stale
properties. Source/binary correspondence is not a substitute for fresh device logs.

## Reproduced defects and staged corrections

1. The light expression's manual-light OR arm was not grouped before combining
   orientation constraints. Under manual light, a logic reproduction selects
   THREE sidebar logo controls and TWO hero image controls simultaneously.
   This proves a condition defect, not which policy was selected in a screenshot.
   The proposed named expressions centralize the existing hook-driven policy.
   Square mobile windows, previously matching neither orientation, also receive
   one body variant rather than none.
2. The 1.0.5 paragraph patch narrowed width to 700 without centering its control
   or increasing max auto-height 300. Kodi grouplist additionally resets child
   positions unless usecontrolcoords is enabled. The correction enables that
   option, sets centerleft 50%, uses widths 760/930/790 for normal/compact/portrait,
   permits auto-height up to 550, and leaves font definitions and localized text
   unchanged. The buttons remain in the same vertical flow.
3. The supplied screenshot shows a blue-on-blue focus state. Its precise runtime
   caching cause is not established. To couple foreground and background policy,
   the staged menu has mutually exclusive light/dark groups driven by the SAME
   hook-derived expression, with fixed matching colors inside each group.
   Light: pale E1F1FF / dark-blue 0755A5; dark: 096DCF / white. Calculated opaque
   contrast ratios are approximately 6.39:1 and 5.12:1. This is not accessibility
   certification or rendered verification. The grey lists/focus.png texture was
   decoded from XBTF; neutral colors/white.png avoids multiplying the desired
   color by grey. Introduced white.png paths did not exist and are corrected.

## Startup has separate Android and native stages

The compiled Android loading layout is res/Sp.xml (0x7f070001). Its ImageView
ALREADY uses FIT_CENTER (scaleType 3), 48dp padding and project_infinity_icon
(0x7f040012 -> res/zp.png). The previously replaced res/85.png belongs to a
DIFFERENT drawable, applaunch_screen; res/KE.png is another variant. Therefore
blaming the current Android ImageView's centerCrop was incorrect.

The native startup stage uses the bundled splash. Pinned Kodi commit
`a3a448d26b8d560a65655dab2cd122994dc4e146` contains AR_SCALE (fill/crop) in BOTH:
- xbmc/rendering/RenderSystem.cpp, CRenderSystemBase::ShowSplash
- xbmc/windows/GUIWindowSplash.cpp, CGUIWindowSplash::OnInitWindow

A proper native correction must address both startup paths with contain/AR_KEEP,
current bounds and a bounded startup composition. Android loading should reference
the intended startup resource rather than implicitly reuse launcher artwork.
Existing user overrides must not be overwritten silently.

Changing these native methods changes libkodi.so. It cannot honestly be described
as an unchanged-engine image-only patch. This is targeted startup work on the same
Kodi foundation, not a reason to redesign codecs, playback, PiP or the v4 hook.
No native splash fix or native rebuild is claimed by the staged XML overlay.

## Delivered code and test limits

scripts/infinity_theme_contract.py accepts only the pinned 1.0.5 APK hash and
exports exactly four XML files plus an honest staging receipt. It never signs or
produces an APK. Font.xml, artwork, hero image dimensions, player/lock XML, Java,
native libraries and user data are excluded. Correcting visibility can move the
overall group, so unchanged center-image assets do not promise identical placement.

tests/test_infinity_theme_contract.py has eight locally passing tests, including
270 policy/theme/device/window combinations, old-defect reproductions, idempotence,
paired colors and coordinate checks. It also estimates the supplied English
paragraph's height using the APK's existing font. These tests are NOT an Android
or Kodi renderer, full translation tests, or proof of on-device visual correctness.

## Release gates

Prepare/compile the narrowly scoped native startup change with matching Java,
resources and v4 contract. Verify package/version progression and the existing
public signer certificate. Test the exact signed candidate on Fold cover/inner,
portrait/landscape, manual/system light/dark, startup, playback, PiP and lock/resume.
Do not call a packaging green check a completed visual fix.

Primary code references: the pinned repository contract/source.patch above;
Kodi GUIControlGroupList.cpp AddControl; GUIControlFactory.cpp;
guilib/guiinfo/GUIInfoColor.cpp; RenderSystem.cpp; GUIWindowSplash.cpp.
Dynamic texture color variables ARE supported by the pinned Kodi source.
