# Focused disposable Android harness

These scripts stage and run only ANDROID-REQUEST.json. The existing feature-only `checked_observer` and `verify_three_android.transport` factory are reused from immutable commit `2f18336ec766cf6e0234ecf7e9727ab4993247ff`. No prior broad journey/main or shutdown runner is called. Only the retained Device transport class executes Android operations.

Root supplies signed APKs and an exact signed-pair JSON:

```json
{"certificate_sha256":"ORIGINAL_CERT_SHA256","2103466":{"sha256":"BASE66_APK_SHA256"},"2103468":{"sha256":"CANDIDATE68_APK_SHA256"},"2103469":{"sha256":"FORWARD69_APK_SHA256"}}
```

From the repository root:

```sh
python3 repairs/infinity-watchlist-playback-2103466-20261108/stage_watchlist_android.py \
  --baseline /artifacts/original66.apk --candidate /artifacts/candidate68.apk \
  --recovery /artifacts/forward69.apk --signed-pair /artifacts/SIGNED-PAIR.json \
  --owner-export /inputs/Infinity_Source_Exports_For_Work.zip \
  --sdk "$ANDROID_HOME/build-tools/35.0.0" --out /tmp/watchlist-fixture

python3 repairs/infinity-watchlist-playback-2103466-20261108/verify_watchlist_android.py \
  --baseline /artifacts/original66.apk --candidate /artifacts/candidate68.apk \
  --recovery /artifacts/forward69.apk --fixture /tmp/watchlist-fixture \
  --out /tmp/watchlist-evidence --port 18766
```

Required host tools are Python3, ffmpeg with libx264/AAC, Android adb/build-tools, Pillow and Tesseract English. The retained transport accepts exactly one fresh disposable API37/4KiB emulator. Git must retain objects `2f18336...` and `2759febb`; the extraction helper reads immutable source objects, so prior task files do not need to exist in the working checkout. The host AIO server listens on18766; the emulator reaches it through `10.0.2.2`. No physical device is accepted.

Staging verifies original APK certificate/hash/package/version, all unchanged recovery native libraries and baseline functional module hashes, full source-only owner POV export, all12 retained dependency archives, the five owner Umbrella samples and the exact14/13 production reviewed source pins. Only two schema2 saved rows are seeded; no progress or watched row is seeded. Only the disposable POV profile receives AIO settings and synthetic `fixture:fixture` credentials. Actual public TMDb metadata requests and actual POV Sources/AIO resolution/fresh ListItem/self.play remain unmodified. The AIO stream response and210s clip are synthetic test fixtures and do not establish real account, catalogue or stream availability.

A bounded64-event disposable QA Player subscriber observes genuine AVStarted/Stopped/Ended/Error callbacks, without controlling playback or writing progress. Natural completion requires the actual Ended callback and no Error callback. The observer retains live native ListItem checks and compiles explicit if/raise checks under Kodi optimize1. Movie partial/resume/popup and exact TV descendants use actual native selections and actual AV/player time. A source-identified POV bookmark dialog is handled by its real Start From Beginning button, so the ordinary negative control can distinguish Infinity's scoped resume from POV's own bookmark behavior. Unknown dialogs or provider/network failures fail the selected run and preserve screenshot/logcat/PID evidence.

The explicit persistence restart uses force-stop only after a known saved user Stop. It is not shutdown acceptance. Recovery is a forward install and checks the retained data and profile sentinel. The runner does not uninstall, clear data, patch providers, mock callbacks, sign/build APKs, dispatch CI or modify workflows.

Host-only validation performed before delivery: syntax compilation of five scripts; actual pure-hub two-row seed shape; exact14/13 producer pin shape; retained12 dependency list; observer Assert-to-if/raise transformation and optimize1 syntax compilation. No Android or server/media execution was run by the harness author. A runtime failure is retained as FAIL and is not converted into a provider-source workaround.
