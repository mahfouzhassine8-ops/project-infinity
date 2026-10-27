"""Assemble actual owner modules in the original single application container.

Produces an unsigned review APK only. Original-key signing remains gated by
the independent release authority and its actual-payload checks.
"""
import argparse
import copy
from pathlib import Path
import re
import shutil
import struct
from zipfile import ZipFile,ZipInfo,ZIP_DEFLATED
from inventory import APK_SHA,PACKAGE,SIGNATURE,APP,load,save,file_sha,digest,manifest_tree,chunks,string_pool,validate_names
from release_gate import normalize_manifest,require,ANDROID
from manifest import append_strings,start,end,NONE

def manifest(raw,version):
    require(2103420<version<=2100000000,'APP_ROLLBACK')
    before=manifest_tree(raw);tree=copy.deepcopy(before)
    app=next(n for n in tree['children'] if n['tag']=='application')
    original=next(n for n in app['children'] if n['tag']=='service' and n['attributes'][ANDROID+'name']['value']==PACKAGE+'.InfinityExtendedBackgroundService')
    new=copy.deepcopy(original);new['attributes'][ANDROID+'name']['value']=PACKAGE+'.CobraBackgroundService'
    del new['attributes'][ANDROID+'process']
    app['children'].append(new);tree['attributes'][ANDROID+'versionCode']['value']=version
    parts=list(chunks(raw));pool=next(p for _,k,p in parts if k==1)
    revised_pool=append_strings(pool,[PACKAGE+'.CobraBackgroundService']);strings=string_pool(revised_pool)
    def node(n):
        attrs=[]
        for key,value in n['attributes'].items():
            require(key.startswith(ANDROID),'ANDROID_SERVICE_ATTRIBUTE_REQUIRED')
            attrs.append((key.removeprefix(ANDROID),value['type'],value['value']))
        # Binary Android attributes must remain in resource-ID order. The
        # input inventory is sorted by text, so recover order from the old
        # corresponding node's attribute IDs in the resource map.
        ids=next(p for _,kind,p in parts if kind==0x180)
        resource_ids=list(struct.unpack('<'+'I'*((len(ids)-8)//4),ids[8:]))
        attrs.sort(key=lambda a:resource_ids[strings.index(a[0])])
        return start(n['tag'],attrs,strings)+b''.join(node(c) for c in n['children'])+end(n['tag'],strings)
    addition=node(new);output=[];inserted=False;changed=False
    for _,kind,part in parts:
        if kind==1:output.append(revised_pool);continue
        if kind==0x102 and strings[struct.unpack_from('<I',part,20)[0]]=='manifest':
            mutable=bytearray(part);first,step,count=struct.unpack_from('<3H',part,24)
            for i in range(count):
                at=16+first+i*step
                if strings[struct.unpack_from('<I',part,at+4)[0]]=='versionCode':
                    require(part[at+15]==0x10 and struct.unpack_from('<I',part,at+16)[0]==2103420,'BASE_VERSION')
                    struct.pack_into('<I',mutable,at+16,version);changed=True
            part=bytes(mutable)
        if kind==0x103 and strings[struct.unpack_from('<I',part,20)[0]]=='application':
            require(not inserted,'DUPLICATE_APPLICATION');output.append(addition);inserted=True
        output.append(part)
    require(inserted and changed,'MANIFEST_DELTA_INCOMPLETE')
    body=b''.join(output);result=struct.pack('<HHI',3,8,len(body)+8)+body
    require(manifest_tree(result)==tree,'EXISTING_MANIFEST_NODE_CHANGED')
    return result

def assemble(baseline,modules,out,version):
    require(file_sha(baseline)==APK_SHA,'EXACT_SIGNED_BASELINE_REQUIRED')
    require(not out.exists(),'FRESH_OUTPUT_REQUIRED')
    report=load(modules/'MODULE-BUILD.json')
    dex=report['modules'];require(bool(dex),'MISSING_COMPILED_MODULES')
    for name,row in dex.items():require(file_sha(modules/name)==row['sha256'],'MODULE_BYTES_CHANGED')
    # Android 21+ uses native multidex loading. Every original class remains
    # available; physical DEX order is independent of feature ownership.
    order=sorted(dex,key=lambda n:({'CHOOSER_SHELL':0,'MINIMAL_ANDROID_CONTRACT':1,'INFINITY':2,'COBRA':3,'UNRESOLVED':4}[dex[n]['owner']],n))
    out.parent.mkdir(parents=True,exist_ok=True)
    with ZipFile(baseline) as old,ZipFile(out,'w',allowZip64=True) as new:
        validate_names(old)
        revised_manifest=manifest(old.read('AndroidManifest.xml'),version)
        for info in sorted(old.infolist(),key=lambda x:x.filename):
            if info.filename in SIGNATURE or re.fullmatch(r'classes[0-9]*\.dex',info.filename):continue
            record=ZipInfo(info.filename,(2026,10,27,0,0,0));record.compress_type=info.compress_type;record.external_attr=info.external_attr
            with new.open(record,'w',force_zip64=info.file_size>=2**31) as target:
                if info.filename=='AndroidManifest.xml':target.write(revised_manifest)
                else:
                    with old.open(info) as stream:shutil.copyfileobj(stream,target,4*1024*1024)
        for i,name in enumerate(order,1):
            record=ZipInfo('classes'+(str(i) if i>1 else '')+'.dex',(2026,10,27,0,0,0));record.compress_type=ZIP_DEFLATED
            new.writestr(record,(modules/name).read_bytes())
    save(out.with_suffix('.json'),{'status':'UNSIGNED_MODULE_REVIEW_ONLY','apk_sha256':file_sha(out),'versionCode':version,
         'manifest_delta':'One private Cobra service in the existing Cobra process; all existing nodes preserved; versionCode advanced',
         'modules':{('classes'+(str(i) if i>1 else '')+'.dex'):dex[n] for i,n in enumerate(order,1)},
         'release_approved':False,'signed':False})

if __name__=='__main__':
    p=argparse.ArgumentParser()
    for n in ('baseline','modules','out'):p.add_argument('--'+n,type=Path,required=True)
    p.add_argument('--version',type=int,required=True);assemble(**vars(p.parse_args()))
