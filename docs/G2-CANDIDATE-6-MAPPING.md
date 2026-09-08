# G2 Candidate 6 — mapper hardening using successful G2 #5

## Identity and scope

This is G2 Candidate **6**, based ONLY on the successful G2 workflow **run #5**, ID `34273293502`, source commit `2a674c11cb1dc93002fefd868620f9a5a3d6e396`, artifact `10076770816`. It is NOT the separate Architecture Audited Build, and it does NOT import that build's v3 bridge or native libraries. The user reported installing #5, booting successfully and no crashes so far; playback, Fold, PiP, lock, resume and themes are still being tested.

New branch: `g2-candidate-6-mapping`. The existing #5 workflow and native patch files remain unchanged. Its original signed APK is preserved as the base. Artifact, APK, tool, native-reference-script and upstream-source hashes are pinned in `mapping/g2-candidate6/baseline.json`.

## Concrete changes

1. Replace broad post-build callback/text substitutions with a contract-driven mapper that changes exactly one class: `com.projectinfinity.kodi.InfinityCoreBridge`. Compile the adapter from readable Java against Android API 34; compare its public static descriptors and six native calls to the actual #5 declarations and source registrations. Do not insert a compile-only Main stub into the APK.
2. Add optional-feature guards: null Activity, native ABI version mismatch, missing JNI entry point, unsupported PiP API/feature, finishing/destroyed Activity, and off-main-thread PiP calls. Handle Android IllegalArgumentException, IllegalStateException and SecurityException from PiP parameter/entry requests. These paths previously could throw out of the lifecycle callback. This is a defensive behavior change on those failure paths, not a guarantee of crash-free playback.
3. Preserve #5's normal policy: 16:9 PiP, explicit leave/Home entry, API 31 auto-enter disabled, existing active-video gate. Paused/external-player semantics are deliberately not redefined. All Main lifecycle methods, Fold callbacks and native implementations remain unchanged.
4. Verify exact class identity, method definitions, instance-vs-static JNI flags, lifecycle supercall ordering, argument/register mapping, companion JNI classes and native-library manifest metadata. Reject missing/duplicate definitions, comments masquerading as calls, unknown prior adapter changes, and accidentally mixing in v3 endpoints.
5. Stage the change in a temporary tree, validate it twice for idempotence, assemble the upper layer, then import ONLY `classes5.dex` into the original APK. Disassemble the actual result and require every class except the adapter to match #5 byte-for-byte in decoded form. Require all other non-signature APK members—including every native library, other DEX, manifest, resources, stock add-ons, themes, lock and resume assets—to remain byte-identical. Do not transplant the rebuild's resources or native libraries.

## Source cross-reference and validation

The static reference check validates #5's four native patch script hashes and exact Kodi source files from `a3a448d26b8d560a65655dab2cd122994dc4e146`, applies them to a disposable source copy, and matches all **19 JNI registrations across four classes**, including the six Infinity v2 methods. No C++ compilation is performed.

Local validation passed: actual Android SDK Java/D8 compilation, APK assembly and re-decoding; **22 Python mapping tests**, **5 real SDK signing tests** (including all 14 partial-credential combinations), and **17 host JVM policy cases**. The host policy cases use fake Android/native collaborators and do NOT establish behavior on a phone. Fixture signing keys are temporary and deleted; no production key was created or recovered.

The actual local candidate retained all **45 native shared libraries**, six of seven DEX files byte-identically, and **911 other decoded classes** unchanged. Only the adapter class inside `classes5.dex` changed. Main, binary manifest, all resources, themes and lock files are unchanged. CI repeats the same checks against the downloaded immutable #5 artifact.

## Signing: deliberately no new disposable identity

#5's real certificate SHA-256 is `abcdb7ef3cdcac5c4fb86c3654454f09e69c8845abe04738d6721903f631fcc0`. Its workflow generated a key under `/tmp/infinity.keystore`; its published artifact contains the APK and hashes, not the private key. This does not establish whether the owner has an independent copy.

The mapping pipeline always produces a clearly labelled **unsigned** candidate first. It signs an install-over candidate ONLY when supplied persistent signing credentials resolve to #5's exact certificate, then verifies the final signature and byte inventory. If all four secrets are absent, it reports **unsigned-awaiting-original-signing-key** and publishes no `G2-Candidate-6.apk`. Partial credentials, invalid keys and mismatched certificates stop signing; there is NO temporary-key fallback.

An unsigned APK cannot be installed. The public certificate in #5's APK cannot recreate its private signing key. Do not uninstall #5, erase userdata, publish keys in the repository, or promise install-over compatibility. Continue testing installed #5 while this signing prerequisite is resolved. Successful mapper CI is not the same as a signed release or a successful device test.

## Deliberately unresolved

This change does not fix or claim to fix #5's native display-thread ownership, duplicate configuration-triggered refreshes, legacy native PiP pause/stop handling, dynamic video aspect selection, missing density/uiMode/smallestScreenSize manifest handling, incomplete automatic theme consumers, or 16 KB native alignment. These remain separate compatibility/behavior questions to test and then change only with evidence. No claims of complete architecture equivalence to the separate audited engine are made. Boot success alone does not verify them.

## Primary references

- Exact #5 artifact and source commit listed above.
- Kodi `JNIMainActivity.cpp`, `JNIXBMCMainView.cpp`, `XBMCApp.cpp` and Java lifecycle sources at the pinned 21.3 commit, plus #5's original native patches.
- Android JNI tips: https://developer.android.com/ndk/guides/jni-tips
- Android signing: https://developer.android.com/studio/publish/app-signing
- Apktool 2.x documented decode/build workflow: https://apktool.org/docs/2.x/cli-parameters/
