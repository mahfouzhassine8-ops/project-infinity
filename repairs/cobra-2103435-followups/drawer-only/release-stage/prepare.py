"""Prepare exact435 owner bundles plus a complete unsigned APK comparison.

The existing immutable bundle reader, ModuleDexWriter and sole APK combiner
are reused. No signer, version reservation, registry or acceptance mutation.
RAM output is used when disk space cannot hold the uncompressed review APK.
"""
import argparse
import contextlib
import copy
import hashlib
import io
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
from zipfile import ZipFile

HERE=Path(__file__).resolve().parent
TASK=HERE.parent
REPO=TASK.parents[2]
ISO=REPO/'repairs/dual-experience-isolation-2103420'
CARDS=REPO/'repairs/cobra-next-from-2103427/cards-from-2103431'
sys.path[:0]=[str(ISO),str(CARDS)]
from inventory import canonical,digest,file_sha,save,load,validate_names,CERT_SHA,SIGNATURE
from component_bundles import read_bundle,record,combine
from release_gate import component_digest,normalize_manifest
from projection_patch import methods

BASE='e0c6153588992001d84076d33fdf8f0d676c0d00'
CORRECTION='70c0e3e0ad6cf3100cce6bc599be4e79d424e803'
APK_SHA='dc83faed4a8eb1d2e2e116914cf15f2f1c27cc2a8653813fd6701ba300234442'
BUNDLE_SHA='e67dd28dab95206dcda8cb88903828453da57670468c532a32cd1db077663893'
VERSION=2103436
LABEL='assets/experience-component-updates.properties'
COMPONENT='Lcom/projectinfinity/kodi/CobraComponent;'

class MemoryAPK(os.PathLike):
    """Fresh anonymous RAM file for the UNMODIFIED established APK combiner.

    Only this constructor creates the descriptor; it cannot wrap an existing
    file or baseline. Freshness requires zero bytes in that newly allocated
    descriptor. Path conversion lets the original file SHA256 implementation
    read the actual serialized bytes with no hash/assembler monkeypatch.
    """
    def __init__(self):self.fd=os.memfd_create('unsigned-drawer-review',0)
    def __fspath__(self):return '/proc/self/fd/'+str(self.fd)
    @property
    def parent(self):return self
    def mkdir(self,**kwargs):assert os.fstat(self.fd).st_size==0
    def exists(self):return os.fstat(self.fd).st_size!=0
    def close(self):os.close(self.fd)

def run(*args):subprocess.run(list(map(str,args)),check=True)
def raw_classes(root):
    found={}
    for p in root.rglob('*.smali'):
        raw=p.read_text();name=raw.splitlines()[0].split()[-1];assert name not in found;found[name]=raw
    return found
def committed(source,path):
    assert subprocess.check_output(['git','-C',str(REPO),'show',source+':'+str(path.relative_to(REPO))])==path.read_bytes(),path
def freeze_copy(a,b):
    try:os.link(a,b)
    except OSError:shutil.copyfile(a,b)
    assert file_sha(a)==file_sha(b)

def version_owner(owner,jars,originals,out):
    built=load(owner/'BUILD.json');assert built['status']=='PASS_EXACT435_DRAWER_DELTA_OWNER_ONLY'
    for p,pin in built['compiler_sources'].items():assert file_sha(REPO/p)==pin,p
    for n,pin in built['output_DEX'].items():assert file_sha(owner/'owner-dex/COBRA'/n)==pin,n
    # Reviewed methods/helpers remain exact. Only the version getter changes.
    before=originals[COMPONENT];assert before.count('"2103435.cobra.1"')==1
    revised=before.replace('"2103435.cobra.1"','"2103436.cobra.1"',1)
    a,b=methods(before),methods(revised)
    assert [k for k in a if a[k]!=b[k]]==['public static version()Ljava/lang/String;']
    changed=out/'version-only/com/projectinfinity/kodi/CobraComponent.smali';changed.parent.mkdir(parents=True);changed.write_text(revised)
    run('java','-cp',jars/'*','org.jf.smali.Main','assemble',out/'version-only','-o',out/'version.dex')
    empty=out/'empty';empty.mkdir();run('java','-cp',jars/'*','org.jf.smali.Main','assemble',empty,'-o',out/'empty.dex')
    (out/'assignments.tsv').write_text(''.join(n+'\tCOBRA\n' for n in sorted(originals)))
    (out/'origins.tsv').write_text(COMPONENT+'\t'+COMPONENT+'\n')
    classes=out/'writer';classes.mkdir();cp=':'.join(str(p) for p in sorted(jars.glob('*.jar')))
    run('java','-m','jdk.compiler/com.sun.tools.javac.Main','-source','8','-target','8','-g:none','-Xlint:-options','-cp',cp,'-d',classes,ISO/'ModuleDexWriter.java')
    inputs=sorted((owner/'owner-dex/COBRA').glob('*.dex'))
    run('java','-cp',str(classes)+':'+cp,'org.jf.dexlib2.writer.pool.ModuleDexWriter',out/'owner-dex',out/'assignments.tsv',out/'origins.tsv',out/'version.dex',out/'empty.dex',*inputs)
    actual={}
    for dex in sorted((out/'owner-dex/COBRA').glob('*.dex')):
        target=out/('canonical-'+dex.stem)
        run('java','-cp',jars/'*','org.jf.baksmali.Main','disassemble','--sequential-labels',dex,'-o',target)
        new=raw_classes(target);assert not new.keys()&actual.keys();actual.update(new)
    assert actual.keys()==originals.keys()
    assert [n for n in actual if actual[n]!=originals[n]]==[COMPONENT]
    assert actual[COMPONENT]==revised
    assert file_sha(out/'owner-dex/COBRA/part-1.dex')==built['output_DEX']['part-1.dex']
    return actual,built

