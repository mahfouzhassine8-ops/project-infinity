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

pcs={'weather_worker':0x01927b24,'job_worker':0x0197f298,'directory_worker':0x01a705a4,'script_result_wait':0x021ecb38}
found=[];capacity=[]
for s in sections:
 if s[1] not in (2,11):continue
 t=sections[s[6]];st=b[t[4]:t[4]+t[5]]
 for off in range(s[4],s[4]+s[5],s[9]):
  no,info,other,ndx,value,size=struct.unpack_from('<IBBHQQ',b,off)
  if not value or not size or (info&15)!=2:continue
  n=cstring(st,no)
  if 'CJobManager' in n and 'GetMaxWorkers' in n:
   for section in sections:
    if (section[2]&6)==6 and section[3]<=value<section[3]+section[5] and section[1]!=8:
     start=section[4]+value-section[3];words=[hex(struct.unpack_from('<I',b,start+i)[0]) for i in range(0,size,4)];capacity.append({'name':n,'address':hex(value),'size':size,'arm64_words':words})
  for tag,pc in pcs.items():
   if value<=pc<value+size:found.append({'provided_reference':tag,'pc':hex(pc),'symbol':n,'base':hex(value),'offset':pc-value,'size':size})
def unique(rows):return list({json.dumps(r,sort_keys=True):r for r in rows}.values())
report={'status':'READ_ONLY_SIGNED445_REFERENCE; HISTORICAL_PRODUCER_UNBOUND','library_sha256':hashlib.sha256(b).hexdigest(),'provided_PC_matches':unique(found),'capacity_function':unique(capacity)}
Path('/tmp/infinity-external-worker-reference.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report,indent=2))
