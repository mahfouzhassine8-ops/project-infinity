# ZIP preview correction candidate 2103376

Immediate source/checkpoint: APK 2103375 (`b19f2b9101f8605499925e51c3cfea830b0f371a`).
Protected accepted rollback: APK 2103374. Neither baseline is moved or modified.

The native delta is three files: InputManager and the File Browser header/implementation.
The reviewed 375 admission/nonce/install contract is unchanged. A single-finger raw
hold is owned only by the opted-in Install from ZIP picker, before legacy keymap
translation. Selection uses Kodi's existing mouse/container path. The exact active
dialog instance sets its own skin opt-in from control 9410. Other windows, gestures,
source editing, missing script, non-ZIP pickers and skins without the contract keep
their normal path. Native stage messages contain IDs, not user filenames.

`tests/test_input_dispatch.py` compiles production method bodies. The old code must
reproduce (1) keymap bypass to an empty ContextMenu, (2) selection without click while
finishing scroll, and (3) the masked instance lookup. The candidate must pass these
and admission/duplicate/stale-confirmation/preservation cases. Narrow adapters replace
the GUI renderer, screen transforms and OS queue. These are not physical-device tests.
The supplied Fold screenshot alone does not prove which keymap/instance mechanism
occurred; the current installed keymap and Kodi log were not supplied.

Build continuation replays the exact hash-guarded 375 source checkpoint and reuses
the completed pinned NDK/dependency/compiler-cache artifact. No dependency, player,
provider, PVR, persistence, shutdown or Android Java implementation is changed.
All inherited source/preservation suites run unchanged before compilation.

No lock, acceptance, promotion or rollout is authorized by this work branch.