def package(baseline,owner,jars,canonical_archive,out,source):
    assert not out.exists();out.mkdir(parents=True)
    assert {p.name:file_sha(p) for p in jars.glob('*.jar')}==load(REPO/'repairs/universal-persistence-2103401/RECEIPT-TOOL-PINS.json')
    scope=load(HERE/'SCOPE.json');assert scope['selected_before_execution'] and scope['prospective_versionCode']==VERSION
    for p in [HERE/'prepare.py',HERE/'SCOPE.json',TASK/'runtime/CobraCardsDrawerViewport.java',TASK/'patch.py',TASK/'compile_owner.py',CARDS/'runtime/CobraCardsLayout.java']:committed(source,p)
    assert subprocess.run(['git','-C',str(REPO),'merge-base','--is-ancestor',CORRECTION,source]).returncode==0
    authority=load(ISO/'release-authority.json');assert authority['candidate_versionCode']==2103435 and authority['generation']==20
    assert subprocess.check_output(['git','-C',str(REPO),'ls-remote','origin','refs/heads/lock/infinity-cobra-2103435-user-approved-20261031'],text=True).split()[0]==BASE
    catalog=load(baseline/'catalog.json');assert catalog==authority['bundle_catalog']
    metas={o:read_bundle(baseline/r['file'],r) for o,r in catalog['bundles'].items()}
    assert file_sha(baseline/'COBRA.zip')==BUNDLE_SHA
    originals={}
    with ZipFile(canonical_archive) as z:
        pins=load(canonical_archive.with_name('VERIFIED-CANONICAL-INVENTORY.json'))
        assert set(z.namelist())==set(pins)
        for n in z.namelist():
            raw=z.read(n);assert digest(raw)==pins[n];text=raw.decode();name=text.splitlines()[0].split()[-1];assert name not in originals;originals[name]=text
    assert digest(originals[COMPONENT].encode())==metas['COBRA']['payload']['class:'+COMPONENT]['sha256'],'Exact original435 version-component preimage required'
    test=load(TASK/'correction-host/OUTCOME.json')
    assert len(test['selected_cases'])==5 and all(row['status']=='PASS' for row in test['selected_cases'])
    for name,pin in test['inventory'].items():assert file_sha(TASK/'correction-host'/name)==pin
    actual,built=version_owner(owner,jars,originals,out)
    dest=out/'components';dest.mkdir();result=copy.deepcopy(catalog);result['source']=source
    for o,r in catalog['bundles'].items():
        p=dest/r['file']
        if o in ['INFINITY','MINIMAL_ANDROID_CONTRACT']:freeze_copy(baseline/r['file'],p);continue
        meta=copy.deepcopy(metas[o]);meta.update(approved_source=source,version='2103436.cobra.1' if o=='COBRA' else '2103436.version-metadata.1')
        if o=='COBRA':
            meta['payload']={k:v for k,v in meta['payload'].items() if not k.startswith('class:')}
            meta['payload'].update({'class:'+n:{'owner':o,'sha256':digest(raw.encode())} for n,raw in actual.items()})
            meta['dex']={}
        with ZipFile(baseline/r['file']) as old,ZipFile(p,'w') as z:
            if o=='COBRA':
                for dex in sorted((out/'owner-dex/COBRA').glob('*.dex')):
                    n='dex/'+dex.name;z.writestr(record(n),dex.read_bytes());meta['dex'][n]=file_sha(dex)
            else:
                for n in meta['dex']:z.writestr(record(n),old.read(n))
            for n in meta['members']:
                raw=old.read('payload/'+n)
                if n==LABEL:
                    assert o=='CHOOSER_SHELL' and raw==b'infinity.last_updated_in=2103435\ncobra.last_updated_in=2103435\n'
                    raw=b'infinity.last_updated_in=2103435\ncobra.last_updated_in=2103436\n'
                    meta['members'][n]['sha256']=digest(raw);meta['payload']['member:'+n]['sha256']=digest(raw)
                z.writestr(record('payload/'+n),raw)
            meta['digest']=component_digest(meta['payload'],o);z.writestr(record('component.json'),canonical(meta))
        row={'file':r['file'],'sha256':file_sha(p),**{k:meta[k] for k in ['version','digest','approved_source','settings_schema']}}
        read_bundle(p,row);result['bundles'][o]=row
    for o in ['INFINITY','MINIMAL_ANDROID_CONTRACT']:assert result['bundles'][o]==catalog['bundles'][o]
    old=metas['CHOOSER_SHELL'];new=read_bundle(dest/'CHOOSER_SHELL.zip',result['bundles']['CHOOSER_SHELL']);assert old['dex']==new['dex']
    assert old['payload'].keys()==new['payload'].keys() and [n for n in old['payload'] if old['payload'][n]!=new['payload'][n]]==['member:'+LABEL]
    save(dest/'catalog.json',result)
    next_cobra=read_bundle(dest/'COBRA.zip',result['bundles']['COBRA'])
    changed={n for n in metas['COBRA']['payload'] if metas['COBRA']['payload'][n]!=next_cobra['payload'].get(n)}
    expected={'class:'+n for n in built['changed_methods']}|{'class:'+COMPONENT};assert changed==expected
    assert set(metas['COBRA']['payload'])<=set(next_cobra['payload'])
    assert set(next_cobra['payload'])-set(metas['COBRA']['payload'])=={'class:'+n for n in built['new_classes']}
    receipt=dict(status='PASS_PROSPECTIVE436_PREPARED_COMPONENTS_NOT_RESERVED_OR_SIGNED',source=source,verified_functional_source=CORRECTION,baseline_source=BASE,versionCode=VERSION,component_catalog=result,owner_build_sha256=file_sha(owner/'BUILD.json'),functional_method_changes=built['changed_methods'],new_classes=built['new_classes'],metadata_only_method='CobraComponent.version:2103435.cobra.1->2103436.cobra.1',unchanged_existing_Cobra_classes=7163,part1_byte_identical=True,files={str(p.relative_to(out)):file_sha(p) for p in (out/'owner-dex/COBRA').glob('*.dex')},release_authority_mutated=False,signature='NOT_INVOKED',shutdown='NOT_CHANGED_NOT_RUN',accepted_pointer_updated=False)
    save(out/'PREPARATION.json',receipt)
    return receipt

