# Unexpected exit investigation: unresolved, no crash correction

The new native delta is confined to opt-in input dispatch and add-on information
for the UI contract. It does not modify the player, decoder, Android lifecycle,
directory worker, watched writer, crash recorder, or Essential-First shutdown.

Stop was reported near the failure, not established as its cause. The physical
target is Samsung One UI 9.0 / Android17 API37. Generic API30/35 compatibility
and API37 platform tests cannot certify that firmware or hardware behavior.

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

## Additional lifecycle paths, without presuming a common cause

The exact 2103385 Main bytecode (unchanged from locked2103384, except the separately
identified API30 insertion in 2103386) retains lifecycle breadcrumbs through
`InfinityExitDiagnostics`. `onPause` suspends responsiveness/weather capture and
delegates to NativeActivity; `onStop` resets the orientation request, notifies
`InfinityCoreBridge`, and preserves the existing exit-completion guards.
`onConfigurationChanged` and window-focus callbacks remain present. Their ordering
at the reported physical exit is unknown; a source path is not evidence it ran.

The reviewed native Android activity overlay's `CXBMCApp::onResume` resets wake/
shutdown timers, posts `TMSG_RESUMEAPP`, and handles the existing resume/visible-
behind policy. `onPause`/`onStop` use existing PiP, visible-behind and playback
state to decide pause/Stop actions. `Application.cpp` handles `TMSG_RESUMEAPP` by
marking the GUI dirty; display setup/destruction controls the render surface;
screensaver activation/reset messages route to `CApplicationPowerHandling`.
`InfinitySyncDisplayState` queues settled geometry separately from configuration
notifications. These are correlation points, not selected crash suspects.

Capture background durations **5/20/45/90 minutes**, idle/playing, normal Home/
Recents returns, screensaver dismissal and individual fold/unfold/rotation
transitions. The collector's `background`, `screensaver` and `fold` paths keep
separate timestamped event sequences, firmware fingerprint, process/thread lists,
power/dream/display/device-state snapshots, live logcat and post-event exit/crash
records. Compare original PID/owner and new-process startup so OS reclamation is
not confused with a native fault. Optional post-event `debuggerd -b` is limited
to an identified still-live `com.projectinfinity.kodi:kodi` engine; access denial
is retained and no elevation or signal-based crash induction is attempted.

Still missing: the matching physical PID/time fatal-signal backtrace/tombstone,
logs covering the actual transition, device firmware/session and decoder facts,
and (if frozen) contemporaneous thread/lock ownership. No new physical reproduction
has been supplied. No causal link to the earlier directory/graphics lock cycle,
Stop, background duration or Fold transition is established by the current data.

Crash reproduction on synthetic emulator media can only be a regression smoke;
it cannot exclude a Fold/decoder/provider-specific fault. No crash fix or final
baseline promotion is claimed.
