"""Disposable Android proof: Kodi SELECTED bundled add-on versions from the APK.

Diagnostic script is never packaged into the distributed Infinity APK.
The ten approved IDs are fixed in the source: never parse a JSON list from Kodi's shell-like addon parameter bridge. The
actual Kodi UID resolves the paths; a host receipt pins each selected manifest
hash. This cannot certify native Close, data durability or physical Fold.
"""
from pathlib import Path

PROBE_ID = "script.infinity.bundleprobe"
SCRIPT = '''import hashlib, json, os, sys
import xbmcaddon, xbmcvfs

root = xbmcvfs.translatePath('special://profile/infinity-all-in-one-selected.json')
names = ["resource.images.recordlabels.white","resource.images.studios.white","script.infinity.addonrecovery","script.infinity.commandcenter","script.infinity.rails","script.infinity.uirepair","script.infinity.watchedbridge","script.skinshortcuts","service.infinity.compat","skin.infinity.diggz"]
if len(sys.argv) < 2 or not sys.argv[1]:
    raise ValueError('Missing exact Kodi owner argument')
report = {'scope':'actual Kodi selected addon paths; no input/Close writes',
          'owner':sys.argv[1], 'pid':os.getpid(), 'addons':{}}
for name in names:
    row={'addon_id':name}
    try:
        addon=xbmcaddon.Addon(name)
        folder=xbmcvfs.translatePath(addon.getAddonInfo('path'))
        marker=os.path.join(folder,'addon.xml')
        row.update(path=folder, version=addon.getAddonInfo('version'),
                   addon_xml_exists=os.path.isfile(marker))
        if os.path.isfile(marker):
            with open(marker,'rb') as f:row['addon_xml_sha256']=hashlib.sha256(f.read()).hexdigest()
    except Exception as e:
        row['error']=type(e).__name__+': '+str(e)[:180]
    report['addons'][name]=row
with open(root+'.tmp','w') as f:json.dump(report,f,indent=2)
os.replace(root+'.tmp',root)
'''


def stage(target):
    folder = Path(target) / PROBE_ID
    folder.mkdir()
    (folder / "default.py").write_text(SCRIPT)
    (folder / "addon.xml").write_text(
        '<addon id="' + PROBE_ID + '" name="Infinity bundled add-on CI proof" '
        'version="1.0.0" provider-name="Infinity CI"><requires>'
        '<import addon="xbmc.python" version="3.0.0"/></requires>'
        '<extension point="xbmc.python.script" library="default.py"/>'
        '<extension point="xbmc.addon.metadata">'
        '<summary lang="en_GB">Disposable installed-source check only</summary>'
        '<description lang="en_GB">Never shipped to users</description>'
        '<platform>all</platform><license>GPL-2.0-or-later</license>'
        '</extension></addon>')
    return folder
