#!/usr/bin/env python3
import argparse,sys,xml.etree.ElementTree as ET
from pathlib import Path
import live_apply
p=argparse.ArgumentParser();p.add_argument('--source',type=Path,required=True);p.add_argument('--proof',type=Path,required=True);a=p.parse_args()
live_apply.verify(a.source,a.proof)
base=a.source.parent/'parent-extracted/shell-kodi';prefix=Path('tools/android/packaging/xbmc/src')
def require(c,m):
 if not c:raise AssertionError(m)
def text(n):return(a.source/prefix/n).read_text()
for n in ['InfinityExitCompletion.java.in','InfinityCloseNativeLease.java.in','InfinityKodiShutdown.java.in','Main.java.in','InfinityHealthExport.java.in']:
 require((a.source/prefix/n).read_bytes()==(base/prefix/n).read_bytes(),'Shutdown owner changed: '+n)
g=text('InfinityCloseGuardService.java.in')
for token in ['static final long MAX_PROTECTION_MS=150000;','static final int BIND_FLAGS=Context.BIND_IMPORTANT;','return START_NOT_STICKY;',
 'ready.setData(target.bundle())','InfinityKodiShutdown.ownerAlive(getFilesDir(),target.pid,target.owner)',
 'ui.postDelayed(poll,500)','stopForeground(true);stopSelf();','new InfinityCloseProgress.Reader',
 '.notify(NOTICE,notice(phase.text))','setForegroundServiceBehavior(Notification.FOREGROUND_SERVICE_IMMEDIATE)']:
 require(token in g,'Guard contract missing: '+token)
r=text('InfinityCloseProgress.java.in');card=text('InfinityClosingActivity.java.in')
for content in (r,card):
 for forbidden in ['System.exit(', 'killProcess(', 'forceStopPackage(', 'System.loadLibrary(', 'new XBMCJsonRPC(', 'startService(', 'startForegroundService(']:
  require(forbidden not in content,'Presentation is not read-only: '+forbidden)
require('new RandomAccessFile(file,"r")' in r,'Trace read is not read-only')
require('setIndeterminate(animate)' in card,'Popup must not invent a percentage')
old=(base/prefix/'InfinityPowerControlActivity.java.in').read_text();new=text('InfinityPowerControlActivity.java.in')
force='      } else if (InfinityExitCompletion.FORCE.equals(action))'
require(old[old.index(force):]==new[new.index(force):],'Force Close changed')
manifest=ET.parse(a.source/'tools/android/packaging/xbmc/AndroidManifest.xml.in').getroot();ns='{http://schemas.android.com/apk/res/android}'
app=manifest.find('application');nodes=[n for n in app.findall('activity') if n.get(ns+'name')=='.InfinityClosingActivity'];require(len(nodes)==1,'Popup not registered exactly once')
node=nodes[0];require(ns+'process' not in node.attrib and node.get(ns+'exported')=='false','Popup not private/default-process')
app.remove(node)
# Source formatting differs around the insertion; compare semantic XML structures.
def canonical(node):return(node.tag,dict(node.attrib),tuple(canonical(c) for c in node))
require(canonical(manifest)==canonical(ET.parse(base/'tools/android/packaging/xbmc/AndroidManifest.xml.in').getroot()),'Unrelated manifest delta')
print('PASS: real-stage reader, independent private UI, original native owners and Force Close preserved')
