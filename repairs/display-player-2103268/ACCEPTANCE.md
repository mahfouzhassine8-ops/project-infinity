# Cobra Display + full-screen Player audit criteria

Locked baseline: `locked-infinity-cobra-2103267-playing-dot-restore-device-passed-20260930`, commit `292351efa4e0840c1f01b343a81e62b8905ba3f0`.
Pro Mode, Infinity skin, native engine, providers, accounts and unrelated navigation are preservation-only.

Acceptance is intended user outcome → actual result → pass/fail/action. A missing physical observation is UNVERIFIED. Existing formula-only tests are implementation consistency evidence, not product acceptance.

## Display intent established before new tests

| Choice | User-visible requirement |
| --- | --- |
| Fold Fit | Proportional balanced fitting, materially less dead space than whole-frame containment on mismatched Fold panes; bounded crop; distinctly gentler than Fill. |
| Fold Fill | Proportional centered minimum crop, covers entire actual viewport. |
| Inherit default | Remove the channel aspect override, follow the current global setting including subsequent default changes; preserve other channel settings. |
| Best Fit | Restore substantially fuller/full viewport utilization reported by user; investigate history. Current physical screenshot's giant pillarboxes fail that expectation. Fullscreen should keep shapes with minimum proportional crop; PiP/preview retain safety whole-frame fitting. |
| Crop / Fill | Centered proportional minimum-crop full-viewport cover. |
| 16:9 / 4:3 | Render the labeled display aspect, centered inside the viewport. Shape change is intentional when source differs. |
| Wide 1.10x / 1.25x / 1.40x | Progressively widen whole-frame fit by the labeled factor, centered; intentional horizontal stretching is disclosed. |
| Short + Wide | Intentional horizontal 1.24x and vertical 0.84x relative to whole-frame fit, centered and disclosed. |
| Zoom 1.25x / 1.50x / 2.00x | Uniform centered enlargement of whole-frame fit by the labeled factor; increasing intentional crop. |
| Custom | Independent 55–180% width/height factors, immediate result after adjustment, isolated per channel, persisted, reachable controls and reset to 100%. |

Best Fit history: 2103151/2103152 reset TextureView view scaling and returned for mode 0, leaving its buffer at the full pane. 2103153 replaced this with an explicit centered containment matrix. The locked 2103207 source contains the same mode 0–11 policy as 2103267. Thus this predates glass/Cinema/2103267. Historical descriptions also say Best Fit preserves source shape and shows the whole frame, conflicting with the user's current screen-fill expectation. The old untransformed buffer can stretch on mismatched viewports; it is not proof of an approved proportional fill. No claim is made that a last device-passed proportional full-pane Best Fit implementation was found.

The user was offered fill-with-proportional-crop versus legacy stretching versus whole-frame bars; no answer was returned. Proceed with the smallest reasonable interpretation of the new brief: restore fullscreen utilization using the already accepted proportional Fill policy, preserve preview/PiP/Pro, disclose the behavior and require physical acceptance. Best Fit, Crop / Fill and Fold Fill intentionally share proportional fullscreen cover geometry on identical inputs; labels/IDs remain for saved-setting compatibility and historical entry points. This is documented, not presented as three different algorithms. Fold Fit stays distinct.

## Player acceptance

Actual Activity views must expose reachable controls within window/safe-area bounds, including 320dp width and large fonts. Pause/Play must reflect the owned player's request/suppression state; real call routing remains device-only.
Display/Channels/Multi-View/More open one active surface, dismiss/back correctly, return focus and retain player/session. Empty fullscreen long-press consumes the hold without opening a menu; tap still toggles chrome. Lock intercepts player actions and exposes unlock without restoring the removed menu.
Channels playing dot uses the existing authoritative session policy and remains independent of focus/selection. Preserve 180ms handoff, 240ms morph, OLED floor, cyan and Night Cinema #FFC247. No redundant PLAYING text.
Timeshift timeline must be owned by actual seekable playback, truthful current/buffer/live ranges, retain drag/end boundaries and Go Live; unavailable/non-live sources cannot claim fake live progress.
Multi-View owns each tile/player separately; audio-owner changes cannot pause peers; transforms cannot leak between tiles; enlarge/return preserves all sessions.
Subtitle Off disables text tracks; chosen tracks/languages/size/adaptation remain synchronized. More entries must route to an observable screen/action, not merely have callbacks.
PiP/background/calls/fold/orientation retain playback owner, position/timeshift and Display selection. PiP's whole-frame fit must restore to the saved actual mode on exit. Ambient/Cinema changes surrounding UI only; video matrix/pixels remain unchanged.

## Verification boundaries

Source preservation + new Android compilation + functional Android/Robolectric + deterministic native-rendered UI + controlled-frame composition + state transitions are required automated layers. Controlled Media3 proxies and diagnostic frames do not prove native decoding, audibility, provider behavior, Samsung PiP/SystemUI, real fold transition or physical timing. Those require the coherent physical Fold checklist before any lock/device-pass claim.
