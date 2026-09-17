#!/usr/bin/env python3
"""Exact locked 2103158 -> 2103159 startup experience bridge plus scoped Cobra navigation cleanup."""
from pathlib import Path
import argparse,hashlib,json,re

ROOT=Path(__file__).resolve().parent
SPLASH=Path('tools/android/packaging/xbmc/src/Splash.java.in')
ACTIVITY=Path('tools/android/packaging/xbmc/src/InfinityLiveActivity.java.in')
SPLASH_REL=str(SPLASH)
ACTIVITY_REL=str(ACTIVITY)
BASE_SPLASH='1ef9e88ec974aef5f88ab51d50de7d28105fa4b3496437694883322ec66dcf44'
BASE_ACTIVITY='60b3a483b8dc11ec8f0280da63fc1892852cf95d30e2f182566830a6962d91b6'
LOCKED='fd2af59bab2edcaea6be9e5046720715e25e64e0'

def sha(value):return hashlib.sha256(value.encode() if isinstance(value,str) else value).hexdigest()
def method(text,name):
 marker=re.compile(r'^  (?:(?:@Override|@SuppressWarnings\([^\n]*\))\s+)?(?:private|public|protected) [^\n;=(){}]*\b'+re.escape(name)+r'\s*\([^\n]*\)\s*\{',re.M)
 found=marker.search(text)
 if not found:raise ValueError('Missing method: '+name)
 brace=text.index('{',found.start());depth=0;quote=None;escape=False
 for i in range(brace,len(text)):
  c=text[i]
  if quote:
   if escape:escape=False
   elif c=='\\':escape=True
   elif c==quote:quote=None
   continue
  if c in ('"',"'"):quote=c;continue
  if c=='{':depth+=1
  elif c=='}':
   depth-=1
   if depth==0:return found.start(),i+1
 raise ValueError('Unclosed method: '+name)

def once(text,old,new,label):
 if text.count(old)!=1:raise ValueError('Expected one '+label+' anchor')
 return text.replace(old,new,1)

def patch_splash(before):
 if sha(before)!=BASE_SPLASH:raise ValueError('Not exact locked 2103158 Splash')
 baseline={}
 for name in ('startXBMC','showExperienceCardSettings','showInfinityExperienceChooser','launchInfinityExperience','onCreate'):
  a,b=method(before,name);baseline[name]=before[a:b]
 a,b=method(before,'showInfinityExperienceChooser');original=before[a:b]
 legacy=original.replace('  private void showInfinityExperienceChooser()', '  private void showLegacyInfinityExperienceChooser()',1)
 wrapper='''  private void showInfinityExperienceChooser()
  {
    ExperienceTheme theme = loadExperienceTheme();
    if (theme == null)
    {
      showLegacyInfinityExperienceChooser();
      return;
    }
    showStyledInfinityExperienceChooser(theme);
  }'''
 addition='\n'.join(p.read_text().rstrip() for p in sorted(ROOT.glob('bridge-*.java.inc')))
 after=before[:a]+wrapper+'\n\n'+legacy+'\n\n'+addition+before[b:]
 for name in ('startXBMC','showExperienceCardSettings','launchInfinityExperience','onCreate'):
  c,d=method(after,name)
  if after[c:d]!=baseline[name]:raise ValueError('Protected Splash behavior changed: '+name)
 c,d=method(after,'showLegacyInfinityExperienceChooser')
 if after[c:d].replace('showLegacyInfinityExperienceChooser','showInfinityExperienceChooser',1)!=original:
  raise ValueError('Legacy chooser fallback is not byte-equivalent')
 for token in ('experience-themed-root','experience-initials','YOUR HOME FOR MOVIES, SHOWS AND MORE','FOCUSED. FAST. POWERFUL.','infinity-experience-chooser'):
  if token not in after:raise ValueError('Missing bridge contract: '+token)
 return after

