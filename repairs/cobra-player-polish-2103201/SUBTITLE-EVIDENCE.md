# Subtitle selection evidence

The protected runtime uses `androidx.media3:media3-exoplayer:1.7.1` in its Android Gradle template.

Exact upstream source inspected: [DefaultTrackSelector.java, androidx/media tag 1.7.1](https://github.com/androidx/media/blob/1.7.1/libraries/exoplayer/src/main/java/androidx/media3/exoplayer/trackselection/DefaultTrackSelector.java), `TextTrackInfo` constructor and its `isWithinConstraints` calculation.

An ordinary language-tagged text track with no selection flags is not eligible merely because its track type is enabled. Eligibility also requires a language or role match, default selection flag, or a forced flag together with an audio-language match. Enabling `selectUndeterminedTextLanguage` alone does not make a nondefault English track match an absent language preference.

The existing preview caption switch only changed text enablement. The repair treats an explicit preview On as a current-session request: preserve a supported existing override or selected track, otherwise prefer the requested language and then a supported available text track. Track indexes are never saved. If tracks are not yet discovered, the request remains in the player's existing selection parameters; discovery can satisfy it once. Off and later explicit saved preferences remain authoritative. No new persistent flag or setting is introduced.

The screenshot shows no available text track rows; it cannot prove whether that stream contains subtitles, lacks them, or has an extraction/decoder issue. The saved language picker always offered English regardless of supplied tracks. The repair labels that saved choice as a preference and explains absent or unsupported current tracks. It does not invent subtitle data or alter extractors, stream transport, or native decoding.

Verification uses actual Android sheet/caption code and Media3 track/selection structures with a controlled ExoPlayer. These tests prove control behavior and resulting track overrides, not provider subtitle availability, decoding, physical caption rendering, or physical Fold behavior.
