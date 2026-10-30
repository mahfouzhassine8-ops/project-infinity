"""Verify and package Cards/Cobra owner DEX; retain exact431 frozen ZIPs.

No APK signing, app installation, shared/native resources or acceptance lock.
Chooser executable DEX and all UI members stay exact; only genuine component
version metadata changes through the existing owner-aware bundle mechanism.
"""
import argparse
import copy
from pathlib import Path
import re
import shutil
import subprocess
import sys
from zipfile import ZipFile

from build import HERE,REPO,ISO,APP,VERSION,BASE_SOURCE,run,sha,compiler_sources
from projection_patch import methods
from inventory import load,save,file_sha,canonical
from component_bundles import read_bundle,record
from release_gate import require,component_digest
from review_ownership import class_owner
from verify_owner_source import verify as verify_canonical_owner

EXISTING={APP+n+';' for n in ('InfinityLiveActivity','InfinityLiveActivity$CobraPosterChannelCard',
    'InfinityCobraFeatureRuntime','CobraLogoRequests','CobraComponent')}
ROOTS={APP+n for n in ('CobraCardsTiles','CobraCardsLayout','CobraProfileDataReuse','CobraCardsReuse')}


def standalone_method(text):
    # Baksmali resolves synthetic field-accessor comments only when the target
    # class is present. The five-class patch lacks that full-owner context.
    # Normalize only these generated comments for prediction of the delta;
    # actual payloads and selected compiled method bodies remain raw/exact.
    return re.sub(r'^    # (?:getter|setter) for: L[^\s;]+;->[^\s]+\n', '', text, flags=re.M)


def bound_sources():
    files=[HERE/'build.py',HERE/'package_owners.py',HERE/'verify_owner_source.py',ISO/'ownership-reviewed-roots.json',HERE/'cards_patch.py',HERE/'projection_patch.py',
      HERE/'presentation_patch.py',HERE/'CARDS-SOURCE-BUDGET.json',HERE/'PROJECTION-SOURCE-BUDGET.json',
      HERE/'DEX2JAR-LIB-PINS.json',HERE/'BASELINE.json',HERE/'SCOPE.json',
      HERE/'logo-clear/patch.py',HERE/'logo-clear/SOURCE-BUDGET.json',
      HERE/'profile-reads/patch_feature.py',HERE/'profile-reads/SOURCE-BUDGET.json',
      HERE/'profile-reads/runtime/CobraProfileDataReuse.java']
    files+=sorted((HERE/'runtime').glob('*.java'))
    return sorted(set(files+compiler_sources()))


def texts(folder):
    result={}
    for p in folder.rglob('*.smali'):
        raw=p.read_text();name=raw.splitlines()[0].split()[-1]
        require(name not in result,'DUPLICATE_CLASS:'+name);result[name]=raw
    return result


