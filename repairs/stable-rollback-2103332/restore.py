#!/usr/bin/env python3
"""Exact 2103327/.201 restoration. Version metadata only; not a new shutdown fix."""
import argparse, copy, hashlib, json, struct, zipfile
from pathlib import Path
import xml.etree.ElementTree as ET
APK_SHA='02449fea9c76ad6a370f2ca26a88fdee3a681f83bdc3efa73f8e213f22d4c4d5'
APK331_SHA='b4cf1e83ed44e53b17bb5b8b3c86542eed568ec69a53ab270d2ba67eef4c130d'
NATIVE_SHA='a3f95a64b4433a999df37c18ecc48a3a43876c0cc49ae6c5433e82c98835764c'
SKIN_SHA='c07ac8f44078dae2697a90544ba58ba47523eba766f4986edd15c0414ca611e5'
CERT='d7adeb68e9341596a02bd3262b737a0f45fc6e771ed7e60285437e833b58c6d7'
PACKAGE='com.projectinfinity.kodi'
OLD_NAME='1.0.9-JobManager-Close-RC1'
NEW_NAME='1.0.9-Rollback-2103332-RC1'
SIG={'META-INF/INFINITY.SF','META-INF/INFINITY.RSA','META-INF/MANIFEST.MF'}
MANIFEST='AndroidManifest.xml'
LIB='lib/arm64-v8a/libkodi.so'
ADDON='skin.infinity.diggz/addon.xml'
POWER='skin.infinity.diggz/unified/DialogButtonMenu.xml'

def require(ok,msg):
    if not ok: raise ValueError(msg)
def digest(b): return hashlib.sha256(b).hexdigest()
def file_digest(p):
    h=hashlib.sha256()
    with p.open('rb') as f:
        for b in iter(lambda:f.read(1048576),b''):h.update(b)
    return h.hexdigest()
def u16(b,p):return struct.unpack_from('<H',b,p)[0]
def u32(b,p):return struct.unpack_from('<I',b,p)[0]

def axml(b):
    require(len(b)>40 and u16(b,0)==3 and u16(b,2)==8 and u32(b,4)==len(b),'Invalid binary XML')
    strings=[];loc=[];attrs={};pos=8
    while pos<len(b):
        typ,head,size=struct.unpack_from('<HHI',b,pos)
        require(8<=head<=size and pos+size<=len(b),'Invalid XML chunk')
        if typ==1:
            require(not strings and head>=28 and not (u32(b,pos+16)&0x100),'Expected one UTF16 pool')
            count=u32(b,pos+8);start=u32(b,pos+20)
            require(pos+head+4*count<=pos+size,'Invalid string index')
            for i in range(count):
                a=pos+start+u32(b,pos+head+4*i);length=u16(b,a);n=2
                if length&0x8000:length=((length&0x7fff)<<16)|u16(b,a+2);n=4
                s=a+n;e=s+length*2
                require(e+2<=pos+size and b[e:e+2]==b'\0\0','Invalid UTF16 string')
                strings.append(b[s:e].decode('utf-16le'));loc.append((s,e))
        elif typ==0x102:
            require(strings and head==16,'Unexpected element format')
            if strings[u32(b,pos+20)]=='manifest':
                require(not attrs and u16(b,pos+26)==20,'Unexpected manifest attributes')
                for i in range(u16(b,pos+28)):
                    a=pos+16+u16(b,pos+24)+20*i
                    require(a+20<=pos+size,'Attribute outside element')
                    ns,k,raw=struct.unpack_from('<III',b,a);t=b[a+15];v=u32(b,a+16)
                    name=strings[k]
                    if name in ('package','versionCode','versionName'):
                        require(name not in attrs,'Duplicate identity attribute')
                        attrs[name]={'offset':a,'namespace':strings[ns] if ns<len(strings) else None,
                                     'type':t,'data':v,'value':strings[v] if t==3 else v,
                                     'text_range':loc[v] if t==3 else None}
        pos+=size
    require(pos==len(b) and set(attrs)=={'package','versionCode','versionName'},'Missing identity')
    return attrs

