#!/usr/bin/env python3
import argparse,difflib
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('--base',type=Path,required=True);p.add_argument('--source',type=Path,required=True);a=p.parse_args()
result=[]
for name in ['InfinityLiveActivity.java.in','CobraProUi.java.in']:
 rel='tools/android/packaging/xbmc/src/'+name
 result+=difflib.unified_diff((a.base/rel).read_text().splitlines(True),(a.source/rel).read_text().splitlines(True),fromfile='a/'+rel,tofile='b/'+rel)
Path(__file__).with_name('source.patch').write_text(''.join(result))
