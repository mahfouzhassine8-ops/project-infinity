# NON-NEGOTIABLE PRESERVATION GATE — Cobra Cards drawer-only fix from signed 2103435

**User instruction, Oct 31, 2026:** "Make sure everything else is preserved."

**This preservation contract supersedes any expansive interpretation** of the companion diagnosis
`CARDS-DRAWER-INNER-DISPLAY-RESIZE-20728-20729-20261031.md`.
It is a binding scope constraint for the NEXT *Cobra-only* engineering attempt, not a claim that a fix exists or that code has been changed.

## Frozen source of truth

- **User-approved 2103435 is the baseline**; source commit `e0c6153588992001d84076d33fdf8f0d676c0d00`.
- Exact lock branch: `lock/infinity-cobra-2103435-user-approved-20261031`; must never be advanced, rebased or overwritten.
- Original signed APK SHA256 `dc83faed4a8eb1d2e2e116914cf15f2f1c27cc2a8653813fd6701ba300234442`, GitHub original-key signing run `41125367621`, archive artifact `13011191050`; original signer certificate SHA256 `d7adeb68e9341596a02bd3262b737a0f45fc6e771ed7e60285437e833b58c6d7`.
- Original matching ZIP hashes: Infinity `a99e7bb789a0817fdfc9cc10b4e1649d52a2c78f0e3375f0735c55f4a91a0336`; Cobra `e67dd28dab95206dcda8cb88903828453da57670468c532a32cd1db077663893`; Minimal Android `432bfb7b246a504d9550e1de39368c3b7e0946532f1c695531ed891e74ef03d8`; Chooser Shell `30589df7f2459a133b8fdd34f0bc56f8a5dc363d4f36accbb523a7ae47185f14`.
- Prior accepted/recovery 2103427, 2103431, 2103432, 2103433, and rejected 2103434 remain available, unaltered. Never overwrite signed 435.

## Allowlist — the ONLY approved functional difference

**Existing Cobra Cards navigation drawer opening/closing / drawer-open fold-unfold window geometry.** Fix the observed unwanted inner-display Cards-page shrink/reflow/shift during drawer animation, without altering any other visual design or action. Correct only demonstrably necessary methods/resources in the actual active Cobra Cards drawer/geometry path. Preserve drawer slide/dim/navigation behavior. Keep Cards at stable full usable inner width *behind* the drawer except on a genuine Fold/window-configuration change. For a genuine configuration change, adapt to that actual display, not a temporary animated drawer width.

**The user has NOT authorized** a redesign, a global responsive-layout rewrite, a new Compact mode, any new loading feature, extra controls, or an unrelated workaround. If source ownership requires changing a shared class, isolate the change behind a proven Cards+drawer+inner-state guard and show **negative-control proof** for every consumer. If isolation is unproven, STOP; report blocker rather than relaxing preservation.

## Absolute freeze: Infinity and the combined host

1. **Infinity unchanged** — Kodi engine and native libraries, skin and all responsive variants, Infinity Command Center, loading animations already present in approved 435, service/python code, providers/addons, authorization, bookmarks/Continue Playing, health, power/shutdown and chooser-to-Infinity behavior. No Infinity bug fix, clean-up, reformat, resource repack, or migration.
2. **All shared / minimal Android components unchanged** — JNI/47 native libs, package ID, permissions, signing certificate, launcher icons/themes, startup, power/Essential-First shutdown, PiP/background routing and global multiwindow interfaces. No global Android window flags/configuration workaround unless separately approved.
3. **Chooser unchanged** in appearance/navigation, choices, theming, icon, animations, labels, persisted selection. The only possible necessary differences in a successor install-over APK are transparent/required new version metadata and manifest versionCode. Do not claim the *entire combined APK* is byte-identical if versioning necessarily changes. Instead prove exact unchanged **functional contents** and document metadata-only differences.

## Absolute freeze: Cobra outside this one Cards drawer defect

