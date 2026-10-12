# Dual Infinity — G0 bootstrap implementation checkpoint

Status: **SIGNED STARTUP REPAIR READY. DEVICE ACCEPTANCE PENDING.**
This APK has **one** engine. Two-process startup, independent shutdown, dual
playback and audible handover are not implemented or accepted yet.

## Bootstrap 2 — exact delivery

- File: `Infinity-Dual-Test-G0-Bootstrap-2-Startup-Repair.apk`.
- Package: `com.projectinfinity.kodi.dualtest`; label **Infinity Experimental**.
- Version: `0.1.1-G0-Startup-Repair`, versionCode `2`.
- APK SHA-256: `ae5c95d1b7de3c5d1da5793c36615263f8b61cb93e5b38c183bdb83a8eea85fc`.
- Signer remains `d7adeb68e9341596a02bd3262b737a0f45fc6e771ed7e60285437e833b58c6d7`.
- Compiled shell source: `7ef8ddc6102fd84b6771f4a2807c4a035a747ffd`, run `38187425665`.
- Verification/packaging source: `7d6da0250c3fc3bfb8f2bc22dec7509a9c6450dd`, successful run `38188088077`.
- The parent native source/run/hash remain unchanged; no engine rebuild.
- Exact receipts, generated-class mappings and local download rechecks are in `evidence/G0-BOOTSTRAP2-*` and `evidence/G0-STARTUP-REPAIR-LOCAL-RECHECK.json`.

The shell run passed compilation and all 14 Android tests, then stopped on two
missing compiler-generated exact names. The entire affected population of 56
callbacks is now matched one-to-one by fields, interfaces, flags, instructions
and referenced targets. The compiled shell and executed test outputs were
reused. No source class or native declaration is missing; exact generated names
and their verified mappings remain explicitly recorded. Unknown instructions,
exception handlers, annotation changes or different callbacks are rejected.

Phone check: update **Infinity Experimental** only, open it, and confirm the
Kodi main UI renders. The icon now opens the startup path directly. If it fails,
use **Share startup diagnostics** on the recovery screen and send the ZIP.
Then return to Android Home. Do not treat a splash, compilation or this
one-engine package as a two-window or independent-Close pass.

## Physical failure and scoped repair

The user's `18411.mp4` recording shows bootstrap 1 returning from its splash to
the test launcher, followed by Android's app-bug crash dialog. No Kodi main UI
is visible. G0 native bootstrap has **failed**, rather than passed or merely
remaining unobserved. The recording hash and limitations are preserved in
`evidence/G0-DEVICE-FAILURE-18411.json`.

Exact parent `XBMCApp.cpp` constructs its dynamic broadcast receiver using
`getPackageName()+".XBMCBroadcastReceiver"`. Pinned libandroidjni commit
`7c1f1b326c14e0cf4d646b63a2ac448d7a8debe0` loads that Java class in its
constructor. Bootstrap 1 retained only the original class namespace, so this
experimental-installation class is missing. This is a concrete startup defect;
without a phone crash stack its attribution as the recorded crash's sole cause
remains unproven.

Bootstrap 2 adds a final receiver subclass under the experimental installation
namespace. It inherits the original registered native callback without adding
another native declaration or changing the cached engine. Pre-start class
resolution, executed reflection tests and DEX superclass verification check
both halves of that contract. The original static JNI methods remain unchanged.

The launcher opens Infinity directly and retains a recovery screen with **Share
startup diagnostics**. Its bounded ZIP contains only selected experimental
startup records, Java crash evidence and Android's own exit traces when exposed.
The export provider is private, accepts only one fixed read-only URI, and requires
an explicit read grant. It reads no production or add-on userdata. The Java fatal
handler records evidence and delegates to Android's existing handler.

The Android shell compilation and verified repackage use branch-scoped runs;
the protected parent engine and successful shell outputs are reused. The older standalone packaging workflow
is now manual and requires a verified repaired shell run instead of silently
using the first donor. There is no new native build or phone install here.

This repair is an update to **Infinity Experimental** only, versionCode 2,
`0.1.1-G0-Startup-Repair`. It remains a one-engine bootstrap. A successful build
cannot clear the failed physical bootstrap; a new phone observation is required.

## Exact source recovered

The technical parent is `2515c1a281abf9e57cfdbf570244c69f751a1437`, compiled
in successful workflow `38137092930`. The separate later lock record is
`18a2c4225661608235e44c57769426b6e08cbe47`.

All **9,390 native** inputs and **264 Android** inputs now match their current
compiled manifests. The five missing modified native files and four additional
3334 parent files are preserved under `recovered-native/`.

The 37 branding assets were recovered in the original Ubuntu 22.04 renderer:
ImageMagick `8:6.9.11.60+dfsg-1.3ubuntu0.22.04.5` and DejaVu `2.37-2build1`.
Only full SHA-256 matches were accepted. The previous workspace renderer was
6.9.12.98 and could not reproduce those bytes. Timestamp recovery preserved
all other PNG chunks. Workflow `38182143174`, artifact `11718482371`, contains
the reusable exact source archive; its hashes and local verification are in
`evidence/G0-SOURCE-COMPLETE.json`.

## Implemented Android installation probe

Android's installation ID and Java/JNI class namespace are distinct. The
previous statement that this decoy necessarily required a rebuilt native
package identity was too broad. The probe retains the verified class namespace
and explicitly adapts installation-bound routes and directories.

