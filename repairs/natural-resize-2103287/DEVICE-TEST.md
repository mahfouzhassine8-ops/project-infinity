# Infinity 2103287 — Natural Window Resize RC1

Install the APK as an update over 2103285. Do not uninstall or clear data.

Install skin 1.0.5.180 directly from ZIP after the APK. It is the exact accepted 1.0.5.178 skin with only the version/description advanced; the rejected 1.0.5.179 16:9 default fallback is not carried forward.

## What this candidate owns
- Android Choose Your Experience uses the current activity window and preserves the complete approved composition.
- Hidden whole-background long-press theme controls are removed.
- Existing explicit gear/settings controls remain authoritative.
- Kodi's existing Android bridge remains the owner of settled SurfaceView/window dimensions.
- Kodi GUI windows now re-evaluate their skin resolution/profile after a committed window aspect change.
- If the closest skin profile changes, only that window's XML/control layer is rebuilt; its higher-level window/list model is retained and control state is saved/restored.
- 2103285 native FD crash repair, 2103209/2103254 Python runtime repairs, render hardening, playback, PiP, rotation, providers and user data are preserved.

## Device acceptance
1. Start on the Fold inner display. Enter Infinity/Kodi.
2. Rotate portrait -> landscape-left -> landscape-right -> portrait. Each settled orientation must fill/reflow to the current window without a stale old-profile layout.
3. Fold inner -> cover -> inner while browsing Home, Movies, TV Shows and one add-on directory. Verify focus/selection/list position remains sensible.
4. Start playback, open/close the OSD, rotate and Fold/unfold. No second player, playback restart, black return or stuck orientation.
5. Return from fullscreen to the background-video/Home state and repeat a Fold transition.
6. Try split screen/resized window. Kodi's surface and skin must follow the actual region rather than the physical panel.
7. On Choose Your Experience, long-hold empty background: nothing should open.
8. Check Light, Dark and OLED.

Do not lock from CI alone. Physical Fold acceptance is required.
