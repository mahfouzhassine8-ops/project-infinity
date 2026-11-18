# Cast reliability QA 2103514 / recovery 2103515

Foundation: authenticated original-signed 2103512. The existing Kodi engine and completed DEX artifact are reused. No owner data was accessed.

## Confirmed defects and corrections

- Conservative source working-set planning could reject valid requests before reading. Bounded origin/cache accounting now separates actual network ingress from bounded replay, retaining the 128 MiB physical read ceiling.
- Valid larger resources exceeded whole-fragment output buffering and failed flush below the read budget. Cast-owned bounded paged output publishes only complete validated fragments, with a 64 MiB aggregate limit and cancellation-safe ownership.
- Empty source hvcC plus in-band parameter sets only at the first keyframe could leave later independent fragments undecodable. Verified source VPS/SPS/PPS bootstrap Cast initialization without altering source video packets.
- Strict integration caught a new internal-mux boundary timestamp shift before release. Fresh bounded internal muxers preserve exact source video packet timestamps and the canonical AAC sample clock.
- Target prebuffering, seek coalescing and actual-contiguous-span delivery accounting replace duplicate or irrelevant warm-up credit. Hardware phase timings remain explicit; no physical throughput is inferred.

## Retained verification

- Component44220512115: production DEX and exact class-delta gate passed.
- ARM64/Android44230184774: original engine/JNI integration, complete authenticated resources above14 MB, ranges, 81 coalesced seeks, H.264/AAC Android playback/seek, source packet/timestamp checks, exact1125-entry AAC grid, cancellation110 ms and zero remaining native contexts.
- Staging44231874837: exact four candidate member changes and7773 unchanged; recovery two metadata changes and7775 unchanged.
- Preparation44232787000: original owner bundles, runtime ownership and exact proposal verification passed; original-key signing follows registry and independent review.

Eight Cast production source files change. Packaging metadata and scoped CI/release evidence are separately accounted for. Cobra2103445, Kodi, shutdown, providers, Search, Watchlist, Continue Watching, Video Lock, UI and settings remain protected.

## Limits

Receiver SDK310 does not independently identify a decoder fault. The source defects were reproduced; equivalence to every receiver failure is unproven. CI Main10 decoding was unsupported and is not recorded as playback success. Physical Fold Main10/hardware throughput, thermal behavior, sustained television playback, phone handoff and post-Cast shutdown require owner acceptance. Shutdown code was unchanged and no shutdown test was selected. Small-raster long/high-byte-rate fixtures do not qualify4K hardware performance.

Forward recovery515 restores exact signed512 runtime content at a higher version; it is not an automatic baseline promotion.
