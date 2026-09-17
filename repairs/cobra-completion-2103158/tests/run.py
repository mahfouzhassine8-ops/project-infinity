#!/usr/bin/env python3
"""Fail-closed whole-file checks; production recovery inspector runs with explicit host doubles."""
from pathlib import Path
import argparse,importlib.util,json,subprocess,tempfile
ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('completion',ROOT/'apply.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
def run(baseline,out):
 before=baseline.read_text();after,report=m.patch(before);out.mkdir(parents=True,exist_ok=True)
 (out/'InfinityLiveActivity.java.in').write_text(after)
 for wrong in (before+'\n',after):
  try:m.patch(wrong)
  except ValueError:pass
  else:raise AssertionError('Unknown/reapplied preimage accepted')
 protected=('CobraModeLayout','CobraBroadcastRow','CobraMobileChannelRow','CobraCompactChannelRow','CobraPosterChannelCard','CobraFocusQueueRow','CobraLayoutMath','CobraGuideMath')
 for name in protected:
  a,b=m.span(before,name,'class');c,d=m.span(after,name,'class');assert before[a:b]==after[c:d],name
 for name in ('loadGuideAsync','cobraParseGuide','cobraWriteEpgCache','cobraReadEpgCache','cobraDownloadEpg','cobraRefreshGuide','startSinglePlayer','startCobraPreview','setMultiAudio','returnToInfinity','pauseCobraForBackground','resumeCobraAfterBackground','showCobraViewModeMenu','cobraSwitchMode'):
  a,b=m.span(before,name);c,d=m.span(after,name);assert before[a:b]==after[c:d],name
 module=(ROOT/'completion.java.inc').read_text()
 for token in ('.prepare(','.play(','.release(','.setMediaItem(','.setVolume(','.setAudioAttributes(', 'setSurfaceTextureListener(', 'loadLibrary(', 'clearData(', 'Runtime.getRuntime('):assert token not in module,token
 a,b=m.span(after,'toggleCobraDrawer');assert 'VIEW MODES' not in after[a:b] and 'CobraModeLayout.MODES' not in after[a:b]
 java=(ROOT/'tests/RecoveryHost.java.in').read_text()
 for token,name,kind in [('CHOICE','CobraPlaybackChoice','class'),('BUDGET','CobraRecoveryBudget','class'),('RECOVERY','CobraSurfaceRecovery','class'),('INSPECT','cobraInspectSurfaceRecovery','method'),('SUSPEND','cobraSuspendRecovery','method')]:
  a,b=m.span(after,name,kind);java=java.replace('@@'+token+'@@',after[a:b])
 host=out/'host';host.mkdir(exist_ok=True);(host/'RecoveryHost.java').write_text(java)
 p=host/'android/os/SystemClock.java';p.parent.mkdir(parents=True,exist_ok=True);p.write_text('package android.os;public class SystemClock {public static long now;public static long elapsedRealtime(){return now;}}')
 subprocess.run(['javac','--release','8','-encoding','UTF-8','-d',str(host/'classes'),str(p),str(host/'RecoveryHost.java')],check=True)
 result=subprocess.run(['java','-cp',str(host/'classes'),'RecoveryHost'],check=True,capture_output=True,text=True,timeout=30)
 print(result.stdout);(out/'host-output.txt').write_text(result.stdout)
 report.update(host_checks_passed=True,protected_classes=list(protected),android_tested=False,physical_playback_tested=False)
 (out/'results.json').write_text(json.dumps(report,indent=2)+'\n');return report
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--baseline',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args();run(a.baseline,a.out)
