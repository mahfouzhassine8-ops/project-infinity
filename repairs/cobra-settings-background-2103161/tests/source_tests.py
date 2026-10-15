#!/usr/bin/env python3
from pathlib import Path
import argparse,importlib.util,json
ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('p161',ROOT/'apply.py');p=importlib.util.module_from_spec(spec);spec.loader.exec_module(p)
def method(text,name):
 a,b=p.span(text,name);return text[a:b]
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--source',type=Path,required=True);ap.add_argument('--out',type=Path,required=True);args=ap.parse_args();args.out.mkdir(parents=True,exist_ok=True)
 before={rel:(args.source/rel).read_text() for rel in p.HASHES}
 for rel,text in before.items():assert p.sha(text)==p.HASHES[rel],('preimage',rel,p.sha(text))
 after={p.ACT:p.patch_activity(before[p.ACT]),p.SPLASH:p.patch_splash(before[p.SPLASH]),p.RENDER:p.patch_renderer(before[p.RENDER]),p.THEME:p.patch_theme(before[p.THEME])}
 checks=0
 for rel,text in after.items():assert text!=before[rel];checks+=1
 protected=['onResume','onPause','onStop','pauseCobraForBackground','resumeCobraAfterBackground','rememberAndPauseCobraPlayer','startCobraPlayer','buildPlayer','startSinglePlayer','cobraLayoutGuide','cobraRenderGuideBrowser','cobraSavePreferences','cobraPreferenceKey']
 found=[]
 for name in protected:
  try:b=method(before[p.ACT],name);a=method(after[p.ACT],name)
  except ValueError:continue
  assert b==a,name;found.append(name);checks+=1
 picker=method(after[p.ACT],'showCobraBackgroundModePicker')
 for token in ['InfinityExtendedBackgroundService.setEnabled(this,false)','InfinityExtendedBackgroundService.setEnabled(this,true)','InfinityExtendedBackgroundService.notificationsAllowed(this)','InfinityExtendedBackgroundService.openNotificationSettings(this)']:
  assert token in picker,token;checks+=1
 assert 'getSharedPreferences(' not in picker and 'putBoolean(' not in picker;checks+=1
 settings=method(after[p.ACT],'showSettings')
 for token in ['cobra_background_mode','cobra_visual_theme_state','cobra-visual-theme-controls:previous','cobra-visual-theme-controls:builtin','INSTALL COBRA UI / VISUAL THEME ZIP']:
  assert token in settings,token;checks+=1
 splash=method(after[p.SPLASH],'showVisualExperienceScene')
 for token in ['setOnApplyWindowInsetsListener','getSystemWindowInsetTop','getSystemWindowInsetBottom','requestApplyInsets']:
  assert token in splash,token;checks+=1
 for name in ['launchInfinityExperience','showExperienceCardSettings','showInfinityExperienceChooser']:
  assert method(before[p.SPLASH],name)==method(after[p.SPLASH],name),name;checks+=1
 renderer=after[p.RENDER]
 assert 'startsWith("cobra-visual-theme-controls")' in renderer;checks+=1
 for token in ['setMediaItem','ExoPlayer','TextureView.set','release()','prepare()']:
  assert token not in method(renderer,'restoreBuiltIn')+method(renderer,'restorePrevious'),token;checks+=1
 assert 'VISUAL THEME RUNTIME 2\\n' in after[p.ACT];checks+=1
 assert 'description()+\"\\n\\nReset and rollback change presentation only.' in after[p.RENDER];checks+=1
 assert 'description()+\"\n\nReset and rollback change presentation only.' not in after[p.RENDER];checks+=1
 assert 'BUILD=2103161' in after[p.THEME];checks+=1
 result={'checks':checks,'protected_activity_methods':found,'after_sha256':{k:p.sha(v) for k,v in after.items()},'background_contract':'existing InfinityExtendedBackgroundService Normal/Extended; no new preference','safe_area':'system window insets applied to themed chooser root','official':False}
 (args.out/'source-tests.json').write_text(json.dumps(result,indent=2)+'\n')
 print('PASS:',checks,'source assertions; protected methods:',len(found))
if __name__=='__main__':main()
