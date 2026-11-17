"""Read-only reverse APK linkage and unchanged external dispatch contract.

Use after component compilation or during staging; no need to rebuild DEX.
"""
from pathlib import Path
from zipfile import ZipFile
import json,re,sys
CAST=Path(__file__).resolve().parents[1]/'infinity-movies-continue-cast-2103486-20261112/cast'
sys.path.insert(0,str(CAST))
from dex_contract import Dex
def flags(d):
 classes={};methods={};fields={}
 for n in range(d.u(96)):
  at=d.u(100)+n*32;name=d.types[d.u(at)];classes[name]=d.u(at+4);pos=d.u(at+24)
  if not pos:continue
  def read():
   nonlocal pos
   value=0;shift=0
   while True:
    b=d.data[pos];pos+=1;value|=(b&127)<<shift
    if not b&128:return value
    shift+=7
  counts=[read() for _ in range(4)]
  for group,count in enumerate(counts):
   index=0
   for _ in range(count):
    index+=read();access=read()
    if group>=2:read();methods[d.methods[index]]=access
    else:fields[d.fields[index]]=access
 return classes,methods,fields
def verify(apk,component):
 old={};new={};original_flags=({}, {}, {});candidate_flags=({}, {}, {});external=[];all_defs={}
 with ZipFile(apk) as z:
  for name in z.namelist():
   if re.fullmatch(r'classes\d*\.dex',name):
    d=Dex(z.read(name))
    if name=='classes6.dex':old=d.classes;original_flags=flags(d)
    else:external.append(d);all_defs.update(d.classes)
 for p in Path(component).glob('*.dex'):
  d=Dex(p.read_bytes());new.update(d.classes)
  for i,m in enumerate(flags(d)):candidate_flags[i].update(m)
 all_defs.update(new);checked=[]
 def resolve(owner,name,signature,kind,seen=None):
  seen=set() if seen is None else seen
  if owner in seen:return None
  seen.add(owner);definition=all_defs.get(owner)
  if not definition:return None
  table=candidate_flags[1 if kind=='methods' else 2]
  if (owner,name,signature) in table:return owner,table[(owner,name,signature)]
  if name in ('<init>','<clinit>'):return None
  for parent in [definition['parent']]+definition['interfaces']:
   if parent:
    match=resolve(parent,name,signature,kind,seen)
    if match:return match
  return None
 for d in external:
  for kind,refs in [('methods',d.methods),('fields',d.fields)]:
   for owner,name,signature in refs:
    if owner not in old:continue
    assert owner in new and (original_flags[0][owner]&0x201)==(candidate_flags[0][owner]&0x201),('external class dispatch changed',owner)
    before=original_flags[1 if kind=='methods' else 2].get((owner,name,signature));after=resolve(owner,name,signature,kind)
    assert after is not None,('external member missing',owner,name,signature)
    if before is not None:
     assert (before&8)==(after[1]&8),('staticness changed',owner,name)
     if before&1:assert after[1]&1,('public access reduced',owner,name)
     if before&4:assert after[1]&5,('protected access reduced',owner,name)
    checked.append([kind,owner,name,signature])
 # JNI/reflection names are intentionally kept by the established Cast rules.
 for name,signature in [('begin','(Ljava/lang/String;[B[BJJ)V'),('offer','([BJ)V'),('finish','()[B'),('abortSegment','()V'),('qualifyDelivery','(JJ)V')]:assert (name,signature) in new['Lcom/projectinfinity/kodi/InfinityCastHardwareVideo;']['methods']
 for root in ('InfinityCastOptions','InfinityCastDialog','InfinityCastSession','InfinityCastNative','InfinityCastRemuxNative'):assert 'Lcom/projectinfinity/kodi/'+root+';' in new
 return {'status':'PASS_RETAINED_APK_CALLER_ACCESS_STATICNESS_AND_CAST_ENTRYPOINTS','external_members_checked':checked,'added':sorted(set(new)-set(old)),'removed':sorted(set(old)-set(new))}
if __name__=='__main__':print(json.dumps(verify(sys.argv[1],sys.argv[2]),indent=2))
