"""Immutable per-owner payload bundles and the sole combined APK assembler."""
import argparse
from pathlib import Path
import re
import struct
from zipfile import ZipFile,ZipInfo,ZIP_DEFLATED
from inventory import APK_SHA,PACKAGE,CERT_SHA,SIGNATURE,HERE,load,save,canonical,digest,file_sha,validate_names
from assemble_modules import manifest as initial_manifest
from release_gate import normalize_manifest,require,component_digest

OWNED=('INFINITY','COBRA','CHOOSER_SHELL','MINIMAL_ANDROID_CONTRACT')
VERSIONS={'INFINITY':'2103420.isolation.1','COBRA':'bundled-2103420.isolation.1',
          'CHOOSER_SHELL':'2103420.container.1','MINIMAL_ANDROID_CONTRACT':'isolation-contract.1'}
SCHEMAS={'INFINITY':'original-2103420','COBRA':'original-plus-settings-snapshot-v1',
         'CHOOSER_SHELL':'original-launch-preference','MINIMAL_ANDROID_CONTRACT':'owner-durability-v1'}

def record(name,compressed=True):
    info=ZipInfo(name,(2026,10,27,0,0,0));info.compress_type=ZIP_DEFLATED if compressed else 0
    info.external_attr=0o100644<<16;return info

def set_version(raw,version):
    normalized,previous=normalize_manifest(raw)
    old=struct.pack('<I',previous)
    positions=[i for i in range(len(raw)-3) if raw[i:i+4]==old and normalized[i:i+4]==b'\0'*4]
    require(len(positions)==1,'ONE_TYPED_VERSION_OFFSET')
    at=positions[0];result=raw[:at]+struct.pack('<I',version)+raw[at+4:]
    require(normalize_manifest(result)==(normalized,version),'MANIFEST_MUTATED_OUTSIDE_VERSION')
    return result

def pack(baseline,modules,ownership,out,source):
    require(file_sha(baseline)==APK_SHA,'EXACT_BASELINE')
    require(re.fullmatch('[0-9a-f]{40}',source) is not None,'EXACT_SOURCE')
    out.mkdir();classes=load(ownership/'CLASSES.json.gz');review=load(ownership/'OWNERSHIP.json');built=load(modules/'MODULE-BUILD.json')
    require(review['direct_infinity_cobra_feature_edges']==0,'CROSS_FEATURE_IMPORT')
    require(set(classes)==set(built['classes']),'INCOMPLETE_REVIEW')
    for n,c in classes.items():require({k:c[k] for k in ('owner','sha256')}==built['classes'][n],'REVIEW_MODULE_MISMATCH:'+n)
    catalog={'schema':1,'package':PACKAGE,'certificate_sha256':CERT_SHA,'source':source,'bundles':{},'release_approved':False}
    with ZipFile(baseline) as original:
        raw_manifest=initial_manifest(original.read('AndroidManifest.xml'),2103421)
        for owner in OWNED:
            meta={'schema':1,'owner':owner,'version':VERSIONS[owner],'settings_schema':SCHEMAS[owner],
                  'approved_source':source,'payload':{},'dex':{},'members':{},'contract':'isolation-v1'}
            path=out/(owner+'.zip')
            with ZipFile(path,'w') as bundle:
                for n,c in sorted(classes.items()):
                    if c['owner']==owner:meta['payload']['class:'+n]={'owner':owner,'sha256':c['sha256']}
                for n,d in sorted(built['modules'].items()):
                    if d['owner']!=owner:continue
                    require(all(classes[c]['owner']==owner for c in d['classes']),'MIXED_OWNER_DEX')
                    raw=(modules/n).read_bytes();require(digest(raw)==d['sha256'],'MUTATED_DEX')
                    key='dex/'+Path(n).name;require(key not in meta['dex'],'DUPLICATE_DEX')
                    bundle.writestr(record(key),raw);meta['dex'][key]=d['sha256']
                for n,d in sorted(review['members'].items()):
                    if d['owner']!=owner or n in SIGNATURE or re.fullmatch(r'classes\d*\.dex',n):continue
                    raw=raw_manifest if n=='AndroidManifest.xml' else original.read(n)
                    normalized=normalize_manifest(raw)[0] if n=='AndroidManifest.xml' else raw
                    meta['payload']['member:'+n]={'owner':owner,'sha256':digest(normalized)}
                    meta['members'][n]={'sha256':digest(raw),'compress_type':original.getinfo(n).compress_type,
                                        'external_attr':original.getinfo(n).external_attr}
                    bundle.writestr(record('payload/'+n),raw)
                meta['digest']=component_digest(meta['payload'],owner)
                bundle.writestr(record('component.json'),canonical(meta))
            catalog['bundles'][owner]={'file':path.name,'sha256':file_sha(path),'version':meta['version'],
                'digest':meta['digest'],'approved_source':source,'settings_schema':meta['settings_schema']}
    save(out/'catalog.json',catalog)
    return catalog

