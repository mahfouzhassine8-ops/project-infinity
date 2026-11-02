# Preview cinematic controls and call audio over signed 2103448

The user selected the exact signed 448 APK as the base. This work changes only
the private Preview Activity and its new drawing helper. The Android handler,
Splash, decoder, per-video resume store, request-generation state, Kodi, Cobra,
shared/native payload, installed resources and shutdown are preserved.

The visible approved reference is the cinematic dark Preview image attached to
the task, with the glass Close/title/Infinity header, cyan framed video, elapsed
and total times, independent seekbar and glass transport/audio/display strip.
The other attached image shows the plain installed player and its denied-focus
message; it is symptom evidence, not the target design. Both inline images were
visually inspected. Raw reference PNG bytes are not exposed here, so no hash or
automated pixel-equality claim is made. Dynamic video, filename, clock and window
proportions necessarily vary. Light uses the same geometry and the separately
locked design's light-palette specification. The design lock was not modified.

`InfinityPreviewChrome.java` draws the Preview-only glass, static cyan contours,
brand and button icons. It retains native Button semantics, labels and accessible
descriptions. The existing bundled Roboto font is reused read-only. No new bitmap,
video engine, native library, provider, timer or service is added.

`InfinityExternalPlayerActivity.java` places the same video surface and existing
actions in the new layout. The horizontal strip remains a real ScrollView; the
timeline is outside it. Pause/Play, Stop/Close, ±10 seconds, Mute, Audio, Subtitles,
Display, rotation and the original Volume dialog remain. The reference's inline
volume slider uses the same private player level. Display also exposes Preview's
System/Light/Dark appearance preference, isolated from both main experiences.
The existing Best Fit/Fill calculation and resume callbacks are unchanged.

Call entry applies a separate temporary mute. Video can start with denied audio
focus while a real Android call/communication mode is reported. The user's
explicit manual Unmute can restore Preview's private audio level during the
call; Android/OEM/carrier muting may still prevent audible media. Ordinary
non-call focus denial/loss retains the prior behavior. Call exit restores
ordinary focus ownership. No global volume, audio usage, call route or telephony
permission changes. A late mode callback cannot restart an unfocused/background
Activity, and a deliberate user Pause remains authoritative.

Focused host reproduction found and corrected two issues in the new work before
release: a call notification could restart an already paused background Activity,
and in-place density changes left old pixel dimensions on the newly drawn
controls. The final host checks verify background pause and update the same
controls' density measurements without replacing the video surface/decoder.

Eight host tests pass, using the actual production Activity, View touch dispatch
and native Canvas. Decoder commands are observed through a terminal spy; these
results do not prove Android decoding or physical Fold behavior. The byte-bound
448 resume-storage/reboot evidence is reused because Engine and Resume remain
source- and class-identical. The new presentation's Resume/Start Over interaction
is selected separately for actual Android input.

The first Android run decoded real video and exercised pause/play and seeks. It
failed when its assertion sampled the clock before asynchronous seek completion;
the preserved XML and later screenshot show 1:34 then 1:44. The harness now waits
for completion within its existing bounded interval. Synthetic fixtures use
one-second keyframes so the unchanged decoder's sync-frame seeking can be
measured clearly. No production decoder or timeout was changed for that test.

The second run established another harness assumption: signed448 stops its
position ticker while paused, and ordinary seek completion does not publish a
new position until playback resumes. The immediate seekbar label is not decoder
readiness evidence. The final existing-control check therefore observes a real
playing tick after seeking and then waits for each relative skip to complete.
The decoder source and complete class definitions are unchanged; no new
paused-clock behavior is claimed. DEX indexes can move when the containing
Infinity DEX is rebuilt, so this is not a claim about isolated raw DEX offsets.

The third Android run completed the selected UI, control, Resume/Start Over,
subtitle, theme, viewport, request-replacement and error/retry checks. It remains
a FAILED workflow: its subsequent call setup incorrectly expected a Resume
prompt after six seconds, below the unchanged 30-second storage threshold. The
completed observations are retained without relabeling that run as successful.

The remaining call and exit checks passed in run 41475018882, using exactly the
same production classes3.dex as the completed UI checks. The emulator reported
MODE_IN_CALL. Video advanced with private player volume 0.0, then continued after
an actual Unmute tap with volume 1.0. Android media-player dumps identify the same
PID, UID and player connection on both sides of the tap. Video continued after
the call ended; Back returned to the source application and released the private
decoder. Kodi did not start. These are real Android API 37.1 emulator decoding and
audio-policy observations, not acoustic evidence from a carrier or VoIP call.

Actual Light and Dark app renders were inspected at cover, inner, landscape and
short-window sizes. The combined evidence gate binds both runs to their exact
artifacts and the same final production DEX. All six focused release-protocol
checks pass. Exact signed-APK comparison and original-key signing results are
reported in the delivery evidence once complete. Samsung call muting, physical
Fold transitions and final visual acceptance remain device checks. No new
release lock is automatic.
