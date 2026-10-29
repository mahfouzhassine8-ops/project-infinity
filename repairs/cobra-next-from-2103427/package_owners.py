"""Exact signed2103427 owner delta: no APK signing or application execution."""
import argparse,copy,json,re,shutil,subprocess,sys
from pathlib import Path
from zipfile import ZipFile
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE))
from build import ISO,VERSION,ACTIVITY,APP,methods,patch_activity,run,sha
from inventory import load,save,file_sha,canonical
from component_bundles import read_bundle,record
from release_gate import component_digest,require
from review_ownership import class_owner

def package(bundles,work,jars,out,source):
    bundles,work,jars,out=(p.resolve() for p in (bundles,work,jars,out))
    require(re.fullmatch('[0-9a-f]{40}',source)!=None,'EXACT_SOURCE')
    for path in [HERE/'build.py',HERE/'SOURCE-BUDGET.json',*sorted((HERE/'runtime').glob('*.java'))]:
        require(subprocess.check_output(['git','show',source+':'+str(path.relative_to(HERE.parents[1]))])==path.read_bytes(),'EXACT_COMMITTED_SOURCE:'+path.name)
    require(not out.exists(),'FRESH_OUTPUT');out.mkdir(parents=True)
    scope=load(HERE/'SCOPE.json')
    previous=json.loads(subprocess.check_output(['git','show',scope['baseline_source']+':repairs/dual-experience-isolation-2103420/release-authority.json']))
    catalog=load(bundles/'catalog.json');require(catalog==previous['bundle_catalog'],'EXACT_BASELINE_CATALOG')
    policy=load(ISO/'ownership-reviewed-roots.json')
    originals={};revised={};changed=set();new=set();metas={};texts={}
    for owner in ('COBRA','CHOOSER_SHELL'):
        old=read_bundle(bundles/catalog['bundles'][owner]['file'],catalog['bundles'][owner]);metas[owner]=old
        originals.update({k:v for k,v in old['payload'].items() if k.startswith('class:')})
        for p in sorted((work/'owner-dex'/owner).glob('*.dex')):
            dest=work/'verified'/owner/p.stem
            require(not dest.exists(),'FRESH_DISASSEMBLY')
            run(['java','-cp',str(jars/'*'),'org.jf.baksmali.Main','disassemble','--sequential-labels',p,'-o',dest])
            for smali in dest.rglob('*.smali'):
                text=smali.read_text();name=text.splitlines()[0].split()[-1];key='class:'+name
                require(key not in revised,'DUPLICATE_CLASS')
                require(class_owner(name,text,policy)==owner,'OWNERSHIP:'+name)
                revised[key]={'owner':owner,'sha256':sha(text.encode())};texts[name]=text
                if key not in originals:new.add(key)
                elif revised[key]!=originals[key]:changed.add(key)
    require(set(originals)<=set(revised),'REMOVED_CLASS')
    expected={APP+n+';' for n in ('InfinityLiveActivity','CobraComponent','ChooserReleaseMetadata')}
    require(changed=={'class:'+n for n in expected},'EXACT_CHANGED_CLASSES')
    roots={APP+x for x in ('CobraArrange','CobraPresentation','CobraLayoutCatalog','CobraLogoRequests')}
    require(bool(new) and all(k[6:].split('$')[0].rstrip(';') in roots for k in new),'NARROW_NEW_CLASSES')
    baseline_texts={}
    for p in (work/'baseline').rglob('*.smali'):
        t=p.read_text();n=t.splitlines()[0].split()[-1]
        if n in expected:baseline_texts[n]=t
    patched,selected=patch_activity(baseline_texts[ACTIVITY])
    # The assembler canonicalizes labels/whitespace. Compare the writer output
    # with a fresh disassembly of the exact assembled, source-pinned delta.
    canonical_delta=work/'expected-canonical'
    run(['java','-cp',str(jars/'*'),'org.jf.baksmali.Main','disassemble','--sequential-labels',work/'changed.dex','-o',canonical_delta])
    for name in expected:
        canonical_text=(canonical_delta/(name[1:-1]+'.smali')).read_text()
        if name==ACTIVITY:
            # Only assembled selected methods are replaced by the DEX writer;
            # all other methods come directly from the old immutable class.
            expected_methods=methods(canonical_text);actual_methods=methods(texts[name])
            for signature in selected:require(actual_methods[signature]==expected_methods[signature],'EXACT_COMPILED_METHOD:'+signature)
            require([s for s in texts[name].splitlines() if s.startswith('.field ')]==
                    [s for s in baseline_texts[name].splitlines() if s.startswith('.field ')],'FROZEN_ACTIVITY_FIELDS')
        else:require(texts[name]==canonical_text,'EXACT_COMPILED_DELTA:'+name)
    old_methods=methods(baseline_texts[ACTIVITY]);new_methods=methods(texts[ACTIVITY])
    require(set(old_methods)==set(new_methods),'EXACT_ACTIVITY_METHOD_SET')
    require({m for m in old_methods if old_methods[m]!=new_methods[m]}==set(selected),'UNCHANGED_ACTIVITY_METHODS')
    result=copy.deepcopy(catalog);result['source']=source
    metadata=b'infinity.last_updated_in=2103427\ncobra.last_updated_in=2103428\n'
    for owner,row in catalog['bundles'].items():
        dest=out/row['file']
        if owner not in metas:
            require(file_sha(bundles/row['file'])==scope['frozen_owner_zips'][owner],'FROZEN_ZIP')
            shutil.copyfile(bundles/row['file'],dest);continue
        old=metas[owner];meta=copy.deepcopy(old)
        meta.update(version=VERSION if owner=='COBRA' else '2103428.version-wording.1',approved_source=source)
        meta['payload']={k:v for k,v in old['payload'].items() if not k.startswith('class:')}
        meta['payload'].update({k:v for k,v in revised.items() if v['owner']==owner});meta['dex']={}
        with ZipFile(bundles/row['file']) as original,ZipFile(dest,'w') as target:
            for p in sorted((work/'owner-dex'/owner).glob('*.dex')):
                name='dex/'+p.name;target.writestr(record(name),p.read_bytes());meta['dex'][name]=file_sha(p)
            for name in meta['members']:
                raw=metadata if name=='assets/experience-component-updates.properties' else original.read('payload/'+name)
                if name=='assets/experience-component-updates.properties':
                    meta['members'][name]['sha256']=sha(raw);meta['payload']['member:'+name]['sha256']=sha(raw)
                target.writestr(record('payload/'+name),raw)
            meta['digest']=component_digest(meta['payload'],owner);target.writestr(record('component.json'),canonical(meta))
        result['bundles'][owner]={'file':row['file'],'sha256':file_sha(dest),**{k:meta[k] for k in ('version','digest','approved_source','settings_schema')}}
        read_bundle(dest,result['bundles'][owner])
    save(out/'catalog.json',result)
    report=dict(status='EXACT_COBRA_DELTA_AND_VERSION_WORDING_VERIFIED',source=source,baseline=scope['baseline_source'],
        existing_classes_checked=len(originals),unchanged_existing_classes=len(originals)-len(changed),changed_existing_classes=sorted(changed),
        added_classes=sorted(new),selected_activity_methods=selected,unchanged_activity_methods=len(methods(baseline_texts[ACTIVITY]))-len(selected),
        new_activity_fields=0,Infinity='EXACT_ZIP',minimal_Android='EXACT_ZIP',Pro_Six_reflow_player_services='EXACT_UNCHANGED_CLASS_OR_METHOD_BYTES',
        shutdown='FROZEN_NOT_RUN',physical_Fold='PENDING',user_device_operations=False,component_catalog=result)
    save(out.parent/'CORRECTIVE-PRESERVATION.json',report)
    print(report['status'])
if __name__=='__main__':
    p=argparse.ArgumentParser()
    for n in ('bundles','work','jars','out'):p.add_argument('--'+n,type=Path,required=True)
    p.add_argument('--source',required=True);package(**vars(p.parse_args()))
