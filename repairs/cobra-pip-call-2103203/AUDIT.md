# Cobra 2103203 PiP / call playback — test candidate

Parent: locked 2103202, commit d9ce6b04a76f9f7d66bb626f1ce58875432c10f0. The exact signed parent, generated source, recipes, evidence and lock receipt were preserved in a verified rollback before edits. The locked parent is not replaced by this candidate.

Scope: requested PiP play/pause, explicit playback/focus retry through the existing player controls, and clearer subtitle-off state. No extra call-audio switch, native rebuild, transport rewrite, buffering tweak, stream reclassification or provider changes are authorized here. The Activity is the only changed runtime source; the Gradle version is the only other generated-source change.

PiP controls must use the current playback owner, reflect actual play/pause intent, reject stale sessions and retain Multi-View restoration. A successful Android/Robolectric control callback does not prove that Samsung SystemUI displays or dispatches the control correctly on the physical device. [Android PiP documentation](https://developer.android.com/develop/ui/views/picture-in-picture).

Cobra can retry audio focus when the user explicitly requests playback. Android can still refuse focus or mute media during a phone call. Incoming-call muting and intentionally starting playback during an existing call are different platform cases. No claim is made that every Samsung model, One UI version, call type or output route supports audible mixing. No automatic focus-stealing loop or media-to-call/alarm reclassification is used. [Android audio-focus documentation](https://developer.android.com/media/optimize/audio-focus).

Subtitle language preference and active subtitle-track selection remain distinct. A check on the Off option means Off is selected, not that captions are enabled. No detected usable track is not proof that a provider never supplies captions; late discovery and unsupported formats must remain observable without inventing a selectable track.

The required gates retain every one of the parent's 400 Android testcase identities and add candidate regressions. Any copy-only inherited expectation adjustment is explicit and guarded; assertions are not removed to make the candidate pass. The two independent signed replicas must have identical APK bytes. Native libraries, assets and resources are compared byte for byte with the locked parent; package identity and permanent signer are verified.

Source/static, host, Android/Robolectric, package/signing and physical-device evidence are separate. The machine-readable acceptance receipt records automated results and explicitly leaves phone-call audibility, SystemUI PiP controls and installed-update acceptance unverified until real-device testing. See DEVICE-TEST.md.

Existing limitations remain: no connected physical Android endpoint, no controlled capture of the user's streams, no promise of Multi-View recovery after process termination, and the parent's unrelated imported-theme, focus-clipping, external-artwork, recording-timeout and native 16 KiB compatibility questions. This candidate does not claim complete product acceptance.