def patch_activity(before):
 if sha(before)!=BASE_ACTIVITY:raise ValueError('Not exact locked 2103158 Cobra Activity')
 protected={}
 for name in ('showSettings','showCobraHealthCenter','buildPlayer','loadGuideAsync','cobraShowGuideShell','onResume','onPause','onDestroy','showPlayerSettingsDrawer','showCobraChannelActions'):
  a,b=method(before,name);protected[name]=before[a:b]

 a,b=method(before,'cobraDrawerView');view_before=before[a:b]
 # Run 35269563869 proved the exact 2103158 baseline and chooser bridge are good,
 # but the cleanup test was brittle because it required the two Health Center
 # statements to be one byte-contiguous block. Keep the exact BASE_ACTIVITY gate,
 # then identify each locked statement independently and require exactly one of each.
 health_row='    LinearLayout health=cobraDetailRow("health","Health Center","Playback, guide and recovery","cobra-drawer-health",false,()->{closeCobraExperienceDrawer();showCobraHealthCenter();});'
 health_attach='    health.setContentDescription("Health Center");items.addView(health,new LinearLayout.LayoutParams(-1,-2));'
 if view_before.count(health_row)!=1:raise ValueError('Expected exactly one locked drawer Health Center row')
 if view_before.count(health_attach)!=1:raise ValueError('Expected exactly one locked drawer Health Center attachment')
 view_after=view_before.replace(health_row+'\n','',1).replace(health_attach+'\n','',1)
 if health_row in view_after or health_attach in view_after:raise ValueError('Drawer Health Center removal incomplete')
 if 'cobraDetailRow("multi","View"' not in view_after:raise ValueError('View destination lost')
 text=before[:a]+view_after+before[b:]

 a,b=method(text,'toggleCobraDrawer');drawer_before=text[a:b]
 old_footer='    LinearLayout footer=new LinearLayout(this);Button infinity=cobraTextButton("∞  Infinity",dark,()->{closeCobraExperienceDrawer();returnToInfinity();});infinity.setVisibility(mUi.destinationEnabled("INFINITY")?View.VISIBLE:View.GONE);Button power=cobraTextButton("Power",dark,()->{closeCobraExperienceDrawer();showCobraPowerMenu();});footer.addView(infinity,new LinearLayout.LayoutParams(0,dp(50),1));footer.addView(power,new LinearLayout.LayoutParams(0,dp(50),1));panel.addView(footer);'
 new_footer='    LinearLayout footer=new LinearLayout(this);Button power=cobraTextButton("Power",dark,()->{closeCobraExperienceDrawer();showCobraPowerMenu();});footer.addView(power,new LinearLayout.LayoutParams(-1,dp(50)));panel.addView(footer);'
 drawer_after=once(drawer_before,old_footer,new_footer,'drawer footer')
 if 'returnToInfinity()' in drawer_after:raise ValueError('Direct Infinity handoff remains in Cobra drawer')
 if 'showCobraPowerMenu()' not in drawer_after:raise ValueError('Power footer lost')
 text=text[:a]+drawer_after+text[b:]

 a,b=method(text,'showCobraPowerMenu');power_before=text[a:b]
 if power_before.count('"⏻  Exit Infinity"')!=1:raise ValueError('Expected one Exit Infinity label')
 power_after=power_before.replace('"⏻  Exit Infinity"','"⏻  Exit"',1)
 if power_after.replace('"⏻  Exit"','"⏻  Exit Infinity"',1)!=power_before:raise ValueError('Power edit changed more than the label')
 for token in ('Switch to Infinity','returnToInfinity()','finishAndRemoveTask()','"Cancel"'):
  if token not in power_after:raise ValueError('Power contract lost: '+token)
 text=text[:a]+power_after+text[b:]

 for name,original in protected.items():
  c,d=method(text,name)
  if text[c:d]!=original:raise ValueError('Protected Cobra method changed: '+name)
 settings=protected['showSettings']
 if 'showCobraHealthCenter()' not in settings or 'HEALTH CENTER' not in settings.upper():
  raise ValueError('Health Center is not retained inside Cobra Settings')

 c,d=method(text,'cobraDrawerView')
 if '"Health Center"' in text[c:d]:raise ValueError('Health Center still exposed in main drawer')
 c,d=method(text,'showCobraPowerMenu')
 if 'Exit Infinity' in text[c:d] or '"⏻  Exit"' not in text[c:d]:raise ValueError('Power Exit label not simplified')
 return text,{
  'activity_before_sha256':sha(before),
  'activity_after_sha256':sha(text),
  'activity_changed_methods':['cobraDrawerView','toggleCobraDrawer','showCobraPowerMenu'],
  'health_center_settings_retained':True,
  'drawer_direct_infinity_handoff_removed':True,
  'power_exit_label':'Exit',
  'protected_cobra_methods':list(protected),
 }

def main():
 p=argparse.ArgumentParser();p.add_argument('--source',type=Path,required=True);p.add_argument('--receipt',type=Path,required=True);a=p.parse_args()
 receipt=Path('engine/background-resume-source.json');data=json.loads(receipt.read_text())
 if data.get('version_code')!=2103158:raise ValueError('Expected exact reconstructed 2103158')
 for rel,row in data['files'].items():
  if sha((a.source/rel).read_bytes())!=row['after']:raise ValueError('2103158 source receipt drift: '+rel)
 splash_path=a.source/SPLASH;activity_path=a.source/ACTIVITY
 splash_before=splash_path.read_text();activity_before=activity_path.read_text()
 splash_after=patch_splash(splash_before);activity_after,activity_report=patch_activity(activity_before)
 splash_path.write_text(splash_after);activity_path.write_text(activity_after)
 data['files'][SPLASH_REL]={'before':BASE_SPLASH,'after':sha(splash_after)}
 if ACTIVITY_REL not in data['files']:raise ValueError('Activity missing from source receipt')
 data['files'][ACTIVITY_REL]['after']=sha(activity_after)
 receipt.write_text(json.dumps(data,indent=2,sort_keys=True)+'\n')
 report={
  'locked_parent':LOCKED,
  'before_sha256':sha(splash_before),
  'after_sha256':sha(splash_after),
  'protected_methods':['startXBMC','showExperienceCardSettings','launchInfinityExperience','onCreate'],
  'legacy_fallback_preserved':True,
  'native_modified':False,
  'chooser_behavior_owner_preserved':True,
  'physical_device_verified':False,
  'candidate_locked':False,
  **activity_report,
 }
 a.receipt.parent.mkdir(parents=True,exist_ok=True);a.receipt.write_text(json.dumps(report,indent=2)+'\n')
 print('PASS: exact locked 2103158 -> 2103159 experience bridge + scoped Cobra drawer/settings/power cleanup')

if __name__=='__main__':main()
