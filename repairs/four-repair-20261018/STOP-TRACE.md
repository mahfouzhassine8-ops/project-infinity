# Post-Stop investigation: unresolved, no crash correction

The new native delta is confined to opt-in input dispatch and add-on information
for the UI contract. It does not modify the player, decoder, Android lifecycle,
directory worker, watched writer, crash recorder, or Essential-First shutdown.

## Path A: Stop → provider movie choices

1. `CApplication::StopPlaying()` temporarily releases the graphics and frame
   move guards around `CApplicationPlayer::ClosePlayer()`.
2. `CApplicationPlayer` holds a shared player reference while `CloseFile()` runs;
   `ResetPlayer()` releases the member under `m_playerLock`. The existing
   checkpoint write guard and active-close rejection remain authoritative.
3. `CVideoPlayer::OnExit()` closes streams, unregisters its render loop, queues
   video settings/bookmark callbacks, flushes rendering, releases demuxers/input
   and queues `OnPlayBackStopped()` on the outbound event queue.
4. `CApplicationPlayerCallback::OnPlayBackStopped()` queues
   `GUI_MSG_PLAYBACK_STOPPED`. `CApplication::OnMessage()` announces OnStop,
   resets the current item, performs `PlaybackCleanup()`, and notifies Python.
5. Command Center's serialized stopped callback persists continue progress and
   playback memory, then drains the existing durable Kodi-sync queue.
6. Android's `CXBMCApp::OnPlayBackStopped()` requests the established render-cache
   flush, updates/deactivates the media session, clears visible-behind and
   releases audio focus. None of these calls was changed by this candidate.

## Path B: the same sequence, then Back/Home

The additional transition activates Home and its asynchronous directory
providers. GUI reads and directory completion may overlap player/Python work.
The established directory retirement repair retains old GUI items until the
directory lock is released, avoiding the previously demonstrated graphics ↔
directory lock cycle. That fix is preserved. A lock cycle is not evidence of
the reported process exit's cause, and the UI changes do not alter its ownership.

## Evidence limits

An Android self-exit status of 139 alone does not identify a faulting signal or
instruction. The historical companion crash recorder has an `_exit(128 + sig)`
fallback after restoring/re-raising a fatal signal; that is a possible mechanism
for such an exit code, not proof it ran in the reported session. Its retained
crash-time register record and a system tombstone are needed to establish that.
An Essential-First receipt from another PID/session cannot establish a normal
shutdown for this exit.

Required missing evidence: a matching PID/time native tombstone or signal
register/backtrace record, contemporaneous Kodi and Android logs spanning Stop
and the optional Home transition, the exact playback/decoder mode, and current
process/exit records. No physical device is attached to the implementation host.
`capture_stop.py` gathers both paths separately without clearing logs or app data,
changing settings, force-stopping, installing, or uploading. Permission failures
are retained instead of represented as successfully captured stacks.

Crash reproduction on synthetic emulator media can only be a regression smoke;
it cannot exclude a Fold/decoder/provider-specific fault. No crash fix or final
baseline promotion is claimed.