1. **ALL other view modes unchanged** — Mobile, Compact, TV Grid, Pro, Pro Sports, Sports pane and Multi-View; no shared styling changes, control reorder, EPG logic changes, playback handoff changes, or settings changes.
2. **Front/cover Cards visual and behavior unchanged** — exact two-column geometry, header/video/Now Playing/toolbar, logos, fonts, gaps, cyan focus/playing dots and progress; no new resize behavior while opening drawer on the front screen. Where the drawer is opened on cover then phone unfolds, only legitimate display change should reflow to inner.
3. **Inner Cards when drawer CLOSED unchanged** — currently approved 4-column layout with accessibility fallbacks, tile dimensions, thumbnails, EPG/detail panel, controls, color themes, selection and scroll. ONLY eliminate the transient abnormal shrink/offset linked to drawer animation. No permanent shrink, layout density changes, or new design.
4. **Every interaction unchanged** — all channel-card buttons, fullscreen player More/sun menu, Quick Peek, touch/long press, menu back/close, focus/DPAD, search, Favorites/Channel Wall, channel switching, Sports, recording, stats, settings.
5. **Video/playback continuity unchanged** — exact playing channel/session/mute/audio/subtitles, decoder and Surface/Texture ownership, no player recreation or restart, PiP/fullscreen return, ambient modes, background playback.
6. **Data/state unchanged** — all profiles, settings, provider configs, playlists, favorites, watched/resume history, guide cache, databases and filesystem; no clear data, uninstall, storage schema migration, destructive repair, or automatic reset. No extra provider fetch, bind/reload, duplicate observer, interval/timer, or update loop.

## Mandatory verification gate before any signed candidate

- **BASELINE COMPARISON:** Diff *actual exact 2103435 signed APK* vs eventual candidate at APK-member level; provide explicit allowlist and enumerate all changed members, classes/methods, DEX and resources. No broad-source rebuild accepted without proof. Unchanged modules should match their locked 435 bytes/hashes. Repackaging/version metadata exceptions must be documented precisely.
- **ZERO-DELTA OWNER GATE:** Forbid any Infinity (including skin/Python) or Minimal Android functional change, 47 JNI/native libs change, launcher icon changes, chooser executable/UI change, or unrelated Cobra mode methods change. Fail closed on unknown deltas; never invent provenance.
- **FRONT AND INNER GEOMETRY:** Compare the locked 435 front two-column geometry to candidate at fixed viewports; compare inner 4-column closed state. Opening/closing drawer must not change Cards content-root geometry or number of columns except a real window/fold change. Capture measured root/shell bounds, layout requests, translation/scale, insets.
- **PHYSICAL REPRO ROUTES:** `20728.mp4` (cover→drawer→unfold) and `20729.mp4` (already inner→drawer open/close repeatedly); include rapid interrupted animation, rotation and return. No stray black unused region, no transient scaled/squashed video or card grid.
- **STATE/FUNCTION:** Before/after selected channel identity, scroll pixel offset, EPG, player object/surface identity, current playback/audio, focus, Back, drawer destinations. Do not claim a host-only screen is proof of real Fold behavior.
- **NEGATIVE CONTROLS:** Cover Cards and Pro/Pro Sports/Mobile/TV Grid/Compact/Multiview unaffected, both appearance and click behavior.
- **SIGN/DELIVERY:** Only after targeted checks and diff gates pass, build one next-version original-key signed install-over *test candidate* plus matching component ZIPs and SHA256; do not promote/lock pending user's physical Fold approval. One owner changed only. No shutdown tests.

**FAIL CONDITION:** Any unexplained member/class/resource/behavior change outside this drawer-specific allowlist means STOP, no signed promotion or disguised workaround; report exact blocker and preserve 2103435.

**STATUS:** Preservation instruction only; code unchanged by this document. Actual post-fix preservation cannot be asserted until a candidate's source/binary comparisons and user device checks have passed.
