#!/usr/bin/env python3
from pathlib import Path
import argparse,hashlib,re,zipfile,copy,json
PARENT='64ed5ce79096a3e09d02907cf72d3a5c4ad20186da231898c92db83e540d266b'
OLD='f6eb05f091bfe7a624105a0a83744a292e229b385d39c1b6a23f8bf954a2522a'
SIG=re.compile(r'META-INF/(?:MANIFEST\\.MF|[^/]+\\.(?:SF|RSA|DSA|EC))$',re.I)
H=lambda b:hashlib.sha256(b).hexdigest()
def main():
 p=argparse.ArgumentParser();p.add_argument('--parent',type=Path,required=True);p.add_argument('--native',type=Path,required=True);p.add_argument('--out',type=Path,required=True);p.add_argument('--proof',type=Path,required=True);a=p.parse_args()
 if H(a.parent.read_bytes())!=PARENT:raise SystemExit('wrong 2103285 APK parent')
 native=a.native.read_bytes();new=H(native)
 with zipfile.ZipFile(a.parent) as src:
  if H(src.read('lib/arm64-v8a/libkodi.so'))!=OLD:raise SystemExit('wrong 2103285 native parent')
  with zipfile.ZipFile(a.out,'w',allowZip64=True) as dst:
   for info in src.infolist():
    if SIG.fullmatch(info.filename):continue
    dst.writestr(copy.copy(info),native if info.filename=='lib/arm64-v8a/libkodi.so' else src.read(info.filename))
 with zipfile.ZipFile(a.out) as z:
  assert z.testzip() is None and H(z.read('lib/arm64-v8a/libkodi.so'))==new
 base=H(a.out.read_bytes());a.proof.write_text(json.dumps({'schema':1,'parent_apk_sha256':PARENT,'parent_native_sha256':OLD,'native_engine_sha256':new,'prepared_base_sha256':base,'only_payload_replaced':'lib/arm64-v8a/libkodi.so','signatures_removed_for_final_repack':True},indent=2)+'\\n')
 print(base,new)
if __name__=='__main__':main()
