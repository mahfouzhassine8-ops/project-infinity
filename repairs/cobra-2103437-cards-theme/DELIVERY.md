# Cobra Cards theme candidate 2103438

One original-key signed combined install-over APK is delivered for physical Fold
testing. Protected signed 2103437/source 31d55543 and its lock remain untouched.
No new candidate is automatically accepted, locked or promoted.

- [Signed APK archive](https://github.com/mahfouzhassine8-ops/project-infinity/actions/runs/41250066560/artifacts/13061405460)
- [Exact matching component ZIPs](https://github.com/mahfouzhassine8-ops/project-infinity/actions/runs/41250066560/artifacts/13060877683)
- [Successful original-key build/signing run 41250066560](https://github.com/mahfouzhassine8-ops/project-infinity/actions/runs/41250066560)
- [Signed source a5f721578c53e026a26cf21d929fbdad530f6d17](https://github.com/mahfouzhassine8-ops/project-infinity/commit/a5f721578c53e026a26cf21d929fbdad530f6d17)
- Authenticated official owner preparation: [41248722422](https://github.com/mahfouzhassine8-ops/project-infinity/actions/runs/41248722422), component source `7543f8a25b47a74b335fc7b0c0fbbf1a8de09e5d`.

Extract `Infinity-2103438-Combined-Original-Signer.apk` from the APK archive and
install over the existing app. Do not uninstall or clear data. The component
archive contains matching COBRA, INFINITY, MINIMAL_ANDROID_CONTRACT and
CHOOSER_SHELL ZIPs; these are not separate Android apps.

## What changed

Cards reapplied fixed black surfaces, white/muted text and dark drawables after
native appearance publication. Its custom presentation therefore stayed dark
even while the existing native resolver selected Light.

A Cards-only adapter now reads the existing `cobraModeDark()` and
`cobraModeColor()` APIs. It introduces no preference, palette definitions, global
listener, worker, polling or alternate theme engine. Light uses the native
background, panel/panel2, text, muted, accent and line roles. Existing borders,
fonts, icons, spacing and actions stay. Dark/OLED paths retain every original
paint value; their controlled host screenshots are byte-identical to baseline.

Existing render/restyle and tile bind/refresh hooks update the custom surfaces
and recycled rows. Cached heading spans update their accent without modifying
native source text. Colors are immutable local values, not stored user settings.
No player, data loader, native appearance resolver or other view mode is changed.

## Checksums

| File | SHA256 |
| --- | --- |
| Infinity-2103438-Combined-Original-Signer.apk | `a1907acbcb3a36f5b2312f8a11cd4e38d8fcdbed2f435b6ab45d369adc8e9f35` |
| COBRA.zip | `2229274553616f4febb7ef80925eddc23f6f2346bddf4eeabee18e819158399e` |
| INFINITY.zip | `d03b4d5e845dfb5e1d6bb75c1967c7b6a2e55c5b17a7c65d66d43d43abd2e73d` |
| MINIMAL_ANDROID_CONTRACT.zip | `432bfb7b246a504d9550e1de39368c3b7e0946532f1c695531ed891e74ef03d8` |
| CHOOSER_SHELL.zip | `145c0639a6387659391fa312e646c533a681f6d7e98c0f823d787477a6691266` |

Original certificate SHA256:
`d7adeb68e9341596a02bd3262b737a0f45fc6e771ed7e60285437e833b58c6d7`.
Both actual signed 2103437 and the downloaded 2103438 APK independently verify with that
certificate and APK v1/v2/v3 signatures. CI also verifies native 16 KB ZIP alignment.
Package identity remains `com.projectinfinity.kodi`, versionCode 2103438 > 2103437.
No replacement certificate, data migration or reset was used.

## Focused verification

Controlled Robolectric API 35 source overlays use the existing native 2103435 host
fixture classpath with baseline 2103437 and candidate Cards Java. These are actual
rendered Android views, not full signed-APK execution or physical Fold results.
The compiled candidate Cards definitions are separately bound to actual owner
DEX through canonical class fingerprints and the original signing gate.

- Native Light/Dark/OLED and repeated native restyle: pass.
- Cover two columns and inner four columns: pass; layout/model/bounds/margins,
  focus/clickability and other geometry remain unchanged across theme changes.
  Only the deliberately changed background raster is excluded from that geometry
  comparison; its native palette value is independently asserted.
- Recycled Light rows retain native text color and selected channel identity: pass.
- Cards Light -> Mobile/Pro -> Cards retains appearance choice, selected channel
  and correct Cards text color: pass. This is not a Pro redesign or Pro acceptance.
- Dark and OLED: each baseline/candidate PNG is byte-identical, and full shared-view
  snapshots match. See [host parity](evidence/HOST-PARITY.json).
- Exact palette-field admission and four forbidden field mutations: pass.
- Four release-protocol tests plus exact owner-root/unknown-class rejection: pass.

[Light host render](evidence/HOST-LIGHT-FINAL.png) ·
[Dark host render](evidence/HOST-DARK-FINAL.png) ·
[OLED host render](evidence/HOST-OLED-FINAL.png).

Early host attempts omitted the fixture's existing paused Choreographer setup
and did not reach assertions. They remain failed/stopped evidence. The setup was
restored. Initial geometry assertions also compared entry-loading alpha and
intentional Light/Dark background changes; the corrected check compares the same
native restyle phase and retains strict geometry plus separate native-color
assertions. No failed result is relabeled as passing.

## Exact signed 2103437 preservation

Independent verification downloaded both published artifacts, verified their
GitHub archive digests and compared every published ZIP with the prepared bytes.
All component payload members and all five DEX files match the actual signed APK.

Exactly **seven ZIP members differ** from signed 2103437:

| Member | Permitted reason |
| --- | --- |
| classes4.dex / classes5.dex | Cobra-only Cards palette code and required component-version literal; DEX references/indices are regenerated |
| assets/experience-component-updates.properties | Truthful Cobra last-updated 2103438; Infinity stays 2103437 |
| AndroidManifest.xml | Typed install-over versionCode only |
| META-INF/INFINITY.SF | Regenerated original-key APK signature metadata |
| META-INF/INFINITY.RSA | Regenerated original-key APK signature metadata |
| META-INF/MANIFEST.MF | Regenerated original-key APK signature metadata |

No APK member was added or removed; 7,610 non-signature members remain unchanged.
Infinity ZIP and its actual APK assets/DEX are byte-identical to signed 2103437.
Minimal/shared ZIP, launcher resources, chooser executable/UI, all 47 native
libraries and all unrelated assets remain unchanged. Only truthful chooser
version metadata advances. Source/model/data/shutdown functionality is untouched.

Within Cobra, 7,160 original canonical class definitions are identical. Seven
Cards styling classes change; `CobraComponent.version()` changes only its literal
to `2103438.cobra.1`. Two narrowly scoped palette-adapter classes are added.
The signed drawer `physicalLayout` method is retained byte-for-byte rather than
accepting compiler register renumbering. Every changed method is bounded by
[METHOD-ALLOWLIST.json](METHOD-ALLOWLIST.json). No player/touch-dispatch callback,
shared theme engine, provider, data model or other-mode implementation changes.

Evidence:
- [Complete APK delta including signatures](evidence/delivery438/COMPLETE-APK-DELTA.json)
- [Every non-signature member hash](evidence/delivery438/ALL-APK-MEMBERS.json)
- [Canonical class preservation and method boundaries](evidence/delivery438/CLASS-PRESERVATION.json)
- [Matching component/APK bytes](evidence/delivery438/MATCHING-COMPONENTS.json)
- [Original signature verification](evidence/delivery438/CANDIDATE-SIGNATURE.txt)
- [Final status and source/run binding](evidence/delivery438/STATUS.json)

## Release safeguards and retained failures

The original shared ModuleDexWriter remains untouched. A task-local build adapter
admits exactly one palette-reference field in five explicit Cards classes and
rejects other additions/removals; it never ships in the APK. Compile-only native
signatures are excluded from program DEX. Exact host/owner fingerprints and
negative admission tests remain mandatory.

Preparation 41248454616 stopped because the older tool archive lacked D8. The
existing SDK 35 copy was supplied with its original SHA256 pin enforced;
preparation 41248722422 passed. Signing attempt 41249025549 correctly refused the
unregistered new palette class before key access. A reviewed, exact
`CobraCardsTheme -> COBRA` ownership-map addition was recorded; unknown classes
remain rejected. This evidence-only registry update changed no prepared payload,
component, version or accepted pointer. The successful final run rechecked all
original payload/signature gates. No failed integrity check was waived and only
one signed 2103438 APK was produced.

## Physical acceptance remains pending

The signed APK was not executed on Android 17 or the physical Fold in this task. Full background/
foreground lifecycle, physical fold/unfold/rotation, real streams/decoder,
fullscreen, PiP, More and all ambient/night variants were not newly accepted on a
device. Their underlying protected code is preserved; host/source checks do not
replace physical acceptance. No shutdown test or device installation ran.

On the Fold, select Light/Dark/OLED with the existing sun menu. Check Cards while
visible, after Settings, after background/foreground and after visiting other
modes. Fold/unfold and rotate with the drawer open/closed; confirm cover two/inner four
or the existing accessibility fallback. Scroll/recycle rows and verify selection,
EPG/logo readability, preview/playback, fullscreen More and PiP continuity. Confirm
Infinity and other modes remain as approved. The user alone accepts this candidate.
