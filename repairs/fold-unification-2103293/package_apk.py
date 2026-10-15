#!/usr/bin/env python3
"""Replace only the UI engine and integer versionCode in the exact locked APK."""
from pathlib import Path
import argparse, hashlib, json, re, struct, zipfile
PARENT='c24396f1b60cb934fa9fe10e285101c2ca2d082d283d4a3f91a9dcf7c8a5c819'
NATIVE='36a8feba9e8f7c857ca987b7d6ec868d847fcfc46f5369654ddac3b3e7038b94'
SIGNING=re.compile(r'META-INF/(?:MANIFEST\.MF|[^/]+\.(?:SF|RSA|DSA|EC))$',re.I)
H=lambda b:hashlib.sha256(b).hexdigest()
def version_code(data,new=None):
 b=bytearray(data);pos=8;strings=[];found=[]
 while pos<len(b):
  kind,header,size=struct.unpack_from('<HHI',b,pos);assert size>=header>=8
  if kind==1:
   count,styles,flags,start,_=struct.unpack_from('<IIIII',b,pos+8)
   offsets=struct.unpack_from('<'+'I'*count,b,pos+header)
   def length8(q):
    first=b[q];return (((first&127)<<8)|b[q+1],q+2) if first&128 else (first,q+1)
   for off in offsets:
    q=pos+start+off
    if flags&0x100:
     _,q=length8(q);n,q=length8(q);strings.append(b[q:q+n].decode('utf8'))
    else:
     n=struct.unpack_from('<H',b,q)[0];q+=2
     if n&0x8000:n=((n&0x7fff)<<16)|struct.unpack_from('<H',b,q)[0];q+=2
     strings.append(b[q:q+2*n].decode('utf-16le'))
  if kind==0x102:
   ns,name,astart,asize,count=struct.unpack_from('<IIHHH',b,pos+16)
   if strings[name]=='manifest':
    for i in range(count):
     a=pos+16+astart+i*asize
     if strings[struct.unpack_from('<I',b,a+4)[0]]=='versionCode':
      assert b[a+15] in (0x10,0x11);found.append(struct.unpack_from('<I',b,a+16)[0])
      if new is not None:struct.pack_into('<I',b,a+16,new)
  pos+=size
 assert pos==len(b) and len(found)==1
 return bytes(b),found[0]
def check(parent,final):
 with zipfile.ZipFile(parent) as p,zipfile.ZipFile(final) as f:
  assert p.testzip() is None and f.testzip() is None
  pn={n for n in p.namelist() if not n.endswith('/') and not SIGNING.fullmatch(n)}
  fn={n for n in f.namelist() if not n.endswith('/') and not SIGNING.fullmatch(n)}
  assert pn==fn,(pn-fn,fn-pn)
  changed=[n for n in sorted(pn) if p.read(n)!=f.read(n)]
  assert changed==['AndroidManifest.xml','lib/arm64-v8a/libkodi.so'],changed
  assert version_code(f.read('AndroidManifest.xml'))[1]==2103293
  assert version_code(f.read('AndroidManifest.xml'),2103292)[0]==p.read('AndroidManifest.xml')
  return {'candidate':2103293,'parent_apk_sha256':H(parent.read_bytes()),'apk_sha256':H(final.read_bytes()),'native_sha256':H(f.read('lib/arm64-v8a/libkodi.so')),'changed_payloads':changed,'unchanged_payload_count':len(pn)-2,'dex_and_assets_byte_preserved':True,'unexpected_payload_changes':0,'version_name_inherited_from_2103292':True,'physical_verified':False,'locked':False}
def main():
 a=argparse.ArgumentParser();a.add_argument('command',choices=['build','verify']);a.add_argument('--parent',type=Path,required=True);a.add_argument('--native',type=Path);a.add_argument('--out',type=Path,required=True);a.add_argument('--proof',type=Path,required=True);v=a.parse_args()
 assert H(v.parent.read_bytes())==PARENT
 if v.command=='build':
  lib=v.native.read_bytes();assert H(lib)!=NATIVE and lib[:4]==b'\x7fELF'
  with zipfile.ZipFile(v.parent) as p,zipfile.ZipFile(v.out,'w') as out:
   assert H(p.read('lib/arm64-v8a/libkodi.so'))==NATIVE
   for info in p.infolist():
    if SIGNING.fullmatch(info.filename):continue
    data=p.read(info.filename)
    if info.filename=='lib/arm64-v8a/libkodi.so':data=lib
    elif info.filename=='AndroidManifest.xml':data,old=version_code(data,2103293);assert old==2103292
    out.writestr(info,data)
 r=check(v.parent,v.out);v.proof.write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(r))
if __name__=='__main__':main()
