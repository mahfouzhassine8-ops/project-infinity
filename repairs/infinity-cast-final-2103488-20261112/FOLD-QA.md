# One Cast-only Fold acceptance session

The development base is signed **2103488**. Protected recovery functionality is
**2103486**. Neither is promoted or replaced as an accepted baseline by this QA.

Install the final QA APK as an ordinary update over the current installation.
Keep all profiles, add-ons and settings. Do not uninstall, clear data or force a
lower version. Download the forward recovery for safekeeping; install it only
when deliberately returning to the protected 2103486 functionality.

1. Launch a movie through the existing streaming-provider playback flow. Check
   that regular Movies, Infinity Movies and the existing Continue Watching entry
   still behave normally.
2. Open either existing Cast entry: the icon between Drawer and Volume, or Cast
   to Device immediately below Now Playing. Confirm the title and choose Onn 4K
   or another compatible Google Cast video receiver on the supported local IPv4
   network. Audio-only receivers should not be offered.
3. Observe Connecting / Loading. Confirm the movie itself plays on the TV and
   the dialog says **Now Casting**. Connection alone is not a successful transfer.
4. Check position, Pause/Resume and seeking. Close Controls should dismiss only
   the dialog. Reopen it and use Return to Phone / Disconnect; confirm the movie
   resumes locally at the returned position and the remote session ends.
5. If a source/receiver transfer fails, confirm an understandable failure state,
   continued or restored phone playback, and a usable player. Do not repeatedly
   retry a failing source. Unsupported DRM or codec/manifest combinations remain
   unsupported; they must not be reported as successful Cast playback.
6. Check the same movie's existing Continue Watching/resume presentation after
   real qualifying playback. Saving or selecting a title must create no history.
7. Use normal Power → Exit, then relaunch. Check retained data and the existing
   Movies/TV/Search functionality. Shutdown code and deadlines are unchanged.

This is one combined acceptance session, not a request for repeated experimental
installations. Physical receiver playback, Fold layouts and post-Cast shutdown
remain owner acceptance results until reported. The internal Android probe is a
separate CI package and is never distributed as the owner installer.

Supported delivery includes progressive MP4/M4V/WebM and compatible HLS/DASH
streams using authenticated sender-side manifest/segment proxying. HLS AES-128
identity encryption is delivered through the same selected-peer capability.
DRM, SAMPLE-AES/non-identity key formats, unsupported HLS variable/content-steering
extensions, unavailable source credentials, unsupported receiver codecs and
unsupported receiver routes fail explicitly. No provider implementation or DRM
system is replaced or bypassed.
