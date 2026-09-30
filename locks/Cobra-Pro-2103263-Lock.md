# Cobra Mobile Pro 2103263 Lock

User approval: "Lock", 2026-09-29 at 23:17:21 America/Detroit.

## Frozen Baseline

- Scope: mobile Pro / Focus mode, OLED-dark and Light variants.
- Exact build source commit: `dbe1925cbafc7edf423cd45ded7295ee73f12cd1`.
- Source snapshot: `locked-2103263-pro-oled-light-polish-approved`.
- APK: `Infinity-2103263-Pro-OLED-Light-Polish-RC1.apk`.
- APK SHA-256: `00c3f00eaf336ef2102e9f2226e8cb02e8d95767c043431690024018772153e4`.
- Successful build and verification: [run 36662814776](https://github.com/mahfouzhassine8-ops/project-infinity/actions/runs/36662814776).
- Automated result: 47 tests passed, 36 Pro native-view renders, 20 protected renders byte-identical.
- Native engine, permanent signer, Android resources, 4,039 assets and 46 native files preserved.
- Other view modes and playback action implementations unchanged. Infinity mobile skin `.172` untouched.
- Glass is layered shading and rims, not live backdrop blur or refraction.

## Verification Boundary

This freezes the approved source and signed candidate, not a physically verified stable release.
Physical-device acceptance, real-stream continuity, fullscreen/PiP return, and background/return
behavior remain pending. Original APK and verification report are retained without mutation;
their `stable_lock` and device-verification flags remain false.

Keep the locked 2103262 baseline as rollback. Future work must branch from the exact locked
2103263 commit; do not silently redesign this approved baseline or overwrite its signed APK.
