# Cobra 2103157 — TV Grid, drawer-return video and independent system-dark palette

## Exact starting point and scope

Parent: passing diagnostics candidate 2103156, commit
`b3bcb619b08205dcfc1451424b2d41e05fd37633`, run 35192605567.
Its APK SHA-256 is `fa13db18df0555f0148e7cc935b61d8e45284183c3424829f8c487935d66fe33`.
The user-locked 2103155 branch/commit `4d1ed032df7e13fd27cc2170fc5e028f5059ec32`
is not changed. 2103157 is an UNLOCKED TEST CANDIDATE.

This patch only edits the generated Cobra Activity and Android version metadata.
Cobra's EPG repair and diagnostics exporter are retained. Kodi native code,
assets/skin/Cinema mode, decoder choice, stream URLs, ExoPlayer creation,
recording/Infinity handoff and background/resume policy are not modified.
A complete pre-change APK/UI/source/receipt rollback is prepared before mutation.
Device userdata is not backed up by GitHub Actions.

## Reproduced navigation defects

1. `stopCobraPreview` discarded the guide/TextureView but retained the previous
   measured dimensions and layout record. The next guide inserted its panels at
   1x1 and, at the SAME viewport dimensions, its layout listener could skip the
   first real layout. Fix: invalidate the old size/layout stamps when disposing
   and creating a shell; a new shell must calculate its own measured bounds.
   The listener also rejects callbacks from a no-longer-current shell.
2. A delayed `showVodLibrary` Movies/Shows callback could call `renderVodItems`
   and clear Live TV after the user had returned. Fix: navigation generations
   checked on the main thread when results are delivered. Series-detail responses
   and episode choices are similarly rejected when their route is obsolete.
3. A delayed drawer translation could leave the restored stage shifted. The Live
   TV entry restores zero translation when no experience drawer owns that shift.

Host reproduction executes the actual original and repaired stop methods and
shows the old same-size layout trigger is false and the repaired one is true.
The actual publication helper is executed with a deliberately delayed UI queue.
The Android gate drives real drawer click handlers and actual Android layouts,
including delayed Movies/Shows completion AFTER Live TV returns. It does not
force-call `cobraLayoutGuide`, which would hide the regression.

IMPORTANT: the existing Movies/Shows drawer path disposes its preview player.
This repair preserves that policy; returning Live TV can restart its preview.
It does NOT claim continuous same-player identity across Movies. Switching the
five live VIEW MODES still retains the existing TextureView. No physical provider
stream or decoder has been tested here, and these repairs are not proof that
EVERY possible audio-only/black-screen failure has been eliminated.

## TV Grid workspace

Live TV now opens channel rows and time-aligned programmes immediately, not a
page consisting only of groups. The timeline occupies the primary remaining
viewport. Portrait uses a width-filling preview and compact programme information
above the grid. Wider viewports use preview/information side by side, with a
collapsible group column and, at large widths, a compact navigation rail.
Narrow viewports open groups/playlists in a contextual side overlay above the
guide; they do not replace the timeline or recreate its video texture.

Group/playlist changes reset incompatible group filters, preserve the main guide,
and keep explicit Back/close behavior. Time ruler, now-line, channel column,
programme actions, search and five independent mode renderers remain available.
Screen dimensions are measured from the usable window, not inferred from the
screenshot or a fixed device orientation. Other four mode geometry branches and
row renderer classes are unchanged.

The broadcast-guide information architecture is inspired by TiviMate's official
screenshots; no TiviMate code, branding or artwork is copied. Native Android test
screenshots are evidence of this implementation, not mockups or provider playback.

## Follow System dark preference

Cobra Settings -> Appearance -> System dark palette -> Dark / True OLED Black.

The selected variant is persisted independently in `cobra_system_dark_variant`.
Follow System + system Light = Light. Follow System + system Dark = the selected
Dark or OLED palette. Manual Light/Dark/OLED selections retain their explicit
meaning and do not erase the stored system-dark preference. Reloading the UI or
relaunching does not reset that preference. No existing preference is migrated or
overwritten merely by installing this APK. Missing preference defaults to Dark.

Configuration changes while in Settings retain Settings instead of forcing the
user to Live TV. Active playback isn't torn down to apply a preference. The fresh
diagnostics snapshot now also reports effective palette and preview view bounds,
attachment and texture availability, so a remaining real-device surface problem
has observable evidence.

