# Android transaction core — staged, not installed

The Java 8 classes in `src/com/projectinfinity/kodi/shutdown` implement the transaction and engine-side authorization protocol. They do not modify the recovered 2103335 parent, replace the Kodi engine, ship an APK, implement a native save barrier, or claim a device fix.

Run `python repairs/android-checkpoint-shutdown/test_android.py` from the repository root. It compiles with `--release 8`, all compiler warnings enabled and treated as errors, then runs the host protocol tests. Classes are created only in an automatically removed temporary directory. `java com.sun.tools.javac.Main` works if the JDK compiler module exists without a `javac` executable. No external dependency or downloaded compiler is required.

## Implemented contract

- One immutable transaction session: random session UUID, engine process-owner UUID, PID, authenticated binding UUID, monotonic start and deadline. Duplicate closes return the same transaction without reissuing work. Recovery or a new engine requires a new coordinator instance.
- `IDLE → QUIESCE → CHECKPOINT_REQUESTED → PERSISTING → SAFE_TO_TERMINATE → ENGINE_TERMINATING → COMPLETE`. `SAFE_TO_TERMINATE` is an internal transition immediately followed by dispatch; it is not an animation delay or percentage.
- The required-owner registry is explicitly supplied by the audited native persistence integration. An empty registry is rejected; this code contains no guessed default registry.
- Quiescence produces a manifest for exactly the required owners, with a checkpoint generation and each owner's dirty flag and generation. Admission must remain sealed. The manifest is not an acknowledgement that saves completed.
- A native receipt must match the exact session/checkpoint generation, explicitly keep admission sealed, include each owner exactly once, confirm required writes finished, and match both observed and durable generations to the cut. Dirty owners require `COMMITTED`; clean owners require `ALREADY_DURABLE`. Missing owners, stale generations, extra/duplicate owners and failures reject the entire acknowledgement.
- Only the authenticated channel receives reply capabilities. Read-only snapshots cannot assert a save. Only the coordinator creates a termination capability.
- The engine endpoint revalidates the receipt independently. The capability is one-shot, tied to the engine identity and exact immutable proof, deadline checked, and revocable until consumption. Semantic manifest and receipt comparisons work across DTO decoding; Java object identity is not persistence evidence.
- Native termination remains an injected backend operation. It must atomically recheck the still-sealed generation and process identity immediately before terminating that engine. No default backend, kill fallback, legacy Quit/Stop/Cleanup call, success receipt, or timer-based success exists.
- Completion requires matched engine-death evidence. A missing Activity, lifecycle return, transport disconnect, timeout or observer report cannot complete the transaction.
- A failed dispatch, lost binding or deadline revokes a capability not yet consumed. After consumption, termination is irreversible: a transport exception records `termination_confirmation_pending` and preserves `ENGINE_TERMINATING` until matching death is proven. It cannot truthfully promise cancellation after an engine was already authorized to terminate.

## Mandatory Android integration work still absent

The classes are transport-independent protocol code. No Messenger/Binder adapter or JNI/native backend is provided here. In particular, the in-memory `TerminationAuthorization` must **not** be serialized into a plain boolean, a historical file receipt, or a replayable permission flag.

A real process adapter must retain the capability in the authoritative shell coordinator and expose an authenticated, one-shot Binder consumption gate. The engine must bind that gate to the established coordinator peer, verify sender UID, session, engine-owner UUID, PID and connection UUID, and supply its locally verified native receipt for exact comparison. Failure/revocation and consume must share one serialized authority. If consume was already accepted, a subsequently lost response is an uncertain termination, not proof of revocation. The native backend must retain its sealed state through this exchange and fail closed if it cannot prove its final barrier.

The current direct endpoint implementation is useful for a same-process protocol harness and for implementing the engine adapter's validation rules. Wiring two Android processes requires replacing that direct call with the authenticated capability gate above. No claim is made that transferring a Java object or copying its fields implements Binder authentication.

Other required integration:

1. Recover and audit the exact parent native writer registry; implement the real quiescence and persistence operations, including provider/Python/Resume Hub writers and dirty database/file owners.
2. Convert the existing default-process close guard into the single coordinator. Retain the nonsticky existing-engine binding; never auto-create or restart the engine to deliver shutdown.
3. Route Normal Close through the coordinator; remove its `Application.Quit` dispatches. Preserve explicit Force Close as a distinct user action. Do not finish the NativeActivity before the save barrier.
4. Stop Android-side creation of new refresh/install/weather/TV jobs while quiescing. Preserve Cobra and unrelated shell owners.
5. Add a durable session-bound checkpoint/coordinator receipt and let chooser/Health Center distinguish checkpointed termination from legacy cleanup. Do not synthesize `native.CXBMCApp.Destroy.complete`.
6. Verify the bound engine's death through the existing owner lease and authenticated process identity, then publish COMPLETE. A generic Binder connection loss is not process-death proof.
7. Validate on the device: injected persistence failures, timeout, relaunch, resume/watched/settings integrity, stale callbacks, same-PID different owner, sticky service restart prevention and Cobra survival.

Host tests verify the protocol only. They cannot prove SQLite/file durability, coverage of every persistence owner, Android process behavior, or the absence of legacy teardown on a shipping device.
