# Signed504 Cast investigation — engineering checkpoint

Foundation: signed2103504, APK SHA256 ab9104471c729751d6127cc4dfc6e98d8bb4c916212c356ce9c0295b2a0c5234. Frozen source checkpoint df2fab727635f8bd9e30f03202e86d028b861ed3. No older payload substituted.

## Established evidence

Session connection and LOAD followed by IDLE/ERROR4 establish receiver media failure, not its decoder/HTTP cause. The exact owner source and receiver detailed error are unavailable. No additional owner capture or test requested.

InfinityCastSession checks VIDEO_OUT and uses the Default Media Receiver. This is not codec negotiation. Google's canDisplayType API runs on the receiver, not the phone. Google's media table permits HEVC Main10/L5.1 on several devices and lists Dolby as passthrough; the observed HEVC profile is not itself a demonstrated invalidity.

InfinityCastRemux.cpp State::inspect, Output::begin and State::segment select/copy EAC3 into multiplexed fragmented MP4. InfinityCastRemux.playlist advertises ec-3 and InfinityCastRelay exposes that as HLS. Jellyfin commit bc567fd0488aee29ef8b48394ec5e43be30ffe84 explicitly stopped offering Dolby for this delivery path while retaining eligible complete-MP4 passthrough. This establishes a compatibility concern, not the physical Fold cause.

## Executed selected tests

The exact504 native first-fragment matrix isolates H264/AAC, H264/EAC3, HEVC Main10 L153/AAC and HEVC Main10 L153/EAC3. All completed software decode, but timestamp warnings remain in commands.log; timestamp acceptance is NOT PASS.

Actual Chromium156 MSE accepted H264/AAC init+fragment append/buffering; H264/EAC3 was unsupported. Both HEVC cases were unsupported on this Linux environment. The harness does not render video and these results do not establish ONN firmware support.

An additional host conversion proof copied all192 H264 and95 HEVC video packets byte-for-byte while converting audio to AAC-LC stereo. Full output decoded. This uses host FFmpeg CLI and establishes neither Android encoder performance nor a safe integration into JIT fragments.

Existing signed504 engine exports EAC3 decoder, AAC encoder, FIFO/resampler/frame APIs. No Kodi-engine rebuild is indicated. Export availability does not prove encoder registration or device performance.

## Narrow implementation requirement and remaining gate

An isolated Cast audio adapter must convert only incompatible EAC3→multiplexed-fMP4 delivery, preserve existing AAC/direct-MP4 paths and every video packet/timestamp, emit real AAC configuration, and retain authenticated input and existing relay ownership.

AAC requires a global sample clock and frame grid across video cues. FFmpeg6 AAC frames and encoder initial padding are both1024 samples. Decode/resample/encode delay and final padding must be handled explicitly; current use_editlist=0 provides no assumed trimming. Reopening an encoder at each cue without verified pre-roll loses synchronization. Replaying from movie start for every seek violates current bounded I/O/deadline behavior.

Required before integration/signing: deterministic fragments for out-of-order and cache-evicted requests, adjacent audio coverage without duplicate/gap, nonzero-offset seeks, final padding, multichannel downmix, Android encoder execution/performance, cancellation/drain, and the existing native/relay preservation gates. Attribute current timestamp warnings separately. No production shortcut or compatibility relabeling was applied.

## Release status

No production files changed. No native engine or DEX rebuilt. No version reserved, no new APK signed or published. Signed504 and recovery505 remain unchanged. Receiver playback, phone return and physical acceptance are unverified. No non-Cast functionality, profiles, settings, stores or shutdown code changed.