def compare(prepared,signed435,sdk,out,apk_out=None):
    receipt=load(prepared/'PREPARATION.json');components=prepared/'components';catalog=load(components/'catalog.json');assert catalog==receipt['component_catalog']
    assert not out.exists();out.mkdir(parents=True)
    # Original signed bytes are streamed to a RAM fd to preserve the protected
    # baseline and avoid needing an extra780MB of workspace disk.
    fd=os.memfd_create('protected-signed435',0)
    try:
        with ZipFile(signed435) as z:
            names=validate_names(z);name='Infinity-2103435-Combined-Original-Signer.apk';assert name in names
            with z.open(name) as stream:
                h=hashlib.sha256()
                while raw:=stream.read(4*1024*1024):
                    remaining=memoryview(raw)
                    while remaining:remaining=remaining[os.write(fd,remaining):]
                    h.update(raw)
            assert h.hexdigest()==APK_SHA
        signature=subprocess.check_output(['java','-jar',str(sdk/'lib/apksigner.jar'),'verify','--verbose','--print-certs','/proc/self/fd/'+str(fd)],pass_fds=(fd,),text=True)
        assert re.findall(r'Signer #[0-9]+ certificate SHA-256 digest: ([0-9a-f]+)',signature)==[CERT_SHA]
        for scheme in ['v1','v2','v3']:assert re.search('Verified using '+scheme+r' scheme.*: true',signature)
        (out/'ORIGINAL435-SIGNATURE.txt').write_text(signature)
        apk=apk_out if apk_out else MemoryAPK();assembled=combine(components,catalog,apk,VERSION)
        metas={o:read_bundle(components/r['file'],r) for o,r in catalog['bundles'].items()}
        dex={};i=0
        for o in ['CHOOSER_SHELL','MINIMAL_ANDROID_CONTRACT','INFINITY','COBRA']:
            for n,pin in sorted(metas[o]['dex'].items()):i+=1;dex['classes'+(str(i) if i>1 else '')+'.dex']=(o,pin)
        assert i==5
        os.lseek(fd,0,os.SEEK_SET)
        with os.fdopen(os.dup(fd),'rb') as baseline_stream,ZipFile(baseline_stream) as old,ZipFile(apk) as new:
            old_names=set(validate_names(old))-SIGNATURE;new_names=set(validate_names(new));assert old_names==new_names
            inventory={};changed=[];native=[]
            for n in sorted(new_names):
                with old.open(n) as a,new.open(n) as b:before=hashlib.file_digest(a,'sha256').hexdigest();after=hashlib.file_digest(b,'sha256').hexdigest()
                inventory[n]={'signed435':before,'unsigned_candidate':after}
                if before!=after:changed.append(n)
                if n.endswith('.so'):assert before==after;native.append(n)
            assert set(changed)=={'AndroidManifest.xml',LABEL,'classes4.dex'},changed
            a,av=normalize_manifest(old.read('AndroidManifest.xml'));b,bv=normalize_manifest(new.read('AndroidManifest.xml'));assert a==b and av==2103435 and bv==VERSION
            for n,(o,pin) in dex.items():assert inventory[n]['unsigned_candidate']==pin
            for o,meta in metas.items():
                with ZipFile(components/catalog['bundles'][o]['file']) as z:
                    for n in meta['members']:
                        a,b=z.read('payload/'+n),new.read(n)
                        if n=='AndroidManifest.xml':a,b=normalize_manifest(a)[0],normalize_manifest(b)[0]
                        assert a==b,(o,n)
            assert new.read(LABEL)==b'infinity.last_updated_in=2103435\ncobra.last_updated_in=2103436\n'
            assert len(native)==47
            save(out/'ALL-APK-MEMBERS.json',inventory)
            result=dict(status='PASS_ACTUAL_UNSIGNED436_VS_ORIGINAL_SIGNED435_FULL_MEMBER_COMPARISON',source=receipt['source'],baseline_signed_APK_sha256=APK_SHA,baseline_original_certificate_sha256=CERT_SHA,baseline_signature_schemes=['v1','v2','v3'],prospective_versionCode=VERSION,unsigned_apk_sha256=assembled['unsigned_apk_sha256'],actual_serialized_APK_location=str(apk_out) if apk_out else 'RAM_ONLY; not persisted or installable without original signing',changed_unsigned_members=changed,unchanged_members=len(new_names)-len(changed),unchanged_native_libraries=len(native),component_zip_sha256={o:r['sha256'] for o,r in catalog['bundles'].items()},all_members_inventory_sha256=file_sha(out/'ALL-APK-MEMBERS.json'),Infinity='EXACT435_ZIP_DEX_AND_EVERY_MEMBER',Minimal_Android='EXACT435_ZIP_DEX_AND_EVERY_MEMBER',chooser='EXACT435_DEX_UI; truthful Cobra version metadata only',shutdown='NOT_CHANGED_NOT_RUN',signed_successor_APK_comparison='PENDING; no successor signed APK exists',Android_runtime='NOT_RUN',media_review='NOT_ACCESSED',registry_updated=False,accepted_pointer_updated=False)
            save(out/'APK-PRESERVATION.json',result)
            print(json.dumps({k:result[k] for k in ['status','changed_unsigned_members','unchanged_members','unchanged_native_libraries','signed_successor_APK_comparison']},indent=2))
    finally:
        os.close(fd)
        if 'apk' in locals() and isinstance(apk,MemoryAPK):apk.close()

if __name__=='__main__':
    p=argparse.ArgumentParser();sub=p.add_subparsers(dest='phase',required=True)
    a=sub.add_parser('package')
    for n in ['baseline','owner','jars','canonical-archive','out']:a.add_argument('--'+n,type=Path,required=True)
    a.add_argument('--source',required=True)
    a=sub.add_parser('compare')
    for n in ['prepared','signed435','sdk','out']:a.add_argument('--'+n,type=Path,required=True)
    a.add_argument('--apk-out',type=Path)
    args=vars(p.parse_args());phase=args.pop('phase');(package if phase=='package' else compare)(**args)
