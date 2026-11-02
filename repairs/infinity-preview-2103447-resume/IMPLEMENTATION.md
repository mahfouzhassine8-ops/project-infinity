# Preview-only resume memory

Baseline: exact locked, signed 2103447. Cinematic Light/Dark is a separate retained design lock; this change preserves the existing signed player UI.

## Implementation

- New `InfinityExternalResume` owns `infinity_preview_resume_v1.db` only. Its bounded SQLite records contain keyed hashes, technical media metadata and millisecond positions; no URI strings, credentials, media bytes or persisted provider grants.
- The existing decoder worker performs identity checks and transactional saves. No extra worker, service, polling loop, native patch or UI-thread database operation is added. Active playback uses its existing ticker for a checkpoint every 10 seconds; Pause and decoder release read and save the actual current position. The outgoing video is checkpointed before a new request takes ownership.
- A prepared, seekable video with meaningful saved progress offers Resume or Start Over. Resume waits for actual seek completion before playback. Request generations and the Activity choice token reject superseded requests. Back closes a pending choice without overwriting the prior progress; Start Over removes this logical video's record and aliases.
- A minimum 30 seconds of progress is required for the prompt. The last 30 seconds or 95% of the video resets it, as does completion. Live/nonseekable media does not receive a resume prompt.
- URI/document identity works across callers that pass the same stable identity. An already-granted regular-file descriptor supplies a device/inode/extent alias, allowing different provider authorities for the same backing file. Size, duration, modification time for the same file and a bounded first/last 32 KiB validation fingerprint reject observable media changes. Sampling never merges distinct files by content or name.
- Preview lifecycle restores and explicit new file requests are distinguished. Resume choices do not reopen a provider or create another MediaPlayer. A storage failure reports that memory is unavailable and retains ordinary playback/error handling.

Two boundary regressions were reproduced and repaired before release: a
committed decoder checkpoint now overrides an unupdated zero-valued UI position
on restoration, and document-ID canonicalization requires Android to recognize
the authority as a document provider. Arbitrary provider paths retain their
complete hashed URI, including distinguishing query parameters. The 12 storage
tests and three provider/scheduling boundary tests pass; they are host evidence,
not physical decoding acceptance.

## Limits to verify/disclose

Abrupt process or power loss can lose the interval since the last committed checkpoint (normally at most about 10 seconds, subject to OS scheduling). An orderly Pause/Stop/Back/background checkpoint uses the decoder's actual position; resume decoding remains limited by the format and Android's seek support.

Unrelated cloud/local copies, changing signed URLs and providers that expose no correlatable document/file identity cannot be safely merged. A remote URL or opaque stream with no observable version metadata cannot guarantee detection of a same-duration replacement. No filename guessing, full-video scans or extra network requests are introduced.

The Android fixture uses synthetic granted document/file-provider media, not authenticated MiXplorer/Samsung/Drive accounts. Physical Fold interactions and those applications remain user acceptance checks. No user data, Kodi history or Cobra history is accessed by this implementation or its fixture.

## Preservation

The source guard requires the entire existing activity UI/control-construction suffix and unchanged playback operations to match signed447 source. Compiled comparison preserves 587 unrelated Infinity classes; only Preview engine/activity families and the new helper may differ. APK comparison permits only the Infinity owner DEX, increasing versionCode and truthful Infinity component-version metadata, plus regenerated signatures. Splash/routing DEX, Cobra DEX/components, shared DEX, native libraries, icons, skins, providers and shutdown remain exact. No new release lock is created.
