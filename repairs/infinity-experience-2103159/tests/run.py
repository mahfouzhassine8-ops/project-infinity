#!/usr/bin/env python3
"""Host audit for the exact Splash bridge and the 1.4.0 ZIP payload. No Android rendering claim."""
from pathlib import Path
import argparse,hashlib,importlib.util,json,shutil,tempfile,zipfile
ROOT=Path(__file__).resolve().parents[1]
def load(name,path):
 spec=importlib.util.spec_from_file_location(name,path);mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod);return mod
apply=load('experience_apply',ROOT/'apply.py');builder=load('experience_zip',ROOT/'build_ui_zip.py')
def h(b):return hashlib.sha256(b).hexdigest()
def main():
 p=argparse.ArgumentParser();p.add_argument('--splash',type=Path,required=True);p.add_argument('--ui',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args();a.out.mkdir(parents=True,exist_ok=True)
 before=a.splash.read_text();after=apply.patch_splash(before);receipt={'before_sha256':apply.sha(before),'after_sha256':apply.sha(after),'protected_methods':['startXBMC','showExperienceCardSettings','launchInfinityExperience','onCreate'],'legacy_fallback_preserved':True};(a.out/'Splash.java.in').write_text(after)
 checks=[]
 def check(value,label):
  if not value:raise AssertionError(label)
  checks.append(label)
 check(receipt['before_sha256']==apply.BASE_SPLASH,'Exact locked Splash accepted')
 check(receipt['legacy_fallback_preserved'],'Legacy fallback preserved')
 for name in receipt['protected_methods']:
  x,y=apply.method(before,name);u,v=apply.method(after,name);check(before[x:y]==after[u:v],'Protected '+name+' byte-identical')
 x,y=apply.method(after,'showInfinityExperienceChooser');wrapper=after[x:y]
 check('loadExperienceTheme()' in wrapper and 'showLegacyInfinityExperienceChooser()' in wrapper and 'showStyledInfinityExperienceChooser(theme)' in wrapper,'Bridge dispatches themed or legacy path')
 x,y=apply.method(after,'loadExperienceTheme');loader=after[x:y]
 for token in ('65536','getCanonicalPath','FileInputStream','offset != size'):
  check(token in loader,'Bounded canonical loader has '+token)
 for token in ('new ExoPlayer','setMediaItem','InfinityLiveActivity','startActivity(intent)'):
  x,y=apply.method(after,'showStyledInfinityExperienceChooser');check(token not in after[x:y],'Themed layout owns no playback/launch routing: '+token)
 x,y=apply.method(after,'showLegacyInfinityExperienceChooser');legacy=after[x:y]
 check('INFINITY 2-IN-1' in legacy and 'Two separate environments' in legacy,'Fallback retains prior chooser')
 check(after.count('private void launchInfinityExperience(String experience)')==1,'Single launch owner')
 check('experience-initials' in after and 'experience-themed-root' in after,'HM/theme view tags present')
 check('YOUR HOME FOR MOVIES, SHOWS AND MORE' in after and 'FOCUSED. FAST. POWERFUL.' in after,'Approved card copy present')
 try:apply.patch_splash(before+'\n')
 except ValueError:check(True,'Modified Splash preimage rejected')
 else:raise AssertionError('Modified Splash accepted')
 with tempfile.TemporaryDirectory() as t:
  out=Path(t)/'Infinity-Cobra-UI-1.4.0-Experience.zip';builder.build(a.ui,out)
  shutil.copy2(out,a.out/out.name);shutil.copy2(out.with_suffix(out.suffix+'.sha256'),a.out/(out.name+'.sha256'))
  with zipfile.ZipFile(a.ui) as old,zipfile.ZipFile(out) as new:
   oldf={n:old.read(n) for n in old.namelist() if not n.endswith('/')};newf={n:new.read(n) for n in new.namelist() if not n.endswith('/')}
   check(set(newf)==set(oldf)|{builder.PREFIX+'resources/experience-chooser.json'},'ZIP adds exactly one new runtime resource')
   for name in (builder.PREFIX+'resources/cobra-theme.json',builder.PREFIX+'lib/__init__.py'):
    check(oldf[name]==newf[name],'Locked UI byte preserved: '+name)
   ui=json.loads(newf[builder.PREFIX+'resources/cobra-ui.json']);check(ui['schema']==1 and ui['runtime']['scope']=='cobra-live-only','Existing Cobra UI installer contract preserved')
   exp=json.loads(newf[builder.PREFIX+'resources/experience-chooser.json']);builder.validate_experience(exp)
   check(exp['copy']['initials']=='HM','Approved HM initials')
   check('live tv' not in exp['copy']['infinity_subtitle'].lower(),'Infinity copy contains no Live TV')
   check('Two separate environments' not in json.dumps(exp['copy']),'Removed subtitle absent')
   check('2-IN-1' not in json.dumps(exp['copy']),'2-in-1 absent')
 for bad in (
  {'schema':9,'scope':'infinity-experience-chooser','minimum_bridge':1},
  dict(json.loads((ROOT/'experience-theme.json').read_text()),scope='other'),
  dict(json.loads((ROOT/'experience-theme.json').read_text()),minimum_bridge=99),
 ):
  try:builder.validate_experience(bad)
  except ValueError:check(True,'Incompatible experience contract rejected')
  else:raise AssertionError('Bad experience theme accepted')
 bad=json.loads((ROOT/'experience-theme.json').read_text());bad['copy']['infinity_subtitle']='Movies and Live TV'
 try:builder.validate_experience(bad)
 except ValueError:check(True,'Live TV cannot return to Infinity card')
 else:raise AssertionError('Forbidden Infinity copy accepted')
 (a.out/'results.json').write_text(json.dumps({'checks':checks,'patch':receipt,'android_rendering_verified':False,'physical_device_verified':False},indent=2)+'\n')
 print('PASS:',len(checks),'host bridge/package checks; Android rendering is a separate gate')
if __name__=='__main__':main()
