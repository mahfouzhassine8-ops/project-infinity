# SPDX-License-Identifier: GPL-2.0-or-later
"""One-shot configuration for the native audio-policy hook; not a service."""
import json
import os
import tempfile

import xbmc
import xbmcgui
import xbmcvfs

AUTO = {"schema": 1, "video": "movie", "music": "music", "ui": "sonification"}
LEGACY = {"schema": 1, "video": "music", "music": "music", "ui": "music"}


def write_policy(path, policy):
    """Same-directory atomic replacement, with no half-written configuration."""
    parent = os.path.dirname(path)
    os.makedirs(parent, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix=".infinity-audio-", dir=parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as stream:
            json.dump(policy, stream, sort_keys=True)
            stream.write("\n")
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def main():
    dialog = xbmcgui.Dialog()
    if xbmcgui.Window(10000).getProperty("Infinity.AudioPolicyApi") != "1":
        dialog.ok("Infinity Audio Policy", "This APK does not expose native Audio Policy API 1. No settings were changed.")
        return
    if xbmc.Player().isPlaying():
        dialog.ok("Stop playback first", "Stop the video or music completely, not just Pause. Then open Infinity Audio Policy again.")
        return
    choice = dialog.select("Infinity Audio Policy", [
        "Auto — video as MOVIE; music as MUSIC (default)",
        "Legacy — MUSIC classification for all audio (comparison)",
        "About this test / current configuration",
    ])
    if choice < 0:
        return
    path = xbmcvfs.translatePath("special://profile/infinity-audio-policy.json")
    if choice == 2:
        policy = AUTO
        try:
            with open(path, encoding="utf-8") as stream:
                policy = json.loads(stream.read(4097))
        except (OSError, ValueError):
            pass
        dialog.textviewer("Infinity Audio Policy — API 1", "Native audio classification only. No sound effects, Samsung entitlement or guaranteed Audio Eraser support.\n\n" + json.dumps(policy, indent=2))
        return
    # Recheck after the modal dialog in case another controller started playback.
    if xbmc.Player().isPlaying():
        dialog.ok("Playback started", "Stop playback before changing the policy. Nothing was changed.")
        return
    try:
        write_policy(path, AUTO if choice == 0 else LEGACY)
        dialog.ok("Infinity Audio Policy", "Saved. The next playback uses the selected native audio classification. No app or engine rebuild is needed for this setting.")
    except OSError as error:
        xbmc.log("Infinity Audio Policy: cannot save configuration: " + str(error), xbmc.LOGERROR)
        dialog.ok("Infinity Audio Policy", "Could not save the policy. Your previous configuration was not replaced.")


if __name__ == "__main__":
    main()
