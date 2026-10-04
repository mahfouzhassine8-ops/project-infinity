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

2103299 is the recovered earlier *repair candidate*. The available history does
not establish it as a user-accepted successful normal-Close build. The explicit
earlier device success found in the audit concerned Force Close. This comparison
must not be presented as proof that a working normal-Close APK was identified.

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

The new source workflow preserves the inherited Android compile/test suite and
adds seven Robolectric regressions. Its output is source evidence, not an APK.

The complete skin archive's transfer failed repeatedly. Replaying the Power
patch on the repository fixture provides the required conditional-route test
case, but the fixture's complete-file hash does not match the protected skin
file. No complete-skin hash verification or skin update is claimed.

Drawer geometry/focus polish, provider-owned source/resolver sizing and Back
handling, and idle takeover ownership/lifecycle remain pending skin recovery.
Native shutdown ownership, signed packaging, physical foldable tests, both
themes, all orientations, live resizing and Close/relaunch are still gates.