def read_bundle(path,expected):
    require(file_sha(path)==expected['sha256'],'BUNDLE_HASH_MISMATCH')
    with ZipFile(path) as z:
        validate_names(z);meta=load_bytes(z.read('component.json'))
        require(meta['owner'] in OWNED,'UNOWNED_COMPONENT')
        for key in ('version','digest','approved_source','settings_schema'):require(meta[key]==expected[key],'COMPONENT_BINDING:'+key)
        require(meta['digest']==component_digest(meta['payload'],meta['owner']),'COMPONENT_PAYLOAD_DIGEST')
        require(all(v['owner']==meta['owner'] for v in meta['payload'].values()),'CROSS_OWNER_PAYLOAD')
        required={'component.json'}|set(meta['dex'])|{'payload/'+n for n in meta['members']}
        require(set(z.namelist())==required,'UNDECLARED_BUNDLE_MEMBER')
        for n,s in meta['dex'].items():require(digest(z.read(n))==s,'DEX_HASH')
        for n,d in meta['members'].items():require(digest(z.read('payload/'+n))==d['sha256'],'MEMBER_HASH')
    return meta

def load_bytes(raw):
    import json
    return json.loads(raw)

def combine(bundles,catalog,out,version):
    require(not out.exists(),'FRESH_OUTPUT_REQUIRED')
    require(set(catalog['bundles'])==set(OWNED),'EXACT_OWNER_VECTOR_REQUIRED')
    require(type(version) is int and 2103420<version<=2100000000,'APP_ROLLBACK')
    selected={owner:read_bundle(bundles/row['file'],row) for owner,row in catalog['bundles'].items()}
    payload={};members={};dex=[]
    for owner,meta in selected.items():
        for key,row in meta['payload'].items():require(key not in payload,'DUPLICATE_PAYLOAD_IDENTITY');payload[key]=row
        for name,row in meta['members'].items():require(name not in members,'DUPLICATE_APK_MEMBER');members[name]=(owner,row)
        for name in sorted(meta['dex']):dex.append((owner,name))
    order={o:i for i,o in enumerate(('CHOOSER_SHELL','MINIMAL_ANDROID_CONTRACT','INFINITY','COBRA'))}
    dex.sort(key=lambda x:(order[x[0]],x[1]))
    archives={owner:ZipFile(bundles/catalog['bundles'][owner]['file']) for owner in OWNED}
    try:
        out.parent.mkdir(parents=True,exist_ok=True)
        with ZipFile(out,'w',allowZip64=True) as apk:
            for name,(owner,row) in sorted(members.items()):
                raw=archives[owner].read('payload/'+name)
                if name=='AndroidManifest.xml':raw=set_version(raw,version)
                info=record(name);info.compress_type=row['compress_type'];info.external_attr=row['external_attr']
                apk.writestr(info,raw)
            for i,(owner,name) in enumerate(dex,1):
                apk.writestr(record('classes'+(str(i) if i>1 else '')+'.dex'),archives[owner].read(name))
    finally:
        for z in archives.values():z.close()
    return {'payload':payload,'unsigned_apk_sha256':file_sha(out),'versionCode':version,
            'component_versions':{o:selected[o]['version'] for o in OWNED},'signed':False}

if __name__=='__main__':
    p=argparse.ArgumentParser();commands=p.add_subparsers(dest='command',required=True)
    a=commands.add_parser('pack')
    for n in ('baseline','modules','ownership','out'):a.add_argument('--'+n,type=Path,required=True)
    a.add_argument('--source',required=True)
    a=commands.add_parser('combine')
    for n in ('bundles','catalog','out'):a.add_argument('--'+n,type=Path,required=True)
    a.add_argument('--version',type=int,required=True)
    args=vars(p.parse_args());command=args.pop('command')
    if command=='pack':pack(**args)
    else:
        args['catalog']=load(args['catalog']);result=combine(**args);save(args['out'].with_suffix('.json'),result)