def patch_manifest(b,code=2103332,name=NEW_NAME):
    fields=axml(b);c=fields['versionCode'];n=fields['versionName']
    require(fields['package']['value']==PACKAGE,'Wrong package')
    require(c['type']==16 and c['data']==2103327 and n['value']==OLD_NAME and n['type']==3,'Not original 327 metadata')
    require(c['namespace']==n['namespace']=='http://schemas.android.com/apk/res/android','Wrong namespace')
    require(code>2103327 and len(name.encode('utf-16le'))==len(OLD_NAME.encode('utf-16le')),'Invalid version-only restamp')
    start,end=n['text_range'];a=c['offset']+16
    require(b.count(OLD_NAME.encode('utf-16le'))==1,'Ambiguous version string')
    out=bytearray(b);struct.pack_into('<I',out,a,code);out[start:end]=name.encode('utf-16le');out=bytes(out)
    allowed=set(range(a,a+4))|set(range(start,end))
    require(len(out)==len(b) and all(i in allowed for i,(x,y) in enumerate(zip(b,out)) if x!=y),'Unexpected manifest delta')
    after=axml(out);require(after['versionCode']['data']==code and after['versionName']['value']==name,'Version did not apply')
    return out

def valid_zip(z):
    require(len(z.namelist())==len(set(z.namelist())),'Duplicate ZIP entries')
    require(z.testzip() is None,'ZIP CRC failed')
    require(all(not n.startswith('/') and '..' not in Path(n).parts for n in z.namelist()),'Unsafe ZIP member')

def compare_apk(base,other,code=2103332,name=NEW_NAME):
    require(file_digest(base)==APK_SHA,'Wrong original APK SHA-256')
    with zipfile.ZipFile(base) as a,zipfile.ZipFile(other) as b:
        valid_zip(a);valid_zip(b)
        require(set(a.namelist())-SIG==set(b.namelist())-SIG,'APK file set differs')
        expected=patch_manifest(a.read(MANIFEST),code,name)
        require(b.read(MANIFEST)==expected,'Manifest differs beyond version metadata')
        before={};after={};native={};dex={}
        for n in sorted(set(a.namelist())-SIG-{MANIFEST}):
            one=a.read(n);two=b.read(n);require(one==two,'Protected APK payload changed: '+n)
            before[n]=digest(one);after[n]=digest(two)
            if n.startswith('lib/') and n.endswith('.so'):native[n]=before[n]
            if n.startswith('classes') and n.endswith('.dex'):
                dex[n]=before[n]
                for forbidden in (b'Lcom/projectinfinity/kodi/InfinityClosingActivity;',b'Lcom/projectinfinity/kodi/InfinityCloseProgress;'):
                    require(forbidden not in two,'Experimental class remains')
        require(native.get(LIB)==NATIVE_SHA and len(before)==4170,'Original payload inventory changed')
        require(b'infinity-shutdown-2103330-v1' not in b.read(LIB),'Experimental native engine remains')
        return {'candidate':code,'version_name':name,'package':PACKAGE,'source_apk':2103327,
                'source_apk_sha256':APK_SHA,'apk_sha256':file_digest(other),
                'native_sha256':NATIVE_SHA,'protected_payload_count':len(before),
                'native_libraries':native,'dex_files':dex,'before':before,'after':after,
                'allowed_changes':['AndroidManifest.xml: versionCode/versionName','APK signatures/alignment'],
                'native_rebuilt':False,'dex_recompiled_for_delivery':False,
                'baseline_notification_retained':True,'experimental_activity_absent':True,
                'experimental_phase_reader_absent':True,'shutdown_hang_resolved':None,
                'installed_device_identity_verified':False,'physical_device_verified':False,'locked':False}

