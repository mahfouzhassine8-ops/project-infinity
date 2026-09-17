#!/usr/bin/env python3
"""Exact locked 2103158 -> 2103159 startup experience ZIP bridge. Splash-only runtime delta."""
from pathlib import Path
import argparse,hashlib,json,re
ROOT=Path(__file__).resolve().parent
SPLASH=Path('tools/android/packaging/xbmc/src/Splash.java.in')
REL=str(SPLASH)
BASE='1ef9e88ec974aef5f88ab51d50de7d28105fa4b3496437694883322ec66dcf44'
LOCKED='fd2af59bab2edcaea6be9e5046720715e25e64e0'

def sha(value):return hashlib.sha256(value.encode() if isinstance(value,str) else value).hexdigest()
def method(text,name):
 marker=re.compile(r'^  (?:private|public|protected) [^\n;=(){}]*\b'+re.escape(name)+r'\s*\([^\n]*\)\s*\{',re.M)
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
def patch(before):
 if sha(before)!=BASE:raise ValueError('Not exact locked 2103158 Splash')
 baseline={}
 for name in ('startXBMC','showExperienceCardSettings','showInfinityExperienceChooser','launchInfinityExperience','onCreate'):
  a,b=method(before,name);baseline[name]=before[a:b]
 a,b=method(before,'showInfinityExperienceChooser');original=before[a:b]
 legacy=original.replace('  private void showInfinityExperienceChooser()', '  private void showLegacyInfinityExperienceChooser()',1)
 wrapper='''  private void showInfinityExperienceChooser()\n  {\n    ExperienceTheme theme = loadExperienceTheme();\n    if (theme == null)\n    {\n      showLegacyInfinityExperienceChooser();\n      return;\n    }\n    showStyledInfinityExperienceChooser(theme);\n  }'''
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
 return after,{'locked_parent':LOCKED,'before_sha256':sha(before),'after_sha256':sha(after),'protected_methods':['startXBMC','showExperienceCardSettings','launchInfinityExperience','onCreate'],'legacy_fallback_preserved':True,'native_modified':False,'chooser_behavior_owner_preserved':True,'physical_device_verified':False,'candidate_locked':False}
def main():
 p=argparse.ArgumentParser();p.add_argument('--source',type=Path,required=True);p.add_argument('--receipt',type=Path,required=True);a=p.parse_args();path=a.source/SPLASH
 before=path.read_text();after,report=patch(before)
 receipt=Path('engine/background-resume-source.json');data=json.loads(receipt.read_text())
 if data.get('version_code')!=2103158:raise ValueError('Expected exact reconstructed 2103158')
 for rel,row in data['files'].items():
  if sha((a.source/rel).read_bytes())!=row['after']:raise ValueError('2103158 source receipt drift: '+rel)
 path.write_text(after);data['files'][REL]={'before':BASE,'after':sha(after)};receipt.write_text(json.dumps(data,indent=2,sort_keys=True)+'\n')
 a.receipt.parent.mkdir(parents=True,exist_ok=True);a.receipt.write_text(json.dumps(report,indent=2)+'\n');print('PASS: exact locked 2103158 Splash -> ZIP-driven experience theme bridge')
if __name__=='__main__':main()
