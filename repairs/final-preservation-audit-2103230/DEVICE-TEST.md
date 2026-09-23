# Cobra 2103230 physical acceptance

Keep the locked 2103229 rollback and a device-data backup. Install 2103230 as an update; do not uninstall or clear app data.

1. Run single Live TV and preview with the previously troublesome channels. If a stream ends, export Health Center diagnostics immediately before retrying. Note time, channel, Wi-Fi/cellular, and whether audio/video/both stopped. The provider root cause remains unconfirmed until this evidence is available.
2. Run 2, then 3/4 Multi-View streams where device/provider capacity permits. Pause one tile while another buffers/reconnects. Healthy peers must remain unchanged, and intentionally paused tiles must stay paused. Check Retry only affects the selected tile. Leave sessions running for at least 15 minutes each; record actual duration, not just startup success.
3. Exercise Fit/Fill, Enlarge/Restore, Full Screen/Return, add/remove/change screen and audio selection. The existing channels/sessions must persist through geometry changes. With grid Fill saved, fullscreen Display must still obey its own aspect choice.
4. Fold/unfold, rotate cover/inner displays, enter/return from PiP and background/foreground. Check no doubled safe-area bars, hidden controls, giant unassigned grid gaps, lost timeshift or unintended route change.
5. Verify rewind/Go Live/unified timeline, player lock, volume/mute/subtitles/audio tracks, media notification controls and the previously approved phone-call audio behavior.
6. Verify drawer destinations and native Android Back: Movies/Shows must not jump to Live TV unless explicitly selected. Check detail pages, trailers, episode browser, Resume/Next Episode, My List, shelf restoration, Settings/Power, Choose Your Experience and both Health Center entries.
7. Sweep Guide/EPG, empty/error states, pickers, popups and drawers in Light/Dark/OLED. Check cover/inner portrait/landscape and D-pad where supported. Do not infer device verification from automated layout tests.

Record pass/fail per item, device/OS, channel/provider category (no credentials), elapsed playback duration and exported diagnostics. No automatic lock of this candidate.
