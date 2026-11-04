# Authorized controlled-test packaging

User authorization: package and permanently sign one install-over testing APK,
target version 2103453, from source checkpoint e90b44a1 and exact compiled ARM64
engine d0b6f115e839fbe39e764e2fecad47418c501ab1ece853294578652cd0b80b98.
No engine rebuild, installation, promotion or lock is authorized.

The actual signed 2103452 APK is the package-preservation predecessor. Only its
lib/arm64-v8a/libkodi.so, typed manifest versionCode, truthful version-label asset,
signatures and ZIP alignment/container metadata may change. Preview 451, Cobra,
all DEX and every other payload remain exact. The 451 recovery lock stays frozen.

Selected checks before execution: release-policy/security negative cases, exact
engine/source/artifact identity, all APK-member and component hashes, original
certificate and v1/v2/v3 signatures, package/version/ARM64 identity, zipalign and
unsigned forward-recovery rehearsal using a higher version and the exact 452
payload. Reuse the 20 acknowledged host cases and compiled evidence; run no
application, emulator or shutdown behavioral suite in packaging.

Android/Fold execution remains pending. Preserve every unknown or failed
durability obligation. Settings retirement remains BLOCKED; Scudo, Continue
Playing and Home work remain separate. No claim that ANR or memory exhaustion
is fixed. Stop publication if a signing, preservation or recovery gate fails.

The sole existing combined release workflow owns the key. Its branch/version
selection may be extended to this candidate and the already verified unsigned
ARM64 workflow may be added to its reviewed inventory. No signer, protected
contract, retired-workflow restriction or payload-validation rule is relaxed.