- Installation ID: `com.projectinfinity.kodi.dualtest`.
- Retained JNI namespace: `com.projectinfinity.kodi`.
- Fully qualified component classes; separate task affinity and provider authorities.
- No shared UID; only the experimental launcher is exported.
- All-files/storage-write and boot-receiver permissions removed.
- Cobra/Live/TV publication components disabled in this probe; their code remains unchanged.
- Application-owned paths configured before providers, extraction or native load.
- Shared `xbmc_env.properties` bypassed; fresh profile and disabled server defaults.
- Approved Power XML bytes preserved; reviewed self intents remapped to the decoy.
- Native lease job matching uses retained class names with the actual install ID.
- Original native declarations and class inventory preserved; no MediaCodec guard edit.

The installation strategy is verified at source, compiled-manifest, DEX and
host-test levels. Actual installation, native bootstrap, filesystem activity
and Fold behavior still require the physical phone.

## Executed checks

| Check | Result |
|---|---|
| Exact native source | 9,390 / 9,390 |
| Exact Android export | 264 / 264 |
| Host source/recovery/identity/preservation tests | 15 pass |
| Executable Robolectric ownership/startup tests | 14 pass |
| Original JNI declarations | 77 unchanged |
| Original Java source classes | Present; all 56 affected generated callback bodies verified despite suffix reassignment |
| Original Android resource IDs | 186 preserved |
| Cached native and protected APK payload | 4,106 protected entries unchanged |
| APK signature/alignment/package/CRC | Passed in packaging; ZIP and native hashes rechecked locally |

The first shell job `38183406077` failed release lint on a hardcoded manifest
debug flag; it was removed without disabling lint. `38183707535` compiled but
failed preservation when a raised minimum SDK changed the generated class
inventory. The original SDK baseline was restored. Final verified shell run:
`38184539423`, commit `5372dcdd8e5c29b065f92a189120eb76091ca766`.
Full inventories and executed test receipts are retained. Compilation is not a
native-runtime or two-window acceptance result.

## Historical bootstrap 1 package — failed on the Fold

- File: `Infinity-Dual-Test-G0-Bootstrap-1.apk`.
- Version: `0.1.0-G0-Identity-Probe`, versionCode `1`.
- Packaging source: `064d97d046798cc47518ac42c73a1d08a2524338`.
- Successful packaging run: `38185116610`.
- APK SHA-256: `8a66210e43122e3d79175e331d2868a7a2dfd104e81b19f90ebac2b43137b92d`.
- Signer SHA-256: `d7adeb68e9341596a02bd3262b737a0f45fc6e771ed7e60285437e833b58c6d7`.
- Cached packaged native SHA-256: `bd6be87e3c7d6c510973a55018029ed0e3488cd5328d7a81565cbbfdd44fefb9`.
- Native source/run remain `2515c1a…` / `38137092930`. No native rebuild.

This is a separate install despite retaining the class namespace and permanent
signer. It is not a production replacement, approved lock, or final Dual Infinity
package. Daily userdata/settings/providers/skin are not copied. Packaged skin
and add-on bytes are inherited unchanged from 2103368; the user's installed .207
skin and other installed content remain untouched.

## Original bootstrap 1 phone instructions (now failed; retained history)

1. Install only the named experimental APK. Android should show a new app named
   **Infinity Experimental**, package `com.projectinfinity.kodi.dualtest`.
   A prompt to update daily Infinity is the wrong package/action.
2. Open **Infinity Experimental**, then **Open Infinity test window**.
3. Confirm the native Kodi/Infinity UI renders. This verifies the retained
   namespace and bootstrap on the actual Fold. Do not test simultaneous movies
   or treat this one-engine bootstrap as the two-window feature.
4. Change a simple setting in the experimental app and verify daily Infinity's
   setting/history remains unchanged. Profiles are fresh; no live database was copied.
5. Return to Android Home after the bootstrap check. Report the startup screen
   or error. Independent Close, save receipts and simultaneous playback are not
   part of this first check; those remain separately gated work.

Optional ADB identity check after opening the test window:

```bash
adb shell pm path com.projectinfinity.kodi.dualtest
adb shell pidof com.projectinfinity.kodi.dualtest:kodi
adb shell pidof com.projectinfinity.kodi:kodi
```

The expected experimental PID belongs to `…dualtest:kodi`; the production
package remains separately installed. These commands do not certify writable
path isolation, saves, or shutdown and were not run on the phone here.

## Gate state and continuation

| Gate | State |
|---|---|
| G0 | Exact source recovered; bootstrap 1 failed on the phone; signed startup repair ready; repaired phone startup pending |
| G1 | Not started: no secondary activity/engine, two PID/task/surface or writer trace evidence |
| G2 | Not started: no per-slot 17-owner close proof |
| G3–G6 | Not started: no dual video/audio/Fold/provider/performance measurements |
| G7 | Not reached: final two-window package absent |

After the repaired physical bootstrap passes, continue the authorized Option B work:
two fixed private process components, pre-start writable roots, registry and
task ownership; then physical G1 evidence before independent shutdown or
simultaneous video. Stop at physical G0 evidence after delivering the repair.

## Rollback and preservation

No phone action was performed here. Production 2103368/2103365, approved skin,
Command Center, Health Center and Cobra source/installation remain unchanged.
Only `experiments/dual-infinity/` and four new, branch-scoped workflows differ.

To abandon the test on the phone, leave daily Infinity installed and remove
only **Infinity Experimental** if desired. Removing a test app deletes its fresh
test data; retain/export that data first if needed. Never uninstall or clear
`com.projectinfinity.kodi` as part of this test.

Production integration remains **NO-GO** and separately unauthorized.
