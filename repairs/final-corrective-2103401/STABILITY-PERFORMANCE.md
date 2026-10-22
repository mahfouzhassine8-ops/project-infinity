# Stability and performance evidence

The protected source and 9,404 native inputs were verified before changes. The supplied 2103400 Fold diagnostic includes an Essential-First COMPLETE receipt at 3,448 ms with checkpoint saved, authorization consumed and process death confirmed. Whole-package death was separately false; it is not reclassified as success. That is historical baseline evidence, not a new candidate test.

| Observed operation | Protected baseline | Candidate verification |
| --- | --- | --- |
| Trakt component admission | Rejects shipped bridge because 1.0.5 is hard-coded | Exact candidate bridge/controller accepted; changed/missing/version/path inputs rejected |
| More Info expansion | Second dialog reaches unsupported scrollbar API and raises | One dialog, supported group wrapper, captured text bound and Back returns |
| Provider tap | Completes editor and launches selected provider | Changes selection only, zero completion callbacks |
| Explicit Search | No independent submission control | One completion, selected provider/query/token retained |
| History selection | No universal history surface | Existing query populated, zero provider dispatch |
| Protected persistence | Original participant | Same participant and durable-write proof; no save skipped |

PERFORMANCE-HOST.json contains comparable host geometry timings and exact dialog/callback counts. Geometry is unchanged, so no speedup is claimed. Hash checks and history writes have bounded input sizes. No provider caches, stream resolution, decoder, buffering, or shutdown durability policy is changed.

Whole-app startup, scrolling frame times, artwork load, theme switching, playback return, foreground restoration and Fold reflow were not measured on the user's device. These remain PENDING. Native source preservation, compilation and component execution cannot establish absence of every native runtime lock inversion. The protected lifecycle implementation is retained without speculative fixes.
