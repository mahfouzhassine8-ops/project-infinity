#!/usr/bin/env python3
"""Passive DEX format metadata decoder. NO Dalvik code execution or modification."""
import csv, gzip, json, struct, sys, zipfile
from pathlib import Path
APK=Path(sys.argv[1]);OUT=Path(sys.argv[2]);OUT.mkdir(parents=True,exist_ok=True)
def u4(b,at):return struct.unpack_from('<I',b,at)[0]
def readuleb(b,at):
    n=0;shift=0
    for _ in range(5):
        c=b[at];at+=1;n|=(c&127)<<shift
        if c<128:break
        shift+=7
    return n,at
rows=[];methods=[];perdex=[];errors=[]
with zipfile.ZipFile(APK) as z:
    for filename in sorted(x.filename for x in z.infolist() if x.filename.startswith('classes') and x.filename.endswith('.dex')):
        try:
            b=z.read(filename)
            if not (b.startswith(b'dex\n') and len(b)>112):raise ValueError('DEX header/magic invalid')
            sn,so=u4(b,0x38),u4(b,0x3c)
            tn,to=u4(b,0x40),u4(b,0x44)
            mn,mo=u4(b,0x58),u4(b,0x5c)
            cn,co=u4(b,0x60),u4(b,0x64)
            offsets=[u4(b,so+i*4) for i in range(sn)]
            strings=[]
            for off in offsets:
                _,idx=readuleb(b,off)
                end=b.index(0,idx)
                strings.append(b[idx:end].decode('utf-8',errors='replace'))
            types=[strings[u4(b,to+i*4)] for i in range(tn)]
            for i in range(cn):
                t=u4(b,co+i*32)
                rows.append([filename,i,types[t]])
            for i in range(mn):
                cl,pr,n=struct.unpack_from('<HHI',b,mo+i*8)
                methods.append([filename,types[cl],strings[n],pr])
            perdex.append({'name':filename,'bytes':len(b),'string_ids':sn,'type_ids':tn,'method_ids':mn,'class_defs':cn})
        except Exception as e:errors.append({'file':filename,'error':str(e)})
with gzip.open(OUT/'all-dex-defined-classes.csv.gz','wt',encoding='utf8',newline='') as f:
    w=csv.writer(f);w.writerow(['dex','class_index','descriptor']);w.writerows(rows)
with gzip.open(OUT/'all-dex-methods.csv.gz','wt',encoding='utf8',newline='') as f:
    w=csv.writer(f);w.writerow(['dex','class_descriptor','method_name','proto_index']);w.writerows(methods)
patterns=('infinity','cobra','kodi','cast','ambient','control','service','notification','player','receiver','android','rotation','popup','pip','launch','lifecycle','drawer','windows','diagnostic','health','remux')
filtered=[r for r in rows if any(p in r[2].lower() for p in patterns)]
with (OUT/'feature-related-android-classes.csv').open('w',encoding='utf8',newline='') as f:
    w=csv.writer(f);w.writerow(['dex','class_index','descriptor']);w.writerows(filtered)
result={'schema':1,'scope':'Static Android class symbols only; NOT verified behavior',
        'dex_headers':perdex,'total_defined_classes':len(rows),'total_methods':len(methods),
        'filtered_feature_class_count':len(filtered),'errors':errors,
        'warnings':['DEX class names do not verify installed runtime behavior or JNI control flows',
                    'Build includes native C++ libraries not covered by this DEX index']}
(OUT/'android-dex-inventory-summary.json').write_text(json.dumps(result,indent=2))
print(json.dumps(result,indent=2))
