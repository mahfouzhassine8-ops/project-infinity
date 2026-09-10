# Cumulative Infinity audio integration audit

Status: audit and a locally tested static gate only. No runtime audio-policy change, new APK, native build, or Samsung Audio Eraser enablement is delivered by this commit. The gate is not yet wired into a build workflow.

## Verified public build split

- Responsive Bridge v5: source `9407bd8e14b02b435f86333da2e4469467eaa151`, run `34521625447`, artifact `10172297158`. APK SHA-256 `eabf2e26520fe2b6314fb77f2e8961755e8947572ea757823c5a5172b4a24c72`.
- Native Media compatibility run 4: source `179b66503666b2b2bdd0b35ffc1d22cd0e5654d1`, run `34519841109`, artifact `10171439265`. APK SHA-256 `28df0f1551c86ffa90479fc70bbc386b9801eefb0d31b5a20d7e53c5db24873b`.
- Both APKs report versionCode 2103109. Version code alone cannot identify their capabilities.
- DEX class-table inspection: v5 lacks `InfinityPlatformHooks` and `InfinitySystemMediaHook`. The media APK includes them but lacks the v5 Java publication marker and native responsive fact strings.
- Running `scripts/verify_infinity_cumulative_media.py` on both real artifacts returns 2, as intended: neither is a cumulative responsive-v5 + native-media package.

## Existing hook boundary

`InfinityPlatformHook` exposes MediaSession creation, activity, state, metadata and session-intent callbacks. It does not expose AudioTrack creation. `infinity_upper_layer_repack.py` replaces only the compat and refresh asset trees. Kodi 21.3 `AESinkAUDIOTRACK.cpp` constructs actual AudioTrack attributes in C++ with CONTENT_TYPE_MUSIC. Updating session metadata cannot change that constructor.

## Required next implementation, not yet completed

1. Preserve responsive v5 and reconcile native-media source integration into one cumulative branch. Do not ask a tester to trade one feature set for another.
2. Audit real AudioTrack and audio-focus construction and lifecycle, then introduce a narrow versioned audio-policy extension point. Video and music must stay distinguishable; handle reused sinks and transitions, not just the first track creation.
3. Preserve existing playback, PiP, theme, refresh, diagnostics and user data. No second MediaSession, engine byte patching, package spoofing, private Samsung grants, or guessed activation keys.
4. Assign a unique higher version code and an explicit capability receipt.
5. Wire the cumulative presence gate into CI, then add source/API/JNI, functional policy and on-device gates. Presence checks are not runtime or eligibility proof.
6. Test video/music, start/seek/pause/resume/stop, output changes and fold transitions. Samsung chip visibility remains a separate device observation.

No user diagnostic logs or personal device contents are committed here.
