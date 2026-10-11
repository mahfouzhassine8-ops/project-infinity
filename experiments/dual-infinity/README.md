# Dual Infinity — G0 implementation checkpoint

Status: **BLOCKED AT G0. DEVICE ACCEPTANCE PENDING.** No Dual Infinity runtime,
second engine, decoy APK, native rebuild, or installation has been produced.
This checkpoint contains actual source recovery and a tested source gate; it
does not claim implementation of G1–G7.

## Exact parent and changes

The technical parent is `2515c1a281abf9e57cfdbf570244c69f751a1437`, compiled in
successful run `38137092930`. The separate lock documentation commit is
`18a2c4225661608235e44c57769426b6e08cbe47`. These identities are deliberately
distinct in `PARENT.json`.

Only `experiments/dual-infinity/` is added. No existing runtime overlays,
build recipes, manifests, skin, Command Center, Health Center, Cobra code,
signing assets, release artifacts, or protected branches are modified.

The five native files named by the handoff have been recovered and independently
matched against the current compiled-source manifest by two methods: pinned
Infinity source transformations and archived native review artifact
`11525589472`. Four additional exact 3334 parent files are also preserved.
All nine are under `recovered-native/`; their hashes are recorded in
`PARENT.json`. They are recovery inputs, not replacements applied to production.

`source_gate.py` verifies the pinned native/Android manifests, selects only exact
file hashes, refuses source/destination overlap or existing output directories,
rejects escaping symlinks, and rechecks copied bytes. Partial recovery exits 2;
missing generated images are still blockers. No build validator was weakened.

## Executed evidence

| Check | Result | Limit |
|---|---|---|
| Successful parent workflow identity | 2515c1a…; conclusion success | Existing build, not a prototype build |
| Five required native preimages | All five exact SHA-256 matches | No JNI execution test |
| Four further parent files | Exact compiled postimages recovered | Recovery only |
| Android exported source | 264 / 264 current hashes match | No new Android compilation |
| Full native-source recovery | 9,353 / 9,390 hashes match | 37 assets remain unresolved |
| Source-gate negative controls | Five host tests pass | No Android/device isolation acceptance |

The full missing-file and expected-hash inventory is
`evidence/missing-native-inputs.json`. It consists of 36 PNGs and one JPEG.
The replay of the original image recovery recipe refused these bytes. The
Android shell export and archived native subset did not supply matching copies.
No different pixels, timestamps, source variant, or unverified image was accepted.

## Why packaging remains blocked

The preferred strategy remains a distinct experimental application on the Fold.
Changing only the shell application ID cannot reuse the verified production
library: `CCompileInfo::GetClass()` supplies the compiled package for JNI class
registration, and `JNIMainActivity` registers that package's `Main`. The ambient
companion source also exports the production-package JNI symbol
`Java_com_projectinfinity_kodi_InfinityKodiAmbientGate_setActive`.

A decoy therefore requires matched native/package/companion-library changes,
verified component and authority identities, owned paths, and routing of the
unchanged approved skin's commands. None of that is certified by this checkpoint.
The exact complete native preimage must pass first. Do not start an expensive
native build from the partially recovered tree to work around this gate.

| Gate | State |
|---|---|
| G0 | Blocked: complete native input and installation-safe decoy are not verified |
| G1 | Not started; no two-engine/PID/task/surface evidence |
| G2 | Not started; no independent 17-owner shutdown evidence |
| G3–G6 | Not started; no decoder/audio/Fold/provider/performance measurements |
| G7 | Not reached; no signed experimental APK |

## Resume from this checkpoint

1. Recover the 37 original assets using the expected hashes in the missing-input
   inventory. Verify every native input with the unmodified full-source contract.
2. Complete the separate-package decoy strategy, including all native and
   companion JNI identities and preserved skin command routing. Validate the
   matched package before marking G0 passed.
3. Implement the fixed two-process startup and independent writable roots.
   Physical G1 evidence is required before G2 and dual playback work.
4. Continue the authorized stages in order; preserve the existing native
   checkpoint/proof/death gates and the MediaCodec guard.

No further production-integration authorization is implied. No background build
or implementation continues after delivery of this stopped checkpoint.

## Installation and rollback

There is no test APK to install. Do not install a development APK retaining
`com.projectinfinity.kodi` over the daily Fold installation. A same-package
comparison would require a verified disposable device or isolated profile;
that environment has not been verified here.

No device changes were made, so no device rollback is needed. The locked
2103368 and 2103365 releases remain unchanged. Resume or discard this
experimental branch independently; never reset/rebase a protected branch.

## Re-run the current checks

From the repository root:

```bash
python3 -m unittest discover -s experiments/dual-infinity -p 'test_*.py' -v
python3 experiments/dual-infinity/source_gate.py verify --group native \
  --source /absolute/path/to/recovered/native/tree \
  --report /absolute/path/to/native-source-report.json
python3 experiments/dual-infinity/source_gate.py verify --group android \
  --source /absolute/path/to/recovered/shell-kodi \
  --report /absolute/path/to/android-source-report.json
```

The source gate's successful exit is only a source prerequisite. It never
certifies installation safety, independent shutdown, or physical playback.
