# Close/Power audit and first follow-up correction

The locked APK is 2103304 and the locked authoritative skin is
`skin.infinity.diggz` 1.0.5.195. These locked files have not been modified.

## Recovered evidence

| Package | Exact APK SHA-256 | Evidence |
| --- | --- | --- |
| Earlier graceful-exit repair candidate 2103299 | `e46f1745668d6cd6b3df05ae12785e8a3a952e94c9e14cec70a2901ed0bd9dc5` | [Run 37117015142](https://github.com/mahfouzhassine8-ops/project-infinity/actions/runs/37117015142), artifact 11272405894 |
| Locked current APK 2103304 | `81884f5591d0912b031c6cc8dd6e8c6e198a84ddd95d03a878624fbb1e0425fa` | [Run 37194819014](https://github.com/mahfouzhassine8-ops/project-infinity/actions/runs/37194819014), artifact 11300970401 |

Both downloaded artifact archives and both extracted APKs match their recorded
SHA-256 values. The current APK's Android source proof is identical to the
successful validation export at commit
`70309e66ab33d3f12df93b7a46ddb153f1f02f97`. Every one of its 250 source files
was independently hash-checked before edits.

The user reports that Close previously worked. The exact APK accepted at that
time cannot be identified from the recovered artifacts or incomplete conversation
history. 2103299 is an earlier *repair candidate*, not a verified identification
of that accepted APK. Do not infer that the reported earlier success never happened.

## What changed and what remained

| Component | Result |
| --- | --- |
| Power bridge activity source | Byte-identical between the 3299 and 3304 source manifests |
| Graceful-exit helper | Original normal/force mechanism retained; 15-second record-only observer added later |
| Normal Close | Still waits for Android stop callbacks, then dispatches Application.Quit off the UI thread |
| Force Close | Still follows the explicit separate force-close path |
| Main lifecycle source | Changed by later repairs; native-destruction completion breadcrumbs and other lifecycle work remain |
| Native libraries | 46 of 47 packaged libraries byte-identical between both APKs |
| Main `libkodi.so` | Different binary; earlier `b3f32d5c5a3c346b7c0b15e382d0b43e0d6e795edabadb9e6b4175209043cf61`, current `b6724bc5cff3f3e79c5035f82e77be331535a9e3a7bf33e7650b7ab1e95c0626` |
| Signing certificate evidence | Both record the same permanent certificate SHA-256: `d7adeb68e9341596a02bd3262b737a0f45fc6e771ed7e60285437e833b58c6d7` |

The recovered Java evidence does not show removal of the original Close/Force
Close repair. This does not prove successful native teardown or locate the
shutdown hang. The main native binary changed across intervening builds.

## Confirmed route installer defect

The locked Android installer looks only for unconditioned `<onclick>` elements.
The established 195 Power XML patch specifies one Android and one non-Android
action on each Power button. The installer rejects that shape with “Missing
command 200”; its outer catch then ends the whole profile loop.

The new regression reproduces that exact error using the locked production
helper. The corrected helper accepts the approved paired routes without changing
their bytes. Unknown commands, attributes and conditions are still rejected.
One rejected profile no longer prevents checks of later valid profiles.

The approved 195 Android actions already route directly to the private Power
bridge. Therefore this installer defect alone does **not** explain a native
shutdown hang when the user successfully activates those actions.

## Preservation and rollback

The current source archive and its proof were copied into an immutable rollback
staging area before the working source was changed:

- Source archive SHA-256: `6c98056a4c395aa9144f4d09a5611eecb306218cb4d067522988947123eca466`.
- Source proof SHA-256: `f825d43f01885a661c718e91b5fa99592369709dbe83d9672c07735bf9da36e4`.
- Only `InfinityPowerMenuRoutes.java.in` changes in this follow-up.
- Its preimage is `7c162799c8ac0a0c507e70767b475f3fe9dcd7f53533201eb2002213199faf22`.
- Its corrected SHA-256 is `30091cc727a2fb4a477d286c7d7987af3e5cd683b53af3effe38401871661e6d`.
- All other 249 source files remain byte-identical. No native, skin, weather,
  playback, provider, signing or deferred movie-video framing edit is included.

## Validation and unfinished work

The corrected production helper compiles and passes 33 host checks covering
route preservation, Android component/arguments, unknown-action refusal,
idempotence, original backup contents and per-profile failure isolation. The
host Android stand-ins do not simulate device lifecycle or native shutdown.

The source workflow succeeded at commit
`671b3a91d2d32aeeb727d68b4ece98135ae16c74` in
[run 37221584705](https://github.com/mahfouzhassine8-ops/project-infinity/actions/runs/37221584705).
Full production Android compilation passed. All 104 Android/Robolectric tests
passed with zero failures, errors or skipped tests, retaining the inherited
suite and adding seven regressions. Ten weather producer tests and the compiled
weather-isolation audit also passed. No native compilation was triggered.

Artifact 11310551059 is unexpired through January 2, 2027. Its ZIP SHA-256 is
`56c99d8eb92d3dde467a3ecf0a35f5c4b59563142fbeea3c648d5654b734ce32`.
The downloaded ZIP passed CRC checks, and every archived source file was read
back and compared against the exact-commit 250-file proof. This evidence
contains no APK or installable skin ZIP.

The complete skin archive's transfer failed repeatedly. Replaying the Power
patch on the repository fixture provides the required conditional-route test
case, but the fixture's complete-file hash does not match the protected skin
file. No complete-skin hash verification or skin update is claimed.

Drawer geometry/focus polish, provider-owned source/resolver sizing and Back
handling, and idle takeover ownership/lifecycle remain pending skin recovery.
Native shutdown ownership, signed packaging, physical foldable tests, both
themes, all orientations, live resizing and Close/relaunch are still gates.

## Exact native shutdown owner recovery (October 4 follow-up)

The two source owners missing from the Android export have now been recovered.
They are audit copies, not changes to the native engine or its build recipe.
Both match the full-source manifest from native run 37189319805 exactly:

| Owner | Verified SHA-256 |
| --- | --- |
| `xbmc/platform/android/activity/XBMCApp.cpp` | `9feadf50fd1864815e819b598221cb2b20f78fea069aba7fb0a771b84ad95f49` |
| `xbmc/platform/android/activity/android_main.cpp` | `d70d38cef4471a74f70e3bc80ed0c100f6ae3dd8c54fc44f3bf482ccce263a32` |

Recovery used official Kodi commit `a3a448d26b8d560a65655dab2cd122994dc4e146`,
the existing audited 7.1 patch with zero fuzz and before/after hash guards, the
existing audio-policy owner transform, inherited v2 render-hardening transform
used by the v3 workflow, and the existing Android keyboard/health transforms.
No alternate native source or skin was substituted.

The unstripped library in that same downloaded artifact was independently read
and matches `2b0897a286a7286e17109e8f5c7c2ec152c838dc91686ce349be3100eea69eac`.
The source-manifest file matches
`b870052cc344b8d419ed8fb29eb5dbc019fdbc9a528219a576576dcc4332b82b`.

The verified source shows the two-stage Android finish/quit path. `Quit()` posts
the second-stage shutdown message and joins the application thread; `android_main`
then destroys `CXBMCApp`, records native cleanup completion, and exits the process.
The join and other synchronous callback waits are investigation points, not
proven owners of the user's hang. Moving or timing out native destruction without
a current blocked-thread trace would be speculative and could damage saves or
renderer ownership. No such change is included.

The newest recovered device report is `Infinity-Diagnostics-20261003-184051.txt`,
uploaded October 3 at 22:41 UTC, and explicitly reports APK **2103302**. Its
`exit.beforeNativeDestroy` records cannot establish what the current 2103304
engine did. This is not a current-build teardown pass or crash symbolication.

The exact 1.0.5.195 full ZIP is not present in the repository. The recoverable
1.0.5.194, 1.0.5.193 and 1.0.5.192 saved archives again failed to download with
HTTP 502. No skin files were changed. Continuing the UI repair requires the exact
locked 195 ZIP, or successful recovery of exact 194 and checksum-identical
reconstruction of 195. Current shutdown diagnosis requires a 2103304 Health
Center report captured after reproducing Close, ideally including the blocked
thread/native trace. No APK or updated skin ZIP has been produced in this follow-up.
