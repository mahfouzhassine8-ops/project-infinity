# Networking acceptance review against protected 2103477

The controlled host comparison found no added DNS-cleanup or cancellation delay
from the preserved networking policy. This is not Android execution clearance.

| Controlled five-second libc stall | Baseline pool/options | Candidate Automatic |
| --- | ---: | ---: |
| Timeout return including handle release | 5.00069 s | 5.00065 s |
| Progress callback first requests abort | 0.256186 s | 0.256157 s |
| Abort return including handle release | 5.00056 s | 5.00054 s |

Both variants used the same unchanged curl 8.10 threaded resolver, AF_UNSPEC
hints, a two-second connect budget, a 3.5-second total diagnostic budget, and the
same injected five-second libc lookup. Baseline pool sources match the protected
native source map. The original signed 2103477 ARM64 ELF independently confirms
the threaded libc backend. Exact Android performance equivalence remains untested.

Baseline CurlFile already sets NOSIGNAL and uses the original cancellation flag.
Curl waits for its resolver thread during teardown. The new family policy does
not change that backend. It does change family hints, cached-address selection,
the DNS cache interval, fresh connections after mode changes, and the default
connection ceiling from 30 to at most 15 seconds; those feature effects still
need their relevant Android checks.

## Proposed release contract for owner review

Retain the original resolver. Record the synthetic hard DNS deadline as an
inherited limitation and an unmet additional target, not an introduced regression.
Do not claim its historical failure passed. Automatic's 200 ms Happy Eyeballs
behavior applies after DNS supplies usable addresses; it is not a DNS deadline.
Streaming receives no new total-duration cutoff.

Keep mandatory gates for actual Android operation, family enforcement and
switching, cache/pool isolation, eligible fallback, TLS/SNI/Host preservation,
redirects/proxies/cookies, cancellation and user-visible timing regressions,
crashes/leaks, settings persistence, existing playback/features, and Cobra
isolation. Any demonstrated new failure remains a blocker.

The earlier three-second assertion against a configured 3.5-second total timeout
was corrected with documented 0.25-second scheduling tolerance. The subsequent
2.25-second DNS-cleanup and 3.75-second total-return requirements still FAIL for
both baseline and candidate under this fixture. Their receipts remain unchanged.

Both independent reviewers support this distinction. No replacement resolver,
helper process, QUICK_EXIT, detached-worker shortcut, TLS exception, provider
change, or new production cancellation mechanism has been activated.

The helper experiments are parked and excluded from release inputs. Their latest
resource test failed and is retained as experimental evidence, not represented as
production behavior. Cobra, CC75, skin270 and signed77 remain unchanged by this
comparison. No new version has been reserved, signed APK prepared, or recovery
modified.
