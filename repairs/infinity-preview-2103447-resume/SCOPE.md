# Preview resume memory — selected implementation and verification

Base: exact original-key signed 2103447, source 89a9e7dabad99c44d19af9b0652beb4596523528,
user lock 1fe75deaebdbf71d5873dc69ba3e21c0526954f0. Work continues on
work/infinity-preview-2103447-per-video-resume-20261102.

The user's latest clarification selects the actual signed dark player UI. The
cinematic Light/Dark design is retained as a separate unimplemented design lock.
No design, theme, Splash/routing, Kodi, Cobra, shared/native or shutdown changes.

Selected checks, recorded before execution:

- Private resume store: separate A/B positions, exact millisecond records,
  process/store reopen, Start Over, completion/near-end/short/live handling,
  stable document identity, granted regular-file aliases, changed media,
  distinct same-named media, hashed identifiers and bounded retention.
- Decoder/request integration: outgoing-player checkpoint, pause/background/
  close/interruption/periodic save, stale request and resume-choice rejection,
  no autoplay before choice, seek completion before resumed playback.
- Boundary regressions: the committed decoder checkpoint takes precedence over
  an unupdated zero-position UI cache on restoration; arbitrary provider paths
  containing `document` do not gain SAF identity semantics unless Android
  recognizes that authority as a document provider.
- Focused Android API37.1 fixture: actual decoded A/B, real Resume/Start Over
  presses and seekbar/control-strip interaction, granted provider aliases,
  rapid switching, app-process restart and emulator reboot without data reset,
  background return, front/inner viewport and rotation. No shutdown suite.
  Process loss is injected only into the identified, already inactive private
  Preview process on the disposable emulator, after Activity/decoder cleanup;
  no package-wide termination or Kodi/Cobra/shutdown API is used.
- Exact signed447 source/class/member comparison, original certificate,
  component matching, same package and increasing install-over version.

Existing unchanged routing/state and native playback-control evidence is reused;
new checks exercise only resume integration and preservation controls. Android
emulator evidence does not constitute physical Fold acceptance or testing of
proprietary third-party file-manager applications.

Storage is a new Preview-only SQLite namespace on its existing decoder worker.
No existing database is read, reset or migrated. Start Over clears this video's
resume record. A checkpoint every 10 seconds bounds abrupt-process-loss exposure;
explicit lifecycle checkpoints read the decoder's actual position.

Runtime continuation: retain run 41436653854 as FAIL with completed core checkpoints through real reboot; execute only unfinished three-viewport/system-theme/control-strip, rapid switching, near-end reset and error-cleanup checks after adding the missing final scroll observation. Exact production DEX remains unchanged. Release evidence must retain both raw results and require every selected checkpoint; no failed run is relabeled PASS.

Release-only evidence validation additionally rejects missing selected checkpoints, a failed remaining segment, mismatched tested DEX, or incomplete viewport/theme coverage. It retains the original full-run FAIL and its exact raw result; the aggregate means selected checks completed across source-identical runs, not all workflows succeeded. No application tests are added by this gate check.

Known resize-input harness correction: run 41438660016 explicitly dropped the tap under Android's transition snapshot (BLOCK_UNTRUSTED). Observe removal of that active system layer before input; keep Android security, animation settings, existing observation bound and production bytes unchanged. Repeat only the still-unfinished remaining segment.

Run 41440049694 stopped before installation at adb root (connection closed/offline). The remaining public-input segment does not require privileged private-history reads or process loss, so its setup omits that unnecessary privilege restart. Full-core checks retain their root prerequisite. This is an emulator setup correction, not a production change.
