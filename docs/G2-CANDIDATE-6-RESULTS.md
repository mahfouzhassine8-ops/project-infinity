# G2 Candidate 6 — confirmed results

Mapping-only GitHub run `34282883671` completed successfully. Code commit: `7110be392fe0421f9d12ce35c1bb2d2c5e8b6745`, branch `g2-candidate-6-mapping`. It is based on successful G2 #5, run `34273293502`, not the separate Architecture Audited Build.

The job ran from 21:51:45Z to 21:53:12Z (1 minute 27 seconds). No Kodi engine or native library was rebuilt. The old #5 workflow and its installed APK were not changed.

All 22 mapper tests, 5 real-SDK signing tests and 17 JVM policy cases passed in CI. Static cross-reference matched all 19 JNI registrations in four classes to #5's pinned source, including its six Infinity v2 methods. The native/Android mock policy tests do not establish runtime success on the user's phone.

Candidate artifact `10078340957` was downloaded. Its ZIP SHA-256 was verified: `a571b0c0488c3726e6134d601b13beb42bf67f7ba2ec0e8adbc05a7473f52568`. Actual unsigned APK SHA-256: `dbe2922171d77a15dfc2138e517956d92db4aa0f8d559d19b2620ed99ba461b4`. The actual CI APK was independently decoded and checked after download: all 45 native libraries, six other DEX files and all other non-signature APK members remain byte-identical to #5. All 911 non-adapter classes, including Main and every existing lifecycle callback, decode identically. Only InfinityCoreBridge inside classes5.dex changes. The mapper adds error/API/version guards and structural checks; it does not replace the native engine, Fold callbacks, lock, themes or normal playback policy.

**Signing is NOT complete.** The actual CI signing-status.json says `unsigned-awaiting-original-signing-key`, `signed: false`. No credentials were supplied to this run under the four configured signing-secret names. The artifact contains only `G2-Candidate-6-unsigned.apk`, not a signed `G2-Candidate-6.apk`. The signing tests used disposable fixtures that were deleted, not production credentials.

The new signing step deliberately refuses a different certificate rather than silently creating another throwaway identity. The #5 original key has not been retrieved or recovered. A signed install-over update needs compatible signing credentials. The original signed #5 APK was separately preserved as artifact `10078342580`. Keep testing #5; do not uninstall it to work around this.

**Status: mapper update built and verified; compatible signing and device testing pending.**
