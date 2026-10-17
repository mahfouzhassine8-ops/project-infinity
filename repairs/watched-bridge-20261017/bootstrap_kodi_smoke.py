"""Enable disposable fixture skins, then quit so startup loads the chosen skin."""
import json
from pathlib import Path
import traceback
import xbmc
import xbmcvfs

profile = Path(xbmcvfs.translatePath('special://profile/'))
result = dict(passed=False)
try:
    for name in ('script.infinity.commandcenter', 'skin.infinity.rowverify.before', 'skin.infinity.rowverify.after'):
        response = json.loads(xbmc.executeJSONRPC(json.dumps(dict(jsonrpc='2.0', id=1,
            method='Addons.SetAddonEnabled', params=dict(addonid=name, enabled=True)))))
        if response.get('result') != 'OK': raise RuntimeError(str(response))
    result['passed'] = True
except Exception:
    result['failure'] = traceback.format_exc()
finally:
    (profile / 'watched-bootstrap-result.json').write_text(json.dumps(result, indent=2) + '\n')
    xbmc.executebuiltin('Quit()')
