#!/usr/bin/env python3
from pathlib import Path
import argparse,hashlib,re,zipfile,copy,json
PARENT='caba1c375cbdee32a0a9a24c7292babfeb6cba157aba8be92a6096137e17e398'
OLD='f6eb05f091bfe7a624105a0a83744a292e229b385d39c1b6a23f8bf954a2522a'
SIG=re.compile(r'META-INF/(?:MANIFEST\\.MF|[^/]+\\.(?:SF|RSA|DSA|EC))$',re.I)
H=lambda b:hashlib.sha256(b).hexdigest()
def main():
 p=argparse.ArgumentParser();p.add_argument('--parent',type=Path,required=True);p.add_argument('--native',type=Path,required=True);p.add_argument('--out',type=Path,required=True);p.add_argument('--proof',type=Path,required=True);a=p.parse_args()
 if H(a.parent.read_bytes())!=PARENT:raise SystemExit('wrong 2103288 evidence-first APK parent')
 native=a.native.read_bytes();new=H(native)
 with zipfile.ZipFile(a.parent) as src:
  if src.testzip() is not None:raise SystemExit('parent CRC failure')
  if H(src.read('lib/arm64-v8a/libkodi.so'))!=OLD:raise SystemExit('wrong protected 2103285 native engine inside 2103288')
  with zipfile.ZipFile(a.out,'w',allowZip64=True) as dst:
   for info in src.infolist():
    if SIG.fullmatch(info.filename):continue
    dst.writestr(copy.copy(info),native if info.filename=='lib/arm64-v8a/libkodi.so' else src.read(info.filename))
 with zipfile.ZipFile(a.out) as z:
  assert z.testzip() is None and H(z.read('lib/arm64-v8a/libkodi.so'))==new
 base=H(a.out.read_bytes());a.proof.parent.mkdir(parents=True,exist_ok=True);a.proof.write_text(json.dumps({
  'schema':1,'parent_apk_sha256':PARENT,'parent_native_sha256':OLD,'native_engine_sha256':new,
  'prepared_base_sha256':base,'only_payload_replaced':'lib/arm64-v8a/libkodi.so',
  'evidence_health_shell_preserved':True,'signatures_removed_for_final_repack':True},indent=2)+'\\n')
 print(base,new)
if __name__=='__main__':main()
