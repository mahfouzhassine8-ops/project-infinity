"""Observable finite QA work reached via a genuine Kodi button onclick."""
from pathlib import Path
import json
import sys
import time
import xbmc
sys.dont_write_bytecode=True
sys.path.insert(0,'/workspace/project-infinity/repairs/infinity-2103436-end-to-end-loading/overlay/script.infinity.commandcenter')
from action_loading import preparation
out=Path('/tmp/infinity-kodi-renderer/evidence')
trace=out/'click-trace.jsonl'
def record(state):
    with trace.open('a') as f:f.write(json.dumps(dict(state=state,time=time.monotonic()))+'\n')
record('invoked')
with preparation('native-click-fixture'):
    record('preparing')
    xbmc.sleep(1800) # QA work only; no production delay or provider timing claim.
record('completed')
