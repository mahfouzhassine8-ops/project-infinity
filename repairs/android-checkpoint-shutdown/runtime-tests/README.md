# Actual Command Center runtime integration checks

Run against the actual candidate add-on source directory; no production module
is copied into the test fixture:

```sh
python repairs/android-checkpoint-shutdown/runtime-tests/test_runtime_checkpoint.py \
  --runtime /absolute/path/to/script.infinity.commandcenter -v
python repairs/android-checkpoint-shutdown/runtime-tests/run_resume_preservation.py \
  --runtime /absolute/path/to/script.infinity.commandcenter
python repairs/android-checkpoint-shutdown/runtime-tests/test_runtime_relaunch.py \
  --runtime /absolute/path/to/script.infinity.commandcenter --cycles 500
python repairs/android-checkpoint-shutdown/runtime-tests/test_runtime_rpc_admission.py \
  --runtime /absolute/path/to/script.infinity.commandcenter
```

The test loads real `service.py`, `common.py`, `resume_hub.py`, `plugin.py`,
`experience.py`, `checkpoint_runtime.py`, and `persistence_participant.py`.
Only Kodi APIs and Android/native file requests are doubled. It exercises the
actual service loop and Player/Monitor callback methods, final frozen-playback
position, watched-state drain, required Kodi JSON-RPC failure, user mutation
admission, input-dialog RMW races, version gating, and owner/session markers.

These are runtime integration tests, not Android device acceptance. Native
player-thread serialization and interpreter callback FIFO order must also be
verified against native implementation and on the device.

The second command runs the original 2103292 fourteen-case Resume Hub behavior
suite against the candidate modules, retaining its existing fixture and adding
only the Monitor API double required by the new resident service class.

The third command starts a distinct host Python process for each journal cycle.
It imports the actual checkpoint modules, supplies current engine registration
and the exact retired prior-owner token before reads, preserves resume/playcount
data, and rejects a wrong prior owner. The harness supplies the registration and
uses completed subprocess exit as its death proof; it does not verify Android
startup timing, the Java owner lease, JNI, or physical close/relaunch behavior.
`relaunch-journal-result.json` records the scoped 500-process result.

The fourth command uses two real host processes and the actual participant flock
to hold an older watched RPC in flight while a newer plugin mutation and a
checkpoint attempt admission. A shared SQLite-backed Kodi RPC double verifies
that the older RPC completes before the new mutation, and that the final watched
mirror agrees with the managed JSON. Failed readback and malformed RPC responses
retain the required queued operation. This tests the Python admission ordering;
it does not replace the separate native database durability barrier.
