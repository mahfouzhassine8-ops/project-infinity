"""One optimized observer-validator control; no actual GUI/theme acceptance."""
import hashlib
import json
from pathlib import Path
import sys
from types import ModuleType
from unittest.mock import patch
HERE=Path(__file__).resolve().parent
source=HERE/'tracking_android_observer.py'
labels={'Container(50).NumItems':'1','Container(50).ListItemAbsolute(0).Label':'Host snapshot control',
    'Container(50).ListItemAbsolute(0).FileNameAndPath':'plugin://host.snapshot/control',
    'Container.FolderPath':'plugin://host.snapshot/','Window(Home).Property(Infinity.Theme)':'observed-host-property'}
xbmc=ModuleType('xbmc');xbmc.Player=object;xbmc.getInfoLabel=lambda key:labels.get(key,'');xbmc.getSkinDir=lambda:'skin.infinity.diggz'
addon=ModuleType('xbmcaddon')
def unavailable(aid):raise RuntimeError('Unknown addon id '+aid)
addon.Addon=unavailable
gui=ModuleType('xbmcgui');gui.getCurrentWindowId=lambda:10025;gui.getCurrentWindowDialogId=lambda:0
with patch.dict(sys.modules,dict(xbmc=xbmc,xbmcaddon=addon,xbmcgui=gui,xbmcvfs=ModuleType('xbmcvfs'))):
 ns=dict(__name__='host_optional_theme_control',__file__=str(source))
 exec(compile(source.read_text(),str(source),'exec',optimize=1),ns)
 value=ns['snapshot']()
 if value['theme'] is not None or value['theme_available'] is not False or 'Unknown addon' not in value['theme_error']:
  raise RuntimeError('Unavailable theme policy was guessed or not reported')
 row=value['controls']['50'][0]
 if row['label']!='Host snapshot control' or row['file']!='plugin://host.snapshot/control' or value['folder']!='plugin://host.snapshot/':
  raise RuntimeError('Optional metadata failure discarded source row/path')
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
a=dict(status='PASS_OPTIMIZED_MISSING_OPTIONAL_THEME_OWNER_ROW_PRESERVATION_CONTROL',observer_sha256=sha(source),test_sha256=sha(Path(__file__)),selection_sha256=sha(HERE/'OPTIONAL-THEME-TEST-SELECTION.json'),compiled_optimization=1,actual_SDK_or_GUI_execution=False,theme_acceptance=False,previous_tests_rerun=False)
(HERE/'OPTIONAL-THEME-HOST.json').write_text(json.dumps(a,indent=2)+'\n');print(a['status'])
