# Cobra 2103271 Sports Data RC1 — acceptance contract

2103269 remains the locked rollback baseline. 2103270 is the failed-on-device Sports Hub candidate. 2103271 changes only the live Sports data path and version metadata.

- Replace deprecated ESPN multi-day range scoreboard requests with supported single-day requests.
- Fetch day pages with bounded concurrency and a small in-memory cache.
- Retry ESPN's alternate site host when the primary site host fails.
- Preserve existing Sports Hub parsing, My Teams, Hide Scores, channel resolver, Watch Live, recording handoff and Smart Multi-View ownership.
- Preserve all locked Live TV/player/provider/native/skin behavior.
- Distinguish a successful empty schedule from a true feed outage.
- Include actionable HTTP/network cause text when a league actually fails.
- Automated green is not a device lock. Real Fold network/data/channel/Multi-View testing is still required.
