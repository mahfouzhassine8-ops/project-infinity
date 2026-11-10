# Infinity performance candidate — ready for one owner Fold acceptance test

The measured correction removes the periodic full skin checksum from the Infinity resident loop. It does not redesign the UI or change rendering, refresh selection, animations, provider networking or playback tracking.

## Package identity

| | Candidate | Forward recovery |
|---|---|---|
|APK|2103480|2103481|
|Command Center|0.3.5.78|0.3.5.79|
|Skin metadata|1.0.5.273|1.0.5.274|
|Functional foundation|Approved signed2103477 +two-file correction|Approved signed2103477|
|Cobra|2103445 unchanged|2103445 unchanged|
|Original signing run|42830516841|42832461653|
|Signed source|80e8fd3399d2d3ce1b8ede6a618ff4ad9bc244e7|1da730fe270847fea2dadfd1fe61e02caaddc0f8|

Package: `com.projectinfinity.kodi`. Original certificate SHA256: `d7adeb68e9341596a02bd3262b737a0f45fc6e771ed7e60285437e833b58c6d7`. Both APKs have verified v1/v2/v3 signatures and original-key complete80-file module manifests.

APK SHA256:

```
9cbb4c5f89a214924b6890463aa5842f85b18ff445d04d855e441fa61f4578c2  Infinity-2103480-Combined-Original-Signer.apk
621060de911fcb3e5098dd063ccb4a97aa339884342cec39f216d10159fe022c  Infinity-2103481-Combined-Original-Signer.apk
```

## Actual changes and measurements

Only `common.py` and `service.py` contain functional changes, frozen at7b84194e. Manual checks keep their original synchronous semantics; periodic checks use one finite, cooperative, read-only worker. Complete checks, source validation and generation checks remain mandatory. Resource budgets and cancellation never produce a partial healthy result.

Signed77's actual warm healthy948-file/43,793,653-byte scan took3147.704ms. The candidate's initial dispatch measured32.364ms, with repeated live-job calls3.7–32.5ms. This separates resident-return time from checksum completion; it is not UI input-to-photon or FPS evidence. The complete worker took5653.739ms versus2901.484ms for a synchronous check in that emulator sample. No total hashing-speed improvement is claimed. Shared CPU/FD observations do not isolate worker CPU or establish physical battery/thermal performance.

The seven-pair six-label batching experiment was slower (129.914ms median versus57.307ms) and was rejected. No batching patch shipped. Existing signed77 projection, Search cache, motion and refresh controls were preserved.

## Verification accounting

- PASS:18 focused actual-source host contracts and full948-file original/manual/cooperative result parity.
- PASS: original module RSA signatures, complete80-file source inventories and four retained real Java installer/data/recovery cases.
- PASS: authenticated Android worker cancellation, retirement, full result parity, actual resident checking→ok publication, loading ready/failure feedback, Home/Hub focus and foreground gate true→false→true (42827490004).
- PASS achieved before the later harness failure: actual41.408s local H264/AAC24fps playback with a complete948-file checking→ok cycle while video remained active (42833554341). This is a local playback smoke, not a provider or physical presentation-cadence result.
- FAIL retained: overall42833554341 stopped at an incorrect Kodi10103 assertion. Its screenshot shows the native Android Infinity Search open. This was an observer API error; no production change or APK rebuild followed.
- PASS: narrowed follow-up42837128934 verified native Android Search/Cancel, Infinity Movies/TV and existing empty Progress/Next/Continue routes, exact installed APK hashes,80-file native module authentication,948-file skin checks, in-place77→80→81 and retained QA sentinel. Completed playback was reused without replay. Empty fixture lists are not proof of owner tracking-card population.
- NOT RUN: physical Fold/front/inner/orientation/theme/high-refresh, battery/thermal, actual online-provider discovery/results/playback,30/60fps presentation, shutdown. Host/emulator results do not grant owner acceptance.

## Preservation

Post-signing comparison permits exactly10 changed members in80 and8 in81. Beyond the two Python sources, changes are required module/signature/version metadata. All five DEX files, all native libraries, Cobra, UI layouts, artwork, provider code, resume/tracking code and unrelated APK members remain byte-identical to exact signed77. Skin versions advance frozen network metadata but retain270's layouts/behavior. Recovery restores77 functional sources at higher versions. Original release tools and signer are unchanged. Astra found no signed-source/preservation discrepancy.

Networking2103478/2103479 remain frozen and unaccepted; neither their payload nor their DNS/proxy experiments were included. No uninstall, reset, cache purge, account/credential change, database migration, provider update, app Close or shutdown verification was performed.

## Installation after clearance

Install2103480 as a normal in-place Android update. Keep existing app data. Confirm CC0.3.5.78 and the existing approved interface. Perform one coordinated Fold check of Home/loading, Search, saved-TV navigation, actual provider playback/progress, and front/inner responsiveness.

Use2103481 only for recovery: it restores approved77 behavior through a higher-version update, preserving data. After installing81, do not try to reinstall80; a future successor must be higher. Never uninstall or force a downgrade to work around an installation rejection.

No final baseline promotion occurs before the owner's physical-device acceptance.

## Verified downloads

- [2103480 signed candidate APK inside ZIP](https://github.com/mahfouzhassine8-ops/project-infinity/actions/runs/42830516841/artifacts/13771187253)
- [2103481 signed forward recovery APK inside ZIP](https://github.com/mahfouzhassine8-ops/project-infinity/actions/runs/42832461653/artifacts/13771773326)

Download and extract the APK. GitHub repository access is required; these retained artifacts expire2027-02-08. Both downloaded archive sizes/SHA256 and extracted APK identity were verified. Keep recovery locally. These are scoped engineering candidates; no public/stable release or owner acceptance is claimed.
