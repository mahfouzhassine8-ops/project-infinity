# Combined Movies / Continue Playing / Cast QA

Accepted base remains **2103486**. This is one experimental combined candidate,
not production acceptance or an automatic baseline promotion.

Install the original-key QA APK over the existing installation. Do not uninstall,
clear data, reset Kodi, or replace provider settings. The separately labelled
forward recovery is for returning to accepted 2103486 functionality; its higher
APK/component versions let Android and authenticated modules accept recovery
without a downgrade or removing user data.

Perform one combined session:

1. Open regular Movies and verify the existing source selection and Resume
   prompt. Resume or play a known movie normally.
2. Open Infinity Movies → Watchlist and select an existing movie. Its verified
   original provider route should reach source selection/playback. Existing
   memberships and working TV navigation must remain intact.
3. After real qualifying partial playback, stop and inspect Home Continue
   Playing and Infinity Movies continuation/resume. Merely saving/browsing must
   create no progress. Original duration, progress, hidden and watched rules
   remain in force; the earlier Sacrifice record was not available for inspection.
4. During supported video playback, use the Cast icon between Drawer and Volume,
   or Cast to Device immediately below Now Playing. Select a compatible Google
   Cast video receiver on the same supported local IPv4 network. Check playback,
   pause, seek and Return to Phone / Disconnect.
5. Use normal Power → Exit, then reopen and verify the same settings, saved
   content and accounts. Shutdown source and safeguards are unchanged.

Cast currently supports progressive MP4/M4V/WebM transports. Adaptive HLS/DASH,
DRM, unsupported Kodi transport options, audio-only receivers and unsupported
receiver network routes are refused while phone playback remains available.
The original provider URI, query and authentication headers remain on the phone.
Receiver transfer and physical Fold layouts are acceptance checks, not claimed
by SDK/component or host tests.

The owner decides acceptance. If reverting is necessary, install the matching
higher-version forward recovery over the QA installation; retain all user data.