def package(bundles,work,jars,out,source):
    bundles,work,jars,out=(p.resolve() for p in (bundles,work,jars,out))
    require(re.fullmatch('[0-9a-f]{40}',source) is not None,'EXACT_COMMITTED_SOURCE')
    for p in bound_sources():
        require(subprocess.check_output(['git','-C',str(REPO),'show',source+':'+str(p.relative_to(REPO))])==p.read_bytes(),
            'COMPILED_SOURCE_CHANGED:'+p.name)
    require(not out.exists(),'FRESH_OUTPUT');out.mkdir(parents=True)
    baseline=load(HERE/'BASELINE.json');catalog=load(bundles/'catalog.json')
    built=load(work/'BUILD.json');require(built['baseline_signed_source']==BASE_SOURCE,'BASELINE_SOURCE')
    require(built['compiler_source_files']=={str(p.relative_to(REPO)):file_sha(p) for p in compiler_sources()},'EXACT_COMPILER_SOURCE_BINDING')
    require(all(file_sha(REPO/n)==pin for n,pin in built['helper_sources'].items()),'EXACT_COMPILED_HELPER_SOURCES')
    require(built['baseline_components']==catalog,'EXACT_COMPILED_CATALOG')
    require(set(built['changed_classes'])==EXISTING,'BOUNDED_CHANGED_EXISTING_CLASSES')
    metas={owner:read_bundle(bundles/row['file'],row) for owner,row in catalog['bundles'].items()}
    for owner,row in catalog['bundles'].items():
        require(file_sha(bundles/row['file'])==baseline['component_sha256'][row['file']],'EXACT431_BUNDLE:'+owner)
    # Recompute the independent policy from the actual owner DEX here. A prior
    # mutable receipt or changed.dex is not an authorization for method changes.
    proof=verify_canonical_owner(work,bundles,jars,'package-canonical','PACKAGE-CANONICAL-RESULT.json')
    require(proof['build_receipt_sha256']==file_sha(work/'BUILD.json'),'CANONICAL_BUILD_BINDING')
    require(proof['compiler_source_files']==built['compiler_source_files'],'CANONICAL_COMPILER_SOURCE_BINDING')
    require(proof['new_DEX_sha256']=={p.name:file_sha(p) for p in (work/'owner-dex/COBRA').glob('*.dex')},'CANONICAL_ACTUAL_DEX_BINDING')
    original=texts(work/'baseline/COBRA');actual={}
    verified=work/'verified/COBRA';require(not verified.exists(),'FRESH_CLASS_VERIFICATION')
    for p in sorted((work/'owner-dex/COBRA').glob('*.dex')):
        dest=verified/p.stem
        run(['java','-cp',jars/'*','org.jf.baksmali.Main','disassemble','--sequential-labels',p,'-o',dest])
        for name,raw in texts(dest).items():
            require(name not in actual,'DUPLICATE_OWNER_CLASS');actual[name]=raw
    require(set(original)<=set(actual),'NO_CLASS_REMOVAL')
    changed={n for n in original if original[n]!=actual[n]};added=set(actual)-set(original)
    require(changed==EXISTING,'EXACT_CHANGED_CLASSES')
    require(bool(added) and all(n.split('$')[0].rstrip(';') in ROOTS for n in added),'BOUNDED_NEW_HELPERS')
    policy=load(ISO/'ownership-reviewed-roots.json')
    for name,raw in actual.items():require(class_owner(name,raw,policy)=='COBRA','EXACT_COBRA_OWNERSHIP:'+name)
    canonical_delta=work/'expected-canonical'
    require(not canonical_delta.exists(),'FRESH_DELTA_CANONICALIZATION')
    run(['java','-cp',jars/'*','org.jf.baksmali.Main','disassemble','--sequential-labels',work/'changed.dex','-o',canonical_delta])
    expected=texts(canonical_delta);require(set(expected)==EXISTING,'EXACT_PATCH_CLASS_SET')
    changes={}
    strip=lambda s:re.sub(r'^\.method [^\n]+\n.*?^\.end method','',s,flags=re.M|re.S)
    for name in EXISTING:
        old,new,compiled=methods(original[name]),methods(actual[name]),methods(expected[name])
        require(set(new)==set(compiled),'EXACT_COMPILED_METHOD_SET:'+name)
        added_methods=set(new)-set(old)
        require(added_methods==({'public static clear(Landroid/app/Activity;Landroid/widget/ImageView;)V'} if name==APP+'CobraLogoRequests;' else set()),'NO_UNREVIEWED_METHOD_ADDITION:'+name)
        require(set(old)<=set(new),'NO_METHOD_REMOVAL:'+name)
        changed_methods={m for m in old if old[m]!=new[m]}
        intended={m for m in old if standalone_method(old[m])!=standalone_method(compiled[m])}
        require(changed_methods==intended,'EXACT_CHANGED_METHOD_SET:'+name)
        require(changed_methods|added_methods==set(proof['changed_methods'][name]),'INDEPENDENT_REVIEWED_METHOD_POLICY:'+name)
        for m in changed_methods|added_methods:require(new[m]==compiled[m],'EXACT_COMPILED_METHOD:'+name+m)
        old_meta,new_meta=strip(original[name]),strip(actual[name])
        if added_methods:
            require([line for line in old_meta.splitlines() if line.strip()]==[line for line in new_meta.splitlines() if line.strip()],
                'FROZEN_CLASS_FIELDS_METADATA:'+name)
        else:require(old_meta==new_meta,'FROZEN_CLASS_FIELDS_METADATA:'+name)
        changes[name]=sorted(changed_methods|added_methods)
    helper_expected=texts(work/'helper-smali')
    require(set(helper_expected)==added,'EXACT_HELPER_SET')
    for name in added:require(actual[name]==helper_expected[name],'EXACT_COMPILED_HELPER:'+name)
    result=copy.deepcopy(catalog);result['source']=source
    metadata=b'infinity.last_updated_in=2103427\ncobra.last_updated_in=2103432\n'
    for owner,row in catalog['bundles'].items():
        dest=out/row['file']
        if owner in ('INFINITY','MINIMAL_ANDROID_CONTRACT'):
            shutil.copyfile(bundles/row['file'],dest);require(file_sha(dest)==row['sha256'],'FROZEN_ZIP:'+owner);continue
        old=metas[owner];meta=copy.deepcopy(old)
        meta.update(approved_source=source,version=VERSION if owner=='COBRA' else '2103432.version-metadata.1')
        if owner=='COBRA':
            meta['payload']={k:v for k,v in old['payload'].items() if not k.startswith('class:')}
            meta['payload'].update({'class:'+n:{'owner':'COBRA','sha256':sha(raw.encode())} for n,raw in actual.items()});meta['dex']={}
        with ZipFile(bundles/row['file']) as before,ZipFile(dest,'w') as target:
            if owner=='COBRA':
                for p in sorted((work/'owner-dex/COBRA').glob('*.dex')):
                    name='dex/'+p.name;target.writestr(record(name),p.read_bytes());meta['dex'][name]=file_sha(p)
            else:
                for name in meta['dex']:target.writestr(record(name),before.read(name))
            for name in meta['members']:
                raw=before.read('payload/'+name)
                if name=='assets/experience-component-updates.properties':
                    require(owner=='CHOOSER_SHELL','METADATA_OWNER')
                    require(raw==b'infinity.last_updated_in=2103427\ncobra.last_updated_in=2103431\n','EXACT_PREVIOUS_LABELS')
                    raw=metadata;meta['members'][name]['sha256']=sha(raw);meta['payload']['member:'+name]['sha256']=sha(raw)
                target.writestr(record('payload/'+name),raw)
            meta['digest']=component_digest(meta['payload'],owner);target.writestr(record('component.json'),canonical(meta))
        result['bundles'][owner]={'file':row['file'],'sha256':file_sha(dest),**{k:meta[k] for k in ('version','digest','approved_source','settings_schema')}}
        verified_meta=read_bundle(dest,result['bundles'][owner])
        if owner=='CHOOSER_SHELL':
            require(verified_meta['dex']==old['dex'],'CHOOSER_EXECUTABLE_DEX_FROZEN')
            delta={k for k in old['payload'] if old['payload'][k]!=verified_meta['payload'][k]}
            require(delta=={'member:assets/experience-component-updates.properties'},'CHOOSER_VERSION_METADATA_ONLY')
            require(set(old['payload'])==set(verified_meta['payload']),'CHOOSER_EXACT_PAYLOAD_SET')
    save(out/'catalog.json',result)
    save(out.parent/'CORRECTIVE-PRESERVATION.json',dict(status='VERIFIED_CARDS_COBRA_ONLY_DELTA_AND_GENUINE_VERSION_METADATA',source=source,
      baseline_signed_source=BASE_SOURCE,changed_classes=sorted(changed),added_classes=sorted(added),method_changes=changes,
      unchanged_Cobra_class_count=len(original)-len(changed),unchanged_Cobra_class_bodies='EXACT',
      original_Activity_fields='EXACT',Pro_player_preview_controls='EXACT431_ORIGINAL_METHODS',
      independent_policy_receipt_sha256=file_sha(work/'PACKAGE-CANONICAL-RESULT.json'),
      Infinity='EXACT431_ZIP',minimal_Android_native_icons='EXACT431_ZIP',chooser='EXACT_DEX_AND_UI_MEMBERS; genuineversionmetadataonly',
      shutdown='FROZEN_NOT_RUN',physical_Fold='PENDING',accepted_pointer_updated=False,component_catalog=result))


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    for name in ('bundles','work','jars','out'):parser.add_argument('--'+name,type=Path,required=True)
    parser.add_argument('--source',required=True);package(**vars(parser.parse_args()))
