#!/usr/bin/env python3
"""Guard the intentional 2103159 Cobra presentation-only cleanup."""
from pathlib import Path
import argparse,hashlib,importlib.util,json

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('experience_apply',ROOT/'apply.py')
apply=importlib.util.module_from_spec(spec);spec.loader.exec_module(apply)

def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def section(text,name):
 a,b=apply.method(text,name);return text[a:b]
def require(ok,msg):
 if not ok:raise AssertionError(msg)

def main():
 p=argparse.ArgumentParser();p.add_argument('--before',type=Path,required=True);p.add_argument('--after',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args()
 before=a.before.read_text();after=a.after.read_text();a.out.mkdir(parents=True,exist_ok=True)
 require(sha(a.before)==apply.BASE_ACTIVITY,'wrong locked 2103158 Activity input')
 expected,report=apply.patch_activity(before);require(after==expected,'delivered Activity differs from audited cleanup patch')
 view=section(after,'cobraDrawerView');drawer=section(after,'toggleCobraDrawer');power=section(after,'showCobraPowerMenu');settings=section(after,'showSettings')
 require('"View"' in view and '"Health Center"' not in view,'main drawer must keep View and remove Health Center')
 require('returnToInfinity()' not in drawer and 'showCobraPowerMenu()' in drawer,'drawer footer must expose Power only')
 require('Switch to Infinity' in power and '"⏻  Exit"' in power and 'Exit Infinity' not in power and '"Cancel"' in power,'Power sheet labels wrong')
 require('returnToInfinity()' in power and 'finishAndRemoveTask()' in power,'Power callbacks changed')
 require('showCobraHealthCenter()' in settings and 'HEALTH CENTER' in settings.upper(),'Health Center missing from Settings')
 for name in ('buildPlayer','loadGuideAsync','cobraShowGuideShell','onResume','onPause','onDestroy','showPlayerSettingsDrawer','showCobraChannelActions','showCobraHealthCenter'):
  require(section(before,name)==section(after,name),'protected runtime method changed: '+name)
 result={'before_sha256':sha(a.before),'after_sha256':sha(a.after),'changed_methods':report['activity_changed_methods'],'drawer_health_removed':True,'settings_health_retained':True,'drawer_infinity_handoff_removed':True,'power_labels':['Switch to Infinity','Exit','Cancel'],'protected_runtime_methods_verified':9,'physical_device_verified':False}
 (a.out/'cobra-ui-cleanup.json').write_text(json.dumps(result,indent=2)+'\n')
 print('PASS: Cobra drawer/settings/power cleanup is presentation-only and matches the approved contract')
if __name__=='__main__':main()
