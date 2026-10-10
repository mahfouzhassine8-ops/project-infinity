#!/usr/bin/env python3
"""Refresh reviewed performance-script postimages and their exact installer/native pins."""
import hashlib,importlib.util,json,re,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 maps=[]
 for folder,manifest,section in [(ROOT/'runtime/commandcenter/overlay',ROOT/'runtime/commandcenter/manifest.json',None),(ROOT/'installed/overlay/script.infinity.commandcenter',ROOT/'installed/manifest.json','script.infinity.commandcenter')]:
  d=json.loads(manifest.read_text());m=d[section] if section else d
  for name in ('service.py','plugin.py','resume_hub.py'):m['after'][name]=sha(folder/name)
  manifest.write_text(json.dumps(d,indent=2,sort_keys=True)+'\n');maps.append(m['after'])
 contract=ROOT/'runtime/native/overlay/xbmc/platform/android/activity/InfinityScriptCheckpointContracts.cpp'
 def update(match):
  hashes=maps[1] if maps[1]['addon.xml'] in match[2] else maps[0]
  body=re.sub(r'(\{"script.infinity.commandcenter/([^"/]+)", ")[0-9a-f]{64}("\})',lambda x:x[1]+hashes[x[2]]+x[3],match[2])
  return match[1]+body+match[3]
 text,n=re.subn(r'(    \{"script.infinity.commandcenter/(?:service|plugin)\.py",[^\n]+\{\n)(.*?)(    \}\},)',update,contract.read_text(),flags=re.S)
 assert n==4;contract.write_text(text)
 sys.path.insert(0,str(ROOT));import participant_asset
 spec=importlib.util.spec_from_file_location('speed_installed_build',ROOT/'installed/build.py');build=importlib.util.module_from_spec(spec);spec.loader.exec_module(build)
 for name,data in [('InfinityCheckpointAddonInstaller',participant_asset.build()),('InfinityCheckpointController20Installer',build.build('script.infinity.commandcenter'))]:
  p=ROOT/'runtime/android/overlay/tools/android/packaging/xbmc/src'/(name+'.java.in')
  text,n=re.subn(r'(?<!PREVIOUS_)ASSET_SHA256 = "[0-9a-f]{64}"','ASSET_SHA256 = "'+hashlib.sha256(data).hexdigest()+'"',p.read_text());assert n==1;p.write_text(text)
 for group in ('native','android'):
  p=ROOT/'runtime'/group/'manifest.json';m=json.loads(p.read_text())
  for name in m['changed']:m['after'][name]=sha(p.parent/'overlay'/name)
  p.write_text(json.dumps(m,indent=2,sort_keys=True)+'\n')
if __name__=='__main__':main()
