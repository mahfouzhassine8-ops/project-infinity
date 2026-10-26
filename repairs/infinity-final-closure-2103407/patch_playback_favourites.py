"""Six-member signed414->415 correction; no native or shared behavior edits."""
import hashlib
import json
from pathlib import Path

CC='script.infinity.commandcenter'
ROOT=Path(__file__).parent


def substitutions(name):
    if name=='addon.xml':return [('version="0.3.5.44"','version="0.3.5.45"')]
    if name=='service.py':
        fragment=(ROOT/'native_playback_capture.py').read_text().rstrip()+'\n\n\n'
        return [
            ('def _continue_player_item(player_id):',fragment+'def _continue_player_item(player_id):'),
            ("    return item if isinstance(item, dict) else {}\n\n\ndef _continue_show_identity",
             "    if not isinstance(item, dict):\n        item = {}\n    return item if item.get('type') in ('movie', 'episode') else _continue_native_item(item)\n\n\ndef _continue_show_identity"),
            ("    source = str(item.get('file') or xbmc.getInfoLabel('Player.Filenameandpath') or '').strip()\n",
             "    source = str(item.get('file') or xbmc.getInfoLabel('Player.Filenameandpath') or '').strip()\n    # Retain the verified identity and fresh resolver route, never an expiring\n    # stream URL from the native-tag fallback as a saved replay destination.\n    if item.get('infinity_transient_playback_source'):\n        source = ''\n")]
    if name=='plugin.py':return [
        ("    matches = [value for value in (favourites or {}).get('favourites', [])\n",
         "    if not isinstance(favourites, dict):\n        return None, None\n    rows = favourites.get('favourites')\n    if rows is None:\n        rows = []  # Kodi returns null for an empty native Favorites collection.\n    if not isinstance(rows, list) or any(not isinstance(value, dict) for value in rows):\n        return None, None\n    matches = [value for value in rows\n")]
    raise ValueError('Unowned playback/Favorites source')


def patch(name,raw):
    pins=json.loads((ROOT/'PLAYBACK-FAVOURITES-415-PLAN.json').read_text())['source_preimages']
    if hashlib.sha256(raw).hexdigest()!=pins.get(name):
        raise ValueError('Exact signed414 source required')
    text=raw.decode();result=text;pairs=substitutions(name)
    for old,new in pairs:
        if result.count(old)!=1:raise ValueError('Playback/Favorites source boundary differs')
        result=result.replace(old,new,1)
    inverse=result
    for old,new in reversed(pairs):
        if inverse.count(new)!=1:raise ValueError('Playback/Favorites inverse is ambiguous')
        inverse=inverse.replace(new,old,1)
    if inverse!=text:raise ValueError('Unrelated source changed')
    if name.endswith('.py'):compile(result,name,'exec',dont_inherit=True)
    return result.encode()