## Verification and packaging gates

Local executable tests before push:
- Original before/after same-size reset regression reproduced.
- Actual delayed navigation publication rejects old responses and retains current ones.
- 2,773 new production geometry/palette/navigation policy assertions.
- Entire old layout assertion body rerun on the new production policy: 12,171
  assertions (the count changes with the number of visible panes, not removed assertions).
- 66 guide and 9 short-guide cases pass on the final patched Activity.
- 42,339 inherited guide/layout/player-state algorithm assertions pass.
- 369 untargeted Activity methods and non-targeted player/renderer classes preserved.

CI repeats exact 2103156 reconstruction and all its source receipt checks, prior
79 executable diagnostics checks and structural guards, new host tests, final EPG
and inherited tests. Android-only compilation/signing keeps permanent signer,
resource-ID, JNI and native/asset integrity gates intact.

The signed candidate is uploaded ONLY AFTER the new four-test Android gate passes:
- Live TV -> Movies/Shows/Recordings/My List/Settings -> Live TV at the same size;
  old Movies/Shows work delivered after return must not overwrite live views.
- Portrait, Fold-sized and landscape guide/group behavior and all five modes.
- Real appearance picker actions, independent persisted OLED preference and
  Light/Dark configuration transitions including large text.
- 12,000-channel list virtualization.

The Android test uses Robolectric native graphics and real production view code,
with fixture guide data and a queued executor. It does not run app startup, login,
network-provider transport, physical GPU decoding or operating-system lifecycle
acceptance. Its source states these boundaries explicitly. Passing compilation,
starting tests, or merely producing screenshots are not counted as a passing gate.
Reports/screenshots and rollback are uploaded even when an earlier gate fails.
The artifact ACCEPTANCE.json reports which gates actually completed.

## Device acceptance and rollback

Install `Infinity-1.0.9-Cobra-TV-Navigation-Appearance-RC1.apk` as an update over
Infinity, without uninstalling or clearing data. The accompanying UI ZIP remains
the exact previously matched 1.3.9; it is not a replacement for the APK.

Verify picture and audio on a real channel, visit Movies, and return via Live TV.
Repeat through Shows/Settings and across orientation/Fold transitions. Check that
the guide spans the available viewport and groups do not replace it. Select
Follow System + True OLED Black and test system light/dark switching and relaunch.
If video is still absent, export diagnostics while it is occurring; real provider,
video texture/decoder, app background and installed-device acceptance remain open.

Rollback artifact: `Cobra-2103155-2103156-Complete-Rollback-For-2103157` includes the
exact prior APK, UI, full source archives, generated Android source and receipts,
plus the retained locked 2103155 rollback. Android may refuse a lower versionCode.
Do not uninstall/clear app data to force downgrade without a separate device-data
backup and reviewed rollback/update path. This workflow does not merge, release,
install or lock the candidate.


## Measurement-ownership repair after the failed Android gate

Runs 35196712386 and 35198082026 passed Android compilation/signing but failed all
four Android view cases. Read-only geometry instrumentation in run 35199155394
reproduced the unchanged failure: the shell was 412x915 and its solved preview box
and LayoutParams were 412x231, while the preview AND TextureView were still
measured/laid out at 1x1. The browser similarly had 412x550 LayoutParams but 1x1
actual bounds. Landscape and smaller portrait cases showed the same mismatch.
The shell's layout request was clear while its children still needed layout.

The earlier deferred callback checked only the shell-size stamp and therefore
could skip work even though its children had never consumed their new parameters.
The replacement makes the guide FrameLayout own this phase: solve changed shell
geometry, rebuild the guide if necessary, measure its visible direct children
against their assigned parameters, and only then let FrameLayout position them.
The late layout listener and deferred timing workaround are removed. Stale-shell
callbacks cannot mutate the current shell. No player/decoder/surface ownership,
EPG algorithms, other mode geometry, native bytes or signing gates are changed.

All four original Android cases and their assertions remain. Additional guards
require a correctly sized preview in the FIRST traversal, before clock advances,
and equality between assigned, measured, laid-out and TextureView bounds. This is
stricter than waiting six frames for the original size check. Upload remains
blocked until the full Android suite and existing packaging/rollback gates pass.
Read-only view-tree evidence remains in the test reports. Device playback and
final visual acceptance remain separate and unverified; 2103157 is not locked.
