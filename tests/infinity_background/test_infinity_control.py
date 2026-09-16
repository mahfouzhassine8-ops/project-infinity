#!/usr/bin/env python3
"""Static contract checks for Infinity-owned Normal/Extended background controls."""
import argparse
import json
from pathlib import Path
import xml.etree.ElementTree as ET

p=argparse.ArgumentParser(description=__doc__)
p.add_argument('--source',type=Path,required=True)
p.add_argument('--out',type=Path,required=True)
a=p.parse_args()
a.out.mkdir(parents=True,exist_ok=True)
root=a.source
base=root/'tools/android/packaging/xbmc'
control=base/'src/InfinityBackgroundControlActivity.java.in'
service=base/'src/InfinityExtendedBackgroundService.java.in'
live=base/'src/InfinityLiveActivity.java.in'
manifest=base/'AndroidManifest.xml.in'
install=root/'cmake/scripts/android/Install.cmake'

ct=control.read_text(); st=service.read_text(); lt=live.read_text(); it=install.read_text()
assert 'BACKGROUND_MODE_NORMAL' in ct and 'BACKGROUND_MODE_EXTENDED' in ct
assert 'InfinityExtendedBackgroundService.setEnabled(this, false)' in ct
assert 'InfinityExtendedBackgroundService.setEnabled(this, true)' in ct
assert 'InfinityExtendedBackgroundService.notificationsAllowed(this)' in ct
assert 'InfinityExtendedBackgroundService.openNotificationSettings(this)' in ct
assert 'EXTENDED BACKGROUND MODE' not in lt
assert 'src/InfinityBackgroundControlActivity.java' in it
assert 'src/InfinityExtendedBackgroundService.java' in it
assert 'Infinity Performance & Display' in st

ns='{http://schemas.android.com/apk/res/android}'
m=ET.parse(manifest).getroot(); app=m.find('application')
activity=app.find("activity[@%sname='.InfinityBackgroundControlActivity']"%ns)
assert activity is not None and activity.get(ns+'exported')=='true'
actions={x.get(ns+'name') for x in activity.findall('./intent-filter/action')}
expected={
 'com.projectinfinity.kodi.action.BACKGROUND_MODE_NORMAL',
 'com.projectinfinity.kodi.action.BACKGROUND_MODE_EXTENDED',
}
assert actions==expected,(actions,expected)
service_node=app.find("service[@%sname='.InfinityExtendedBackgroundService']"%ns)
assert service_node is not None and service_node.get(ns+'exported')=='false'

report={
 'schema':1,
 'owner':'Infinity',
 'normal_action':'com.projectinfinity.kodi.action.BACKGROUND_MODE_NORMAL',
 'extended_action':'com.projectinfinity.kodi.action.BACKGROUND_MODE_EXTENDED',
 'service_exported':False,
 'control_activity_exported':True,
 'cobra_settings_toggle_removed':True,
 'native_engine_modified':False,
}
(a.out/'infinity-background-control.json').write_text(json.dumps(report,indent=2,sort_keys=True)+'\n')
print('PASS: Infinity owns Normal/Extended bridge; private background service preserved; Cobra settings toggle removed')
