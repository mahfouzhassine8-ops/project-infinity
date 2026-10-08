#!/usr/bin/env python3
"""Version-only restamp: exact locked APK 2103327 -> 2103331, no native/DEX/layout changes."""
import argparse, copy, hashlib, json, struct, zipfile
from pathlib import Path
OLD_CODE=2103327
NEW_CODE=2103331
OLD_NAME='1.0.9-JobManager-Close-RC1'
NEW_NAME='1.0.9-Rollback-2103331-RC1'
PARENT_SHA='02449fea9c76ad6a370f2ca26a88fdee3a681f83bdc3efa73f8e213f22d4c4d5'
LIB_SHA='a3f95a64b4433a999df37c18ecc48a3a43876c0cc49ae6c5433e82c98835764c'
PACKAGE='com.projectinfinity.kodi'
MANIFEST='AndroidManifest.xml'
LIB='lib/arm64-v8a/libkodi.so'
SIGNATURE={'META-INF/INFINITY.SF','META-INF/INFINITY.RSA','META-INF/MANIFEST.MF'}
sha=lambda data:hashlib.sha256(data).hexdigest()
u16=lambda data,pos:struct.unpack_from('<H',data,pos)[0]
u32=lambda data,pos:struct.unpack_from('<I',data,pos)[0]

def read_axml(blob):
    assert len(blob)>40 and u16(blob,0)==3 and u16(blob,2)==8 and u32(blob,4)==len(blob)
    pos=8
    strings=[]
    attrs={}
    while pos<len(blob):
        typ,hsize,size=struct.unpack_from('<HHI',blob,pos)
        assert hsize>=8 and size>=hsize and pos+size<=len(blob)
        if typ==1:
            assert not strings and hsize>=28 and (u32(blob,pos+16)&0x100)==0, 'Expected UTF16 pool'
            count=u32(blob,pos+8)
            strings_start=u32(blob,pos+20)
            for i in range(count):
                ofs=u32(blob,pos+hsize+4*i)
                a=pos+strings_start+ofs
                count16=u16(blob,a)
                headerlen=2
                if count16&0x8000:
                    count16=((count16&0x7fff)<<16)|u16(blob,a+2)
                    headerlen=4
                b=a+headerlen
                e=b+count16*2
                assert e+2<=pos+size and blob[e:e+2]==b'\0\0'
                strings.append(blob[b:e].decode('utf-16le'))
        elif typ==0x102:
            assert strings and hsize==16
            name=u32(blob,pos+20)
            if strings[name]=='manifest':
                assert not attrs
                attribute_start=u16(blob,pos+24)
                attribute_size=u16(blob,pos+26)
                attribute_count=u16(blob,pos+28)
                assert attribute_size==20 and attribute_count<100
                for i in range(attribute_count):
                    a=pos+16+attribute_start+i*attribute_size
                    namespace,attr_name,raw=struct.unpack_from('<III',blob,a)
                    dtype=blob[a+15]
                    value=u32(blob,a+16)
                    key=strings[attr_name]
                    if key in ('versionCode','versionName','package'):
                        attrs[key]={'offset':a,'namespace':strings[namespace] if namespace<len(strings) else None,
                                    'raw':raw,'type':dtype,'data':value,
                                    'value':strings[value] if dtype==3 and value<len(strings) else None}
        pos+=size
    assert pos==len(blob)
    return attrs

def patched_manifest(blob):
    assert len(OLD_NAME)==len(NEW_NAME)==26
    fields=read_axml(blob)
    code,name,package=(fields[x] for x in ('versionCode','versionName','package'))
    assert code['namespace']=='http://schemas.android.com/apk/res/android' and code['type']==0x10 and code['data']==OLD_CODE
    assert name['namespace']=='http://schemas.android.com/apk/res/android' and name['type']==3 and name['value']==OLD_NAME
    assert package['value']==PACKAGE
    old=OLD_NAME.encode('utf-16le')
    new=NEW_NAME.encode('utf-16le')
    assert blob.count(old)==1
    b=bytearray(blob)
    struct.pack_into('<I',b,code['offset']+16,NEW_CODE)
    off=blob.index(old)
    b[off:off+len(old)]=new
    result=bytes(b)
    fields2=read_axml(result)
    assert fields2['versionCode']['data']==NEW_CODE
    assert fields2['versionName']['value']==NEW_NAME
    assert fields2['package']['value']==PACKAGE
    differences={i for i,(x,y) in enumerate(zip(blob,result)) if x!=y}
    allowed=set(range(code['offset']+16,code['offset']+20))|set(range(off,off+len(old)))
    assert differences and differences<=allowed and len(blob)==len(result)
    return result

def verify_payload(parent,output):
    with zipfile.ZipFile(parent) as base, zipfile.ZipFile(output) as result:
        assert base.testzip() is None and result.testzip() is None
        old=set(base.namelist())
        new=set(result.namelist())
        assert old-SIGNATURE==new-SIGNATURE, 'File paths added or lost'
        untouched=0
        for path in sorted(old-SIGNATURE):
            orig=base.read(path)
            actual=result.read(path)
            if path==MANIFEST:
                assert actual==patched_manifest(orig), 'Manifest differs from exact two-field change'
            else:
                assert orig==actual, 'Unrelated file changed: '+path
                untouched+=1
        assert sha(result.read(LIB))==LIB_SHA, 'Locked engine mutated'
    return untouched

def restamp(parent,output,proof):
    assert sha(parent.read_bytes())==PARENT_SHA, 'Not exact locked 2103327 APK'
    with zipfile.ZipFile(parent) as base:
        assert base.testzip() is None and len(base.namelist())==len(set(base.namelist()))
        manifest=patched_manifest(base.read(MANIFEST))
        output.parent.mkdir(parents=True,exist_ok=True)
        with zipfile.ZipFile(output,'w',allowZip64=True) as archive:
            for item in base.infolist():
                if item.filename in SIGNATURE: continue
                archive.writestr(copy.copy(item),manifest if item.filename==MANIFEST else base.read(item.filename))
    untouched=verify_payload(parent,output)
    result={'parent_code':OLD_CODE,'new_code':NEW_CODE,'parent_sha256':PARENT_SHA,
            'version_name':NEW_NAME,'unsigned_sha256':sha(output.read_bytes()),
            'unchanged_payload_entries':untouched,'native_sha256':LIB_SHA,
            'version_metadata_only':True,'release_signing_required':True,
            'device_verified':False,'locked':False}
    proof.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result,indent=2))

if __name__=='__main__':
    p=argparse.ArgumentParser()
    p.add_argument('source',type=Path)
    p.add_argument('out',type=Path)
    p.add_argument('proof',type=Path)
    a=p.parse_args()
    restamp(a.source,a.out,a.proof)
