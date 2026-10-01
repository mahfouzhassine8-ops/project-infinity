"""Go to a time in the existing Kodi video; never open or replace a source."""
import math
import re
import xbmc
import xbmcgui

def parse_time(text):
    """Accept seconds, MM:SS or HH:MM:SS; reject ambiguous/nonfinite input."""
    if not isinstance(text, str) or len(text) > 20:
        raise ValueError('Enter seconds, MM:SS or HH:MM:SS.')
    parts = text.strip().split(':')
    if not 1 <= len(parts) <= 3 or not all(re.fullmatch(r'\d+', p) for p in parts):
        raise ValueError('Enter seconds, MM:SS or HH:MM:SS.')
    values = list(map(int, parts))
    if len(values) > 1 and any(v >= 60 for v in values[1:]):
        raise ValueError('Minutes and seconds after a colon must be below 60.')
    total = 0
    for v in values:
        total = total * 60 + v
    return float(total)

def run():
    dialog = xbmcgui.Dialog()
    player = xbmc.Player()
    try:
        if not player.isPlayingVideo() or xbmc.getCondVisibility('Pvr.IsPlayingTV | Pvr.IsPlayingRadio'):
            dialog.ok('Go To Time', 'Available during seekable on-demand video playback.')
            return False
        source = player.getPlayingFile()
        duration = float(player.getTotalTime())
        if not source or source.lower().startswith('pvr://') or not math.isfinite(duration) or duration <= 0:
            dialog.ok('Go To Time', 'This video does not report a seekable duration.')
            return False
        raw = dialog.input('Go To Time — seconds or HH:MM:SS', type=xbmcgui.INPUT_ALPHANUM)
        if not raw:
            return False
        try:
            position = parse_time(raw)
        except ValueError as error:
            dialog.ok('Go To Time', str(error))
            return False
        if not math.isfinite(position) or not 0 <= position < duration:
            dialog.ok('Go To Time', 'Choose a time before the end of this video.')
            return False
        # Dialogs can remain open across a natural end/source switch. Do not seek
        # a different title; no source, title or credential is logged or persisted.
        if (not player.isPlayingVideo() or player.getPlayingFile() != source or
                xbmc.getCondVisibility('Pvr.IsPlayingTV | Pvr.IsPlayingRadio')):
            return False
        current_duration = float(player.getTotalTime())
        if not math.isfinite(current_duration) or abs(current_duration-duration) > 1:
            return False
        player.seekTime(position)
        return True
    except Exception:
        dialog.ok('Go To Time', 'Playback changed or this source could not be seeked. Nothing was restarted.')
        return False

if __name__ == '__main__':
    run()
