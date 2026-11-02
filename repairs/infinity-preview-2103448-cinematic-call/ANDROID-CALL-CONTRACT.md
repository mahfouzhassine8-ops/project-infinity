# Android call/audio boundary

Read 2026-11-02: https://developer.android.com/media/optimize/audio-focus

Official documentation: if an app continues playing when an incoming call
arrives, the system may mute it until the call ends. If playback starts during
a call, Android treats that as an intentional action and need not mute that
player. Actual OEM/carrier/VoIP policy still applies. Android 15+ also requires
top-app or foreground-service eligibility for obtaining focus; this work adds no
service and does not change Preview's background behavior.

The signed448 Activity's startPlayback currently turns any denied focus request
into `Audio is in use. Press Play to retry.` and does not start its decoder.
That source branch exactly matches the user's visible status. The planned
exception is restricted to active call/communication audio modes, keeping the
MediaPlayer, USAGE_MEDIA, normal non-call focus handling and mute/volume ownership.

User clarification: video continues muted during a call; manual Unmute during
the call is explicitly allowed when Android permits media audio. Call entry
adds a separate temporary mute, preserving the prior player level and user mute.
Call exit restores ordinary focus handling. No call-state permissions, global
volume changes, audio-route changes, or new services are introduced.
