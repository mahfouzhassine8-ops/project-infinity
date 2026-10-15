# Infinity 2103377 — Rails Startup/Handoff RC1 (experimental)

**Implementation target:** APK native Kodi engine only. User-authorized investigation and isolated test development, **not** promotion or lock.

## Evidence

- 2026-10-15 physical Fold: Movies first -> 10 cards and TV Shows second -> 11 cards both successful.
- Previous TV-first session: Movie directory helper finished 10-card listing and metadata but no skin bind or first rendered card was recorded before touchscreen ANR.
- A Movies request waited ~29.8s in Kodi's low-priority startup job queue in the successful session; the Python helper's catalog work was milliseconds.
- CDirectoryProvider::OnJobComplete has no job ID/URL validation on existing source, potentially allowing stale in-flight callback to overwrite the current provider after a section switch. **This is a proven code race, not proven to be the sole ANR cause.**

## Scope

Reconstruct exact signed Python retirement RC1 engine source, and change **only** xbmc/guilib/listproviders/DirectoryProvider.cpp:
1. Promote strictly scoped plugin://script.infinity.rails/?section=movies|tvshows directory requests from PRIORITY_LOW to PRIORITY_NORMAL. No new workers, no separate queues, no global JobManager changes.
2. While receiving Kodi job callbacks, drop only obsolete Rails results where the job ID or originating URL differs from current active request. Other Kodi directory callback logic unchanged.

Do not touch native shutdown, the 17 required save owners, python interpreter retirement RC1, touch handling, favorites, playback, databases, skin 1.0.5.223, or Rails helper 0.2.5 / 0.2.6. Preserve Mocha menu and physical rollback.

## Tests and limitations

The host test compiles the actual modified callback and scope matcher with controlled Kodi peers. The complete matched ARM64 Kodi engine and signing/payload gates must pass before a device APK is delivered. Queue-priority and old callback tests are **not** Android UI-thread injection; full Fold quick/full shutdown and switching tests remain required. No proof here that this removes the GUI lock owner; if ANRs persist, use per-lock Stability Evidence export rather than further speculative edits.
