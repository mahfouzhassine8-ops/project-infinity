from zipfile import ZipFile
import struct,hashlib,json
from pathlib import Path
with ZipFile('/tmp/cobra445-signed/Infinity-2103445-Combined-Original-Signer.apk') as z:b=z.read('lib/arm64-v8a/libkodi.so')
assert hashlib.sha256(b).hexdigest()=='151128c176b6094f28bb3fc716cc07c3985a9aa38f1fe41e1bb1424f0285a47e'
h=struct.unpack_from('<16sHHIQQQIHHHHHH',b);assert h[0][:6]==b'\x7fELF\x02\x01' and h[2]==183
sections=[struct.unpack_from('<IIQQQQIIQQ',b,h[6]+i*h[11]) for i in range(h[12])]
strings=sections[h[13]];names=b[strings[4]:strings[4]+strings[5]]
def cstring(data,start):return data[start:data.find(b'\0',start)].decode('utf8',errors='replace')
sec={cstring(names,s[0]):s for s in sections}
records=[]
for s in sections:
 if s[1] not in (2,11):continue
 t=sections[s[6]];st=b[t[4]:t[4]+t[5]]
 for off in range(s[4],s[4]+s[5],s[9]):
  no,info,other,ndx,value,size=struct.unpack_from('<IBBHQQ',b,off)
  if not value:continue
  n=cstring(st,no)
  if n.startswith('_ZN12CVideoPlayerD') or ('CThread' in n and '5Sleep' in n) or ('CJobQueue' in n and 'IsProcessing' in n):records.append(dict(name=n,address=value,size=size))
def fileoff(address):
 for s in sections:
  if s[3]<=address<s[3]+s[5] and s[1]!=8:return s[4]+address-s[3]
 raise ValueError(address)
functions=[];targets=set()
for r in records:
 if not r['name'].startswith('_ZN12CVideoPlayerD'):continue
 calls=[];words=[]
 for delta in range(0,r['size'],4):
  ins=struct.unpack_from('<I',b,fileoff(r['address']+delta))[0]
  if ins&0xfc000000==0x94000000:
   imm=ins&0x03ffffff;imm=imm-(1<<26) if imm&(1<<25) else imm;target=r['address']+delta+imm*4;targets.add(target);calls.append(dict(offset=delta,return_offset=delta+4,target=target))
  if 160<=delta<=208:words.append(dict(offset=delta,word=hex(ins)))
 functions.append(dict(**r,calls=calls,around_plus192=words))
resolved={}
for s in sections:
 if s[1] not in (2,11):continue
 t=sections[s[6]];st=b[t[4]:t[4]+t[5]]
 for off in range(s[4],s[4]+s[5],s[9]):
  no,info,other,ndx,value,size=struct.unpack_from('<IBBHQQ',b,off)
  if value in targets:resolved.setdefault(value,[]).append(cstring(st,no))
for f in functions:
 for c in f['calls']:c['symbols']=sorted(set(resolved.get(c['target'],[])))
build=None
if '.note.gnu.build-id' in sec:
 s=sec['.note.gnu.build-id'];n,d,t=struct.unpack_from('<III',b,s[4]);start=s[4]+12+((n+3)&~3);build=b[start:start+d].hex()
report=dict(artifact='SIGNED2103445_NATIVE_REFERENCE_ONLY; HISTORICAL_ANR_PRODUCER_UNBOUND',library_sha256=hashlib.sha256(b).hexdigest(),build_id=build,functions=functions,related_symbols=records)
Path('/tmp/infinity-external-native-symbols.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps({'library_sha256':report['library_sha256'],'reference_only':report['artifact'],'destructor_offsets':[{'name':f['name'],'address':hex(f['address']),'wait_calls':[c for c in f['calls'] if 160<=c['offset']<=196]} for f in report['functions'] if f['name'].endswith('D1Ev')][:1]},indent=2))
