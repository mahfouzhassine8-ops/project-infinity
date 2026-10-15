#!/usr/bin/env python3
"""Differential source preservation test; never edits the supplied trees."""
import argparse
import importlib.util
from pathlib import Path
import xml.etree.ElementTree as ET

p=argparse.ArgumentParser(description=__doc__)
p.add_argument('--before',type=Path,required=True)
p.add_argument('--after',type=Path,required=True)
a=p.parse_args()

def inventory(root):
    paths=list((root/'tools/android/packaging/xbmc').rglob('*'))+[root/'cmake/scripts/android/Install.cmake']
    return {str(p.relative_to(root)):p.read_bytes() for p in paths if p.is_file()}

before,after=inventory(a.before),inventory(a.after)
allowed={
 'tools/android/packaging/xbmc/src/Main.java.in',
 'tools/android/packaging/xbmc/src/InfinityLiveActivity.java.in',
 'tools/android/packaging/xbmc/src/InfinityExtendedBackgroundService.java.in',
 'tools/android/packaging/xbmc/src/InfinityBackgroundControlActivity.java.in',
 'tools/android/packaging/xbmc/AndroidManifest.xml.in',
 'tools/android/packaging/xbmc/build.gradle.in',
 'cmake/scripts/android/Install.cmake',
}
changed={n for n in before.keys()|after.keys() if before.get(n)!=after.get(n)}
assert changed==allowed,changed^allowed
main='tools/android/packaging/xbmc/src/Main.java.in'
restored=after[main].decode().replace('    InfinityExtendedBackgroundService.sync(this);\n','').replace('    if (isFinishing()) InfinityExtendedBackgroundService.stopForExit(this);\n','')
assert restored.encode()==before[main], 'Main rotation/bridge/media callbacks changed'

ns='{http://schemas.android.com/apk/res/android}'
manifest='tools/android/packaging/xbmc/AndroidManifest.xml.in'
old=ET.fromstring(before[manifest]);new=ET.fromstring(after[manifest])
permission=new.find("uses-permission[@%sname='android.permission.FOREGROUND_SERVICE_SPECIAL_USE']"%ns)
assert permission is not None
new.remove(permission)
app=new.find('application')
service=app.find("service[@%sname='.InfinityExtendedBackgroundService']"%ns)
assert service is not None
assert service.get(ns+'exported')=='false' and service.get(ns+'foregroundServiceType')=='specialUse'
app.remove(service)
control=app.find("activity[@%sname='.InfinityBackgroundControlActivity']"%ns)
assert control is not None and control.get(ns+'exported')=='true'
actions={a.get(ns+'name') for a in control.findall('./intent-filter/action')}
assert actions=={
 'com.projectinfinity.kodi.action.BACKGROUND_MODE_NORMAL',
 'com.projectinfinity.kodi.action.BACKGROUND_MODE_EXTENDED',
}
app.remove(control)
def semantic(node):
    return node.tag,sorted(node.attrib.items()),(node.text or '').strip(),[semantic(c) for c in node]
assert semantic(new)==semantic(old),'Existing manifest activity/provider/permission contract changed'

spec=importlib.util.spec_from_file_location('tests',Path(__file__).with_name('test_background.py'))
mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
path='tools/android/packaging/xbmc/src/InfinityLiveActivity.java.in'
old_live,new_live=before[path].decode(),after[path].decode()
for name in ('returnToInfinity','onUserLeaveHint','onPictureInPictureModeChanged','onConfigurationChanged','onMultiWindowModeChanged','enterCobraPictureInPicture','configureCobraPip'):
    assert mod.method(old_live,name)==mod.method(new_live,name),name
assert 'mPlayer.prepare();\n      startCobraPlayer(mPlayer);' in new_live
assert 'player.prepare(); startCobraPlayer(player);' in new_live
assert 'EXTENDED BACKGROUND MODE' not in new_live, 'Infinity control leaked back into Cobra Settings'
print('PASS: exact seven-file allow-list; native-facing Main contract preserved; Infinity control bridge only; Cobra PiP/Fold/handoff methods preserved')