def build_apk(base,out):
    require(file_digest(base)==APK_SHA,'Wrong original APK SHA-256')
    out.parent.mkdir(parents=True,exist_ok=True)
    with zipfile.ZipFile(base) as a,zipfile.ZipFile(out,'w') as b:
        valid_zip(a);manifest=patch_manifest(a.read(MANIFEST))
        b.comment=a.comment
        for info in a.infolist():
            if info.filename not in SIG:
                b.writestr(copy.copy(info),manifest if info.filename==MANIFEST else a.read(info.filename))
    return compare_apk(base,out)

def compare_skin(base,other,version='1.0.5.206'):
    require(file_digest(base)==SKIN_SHA,'Wrong original skin ZIP SHA-256')
    with zipfile.ZipFile(base) as a,zipfile.ZipFile(other) as b:
        valid_zip(a);valid_zip(b);require(a.namelist()==b.namelist(),'Skin entries/order changed')
        original=a.read(ADDON);needle=b'version="1.0.5.201"'
        require(original.count(needle)==1,'Ambiguous original skin version')
        require(b.read(ADDON)==original.replace(needle,('version="'+version+'"').encode(),1),'Skin metadata changed beyond version')
        before={};after={}
        for n in a.namelist():
            x=a.read(n);y=b.read(n);before[n]=digest(x);after[n]=digest(y)
            if n!=ADDON:require(x==y,'Protected skin file changed: '+n)
        require(len(before)==2940,'Unexpected skin file count')
        root=ET.fromstring(b.read(ADDON));require(root.get('id')=='skin.infinity.diggz' and root.get('version')==version,'Wrong skin identity')
        for n in b.namelist():
            if n==ADDON or (n.startswith('skin.infinity.diggz/unified/') and n.endswith('.xml')):ET.fromstring(b.read(n))
        power=b.read(POWER)
        for token in [b'Infinity.Close.InProgress',b'CLOSING INFINITY',b'InfinityClosingActivity']:
            require(token not in power,'Experimental Power UI remains')
        imports={x.get('addon'):x.attrib for x in root.find('requires')}
        return {'candidate':version,'source_version':'1.0.5.201','source_zip_sha256':SKIN_SHA,
                'skin_zip_sha256':file_digest(other),'addon_id':root.get('id'),
                'changed_files':[ADDON],'protected_payload_count':2939,'before':before,'after':after,
                'power_menu_sha256':after[POWER],'dependencies':imports,
                'physical_device_verified':False,'installed_skin_verified':False,'locked':False}

def build_skin(base,out):
    require(file_digest(base)==SKIN_SHA,'Wrong original skin ZIP SHA-256')
    out.parent.mkdir(parents=True,exist_ok=True)
    with zipfile.ZipFile(base) as a,zipfile.ZipFile(out,'w') as b:
        valid_zip(a);b.comment=a.comment
        for info in a.infolist():
            data=a.read(info.filename)
            if info.filename==ADDON:
                require(data.count(b'version="1.0.5.201"')==1,'Wrong original skin metadata')
                data=data.replace(b'version="1.0.5.201"',b'version="1.0.5.206"',1)
            b.writestr(copy.copy(info),data)
    return compare_skin(base,out)

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('mode',choices=['build-apk','verify-apk','compare331','build-skin','verify-skin','compare205'])
    for n in ('base','output','proof'):p.add_argument('--'+n,type=Path,required=True)
    a=p.parse_args()
    if a.mode=='build-apk':r=build_apk(a.base,a.output)
    elif a.mode=='verify-apk':r=compare_apk(a.base,a.output)
    elif a.mode=='compare331':
        require(file_digest(a.output)==APK331_SHA,'Wrong 3331 artifact');r=compare_apk(a.base,a.output,2103331,'1.0.9-Rollback-2103331-RC1')
    elif a.mode=='build-skin':r=build_skin(a.base,a.output)
    else:r=compare_skin(a.base,a.output,'1.0.5.205' if a.mode=='compare205' else '1.0.5.206')
    a.proof.parent.mkdir(parents=True,exist_ok=True);a.proof.write_text(json.dumps(r,indent=2)+'\n')
    print(json.dumps({k:v for k,v in r.items() if k not in ('before','after','native_libraries')},indent=2))
if __name__=='__main__':main()
