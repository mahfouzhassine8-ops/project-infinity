# One Fold capture for startup and the older movie

Diagnostic QA 2103520 failed both features in the owner's Fold test.
Use the existing installation and profile for one Terminal session. The
earlier Terminal capture was from 2103518. This is the first capture with
2103520's mutex instrumentation.

1. Unlock the Fold and connect it to the Mac by USB. Allow USB debugging
   if Android prompts you.
2. Download [infinity-520-fold-capture.pyz](infinity-520-fold-capture.pyz)
   into Downloads. Open Terminal and run the following command.

   ```sh
   python3 ~/Downloads/infinity-520-fold-capture.pyz
   ```

3. When Terminal shows **Capture running**, open Infinity normally. If
   Empty Shell appears, leave it visible for about 20 seconds. Keep the
   same capture running if Home becomes usable.
4. From Home, open one older saved movie that previously failed. Choose
   the same playback action and wait for the result.
5. Press **Control-C** in Terminal. Share only the
   `Infinity-520-Fold-*.txt` file whose path Terminal prints. If Empty
   Shell prevents access to Home, share the startup capture from that
   session.

The helper checks that 2103520 is installed. It only reads Android logs and
saves a filtered file on the Mac. The file retains startup milestones, mutex
ownership and saved-route decisions. It excludes titles, media IDs, URLs,
credentials and saved positions. The mutex probe samples attempts pending
for at least 100 ms during the first 20 minutes of the process trace.

A `phase=waiting` row associates a pending lock attempt with the last stable
owner publication for that mutex. Owner zero means the sample had no stable
owner. `phase=completed` reports acquisition and release timestamps and the
wait interval for a slow attempt or long hold. Use the Android PID and native
thread ID to join these events to the same process's interpreter milestones.
The site numbers are 1 for the persistence ledger, 2 for protected writes, and
3 for the Python persistence observer. The line fields refer to the exact
patched native source. A loss, observer start failure, or finite capture
window limits what a missing event can establish.
