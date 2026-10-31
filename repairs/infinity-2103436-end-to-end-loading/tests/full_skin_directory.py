"""Finite native GetDirectory fixture; no external provider/performance claim."""
from pathlib import Path
import json
import sys
import time
from urllib.parse import parse_qs
import xbmc
import xbmcgui
import xbmcplugin

params=parse_qs(sys.argv[2].lstrip('?'));name=params.get('case',['unknown'])[0]
out=Path('/tmp/infinity-full-skin-evidence')
def event(state):
    with (out/'directory-trace.jsonl').open('a') as f:f.write(json.dumps(dict(case=name,state=state,time=time.monotonic(),window=xbmcgui.getCurrentWindowId()))+'\n')
event('provider_entered')
if name!='fast-empty':xbmc.sleep(4500)
if name!='fast-empty':xbmcplugin.addDirectoryItem(int(sys.argv[1]),'file:///tmp/qa-only.mp4',xbmcgui.ListItem(label='QA '+name+' result'),False)
event('before_end_directory')
xbmcplugin.endOfDirectory(int(sys.argv[1]),succeeded=True,cacheToDisc=False)
event('returned')
