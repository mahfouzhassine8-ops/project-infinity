"""CI preparation only: compile exact435 delta, reuse passed host evidence.

No behavioral test, signer credential, installation or acceptance operation.
"""
import argparse
import hashlib
import importlib.util
import os
from pathlib import Path
import shutil
import subprocess
from zipfile import ZipFile,ZIP_DEFLATED
from prepare import *
sys.path.insert(0,str(TASK))

def load_module(name,path):
    spec=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m

def produce(baseline,signed435,jars,android,d8,sdk,out):
    assert not out.exists();out.mkdir(parents=True)
    source=subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip();assert source==os.environ['GITHUB_SHA']
    assert os.environ['GITHUB_REF']=='refs/heads/work/cobra-only-from-2103435-20261031'
    assert subprocess.check_output(['git','status','--porcelain','--untracked-files=no'],text=True)==''
    assert file_sha(baseline/'COBRA.zip')==BUNDLE_SHA
    canonical=out/'signed435-canonical';canonical.mkdir()
    with ZipFile(baseline/'COBRA.zip') as z:
        meta=json.loads(z.read('component.json'))
        for name,pin in sorted(meta['dex'].items()):
            dex=out/Path(name).name;dex.write_bytes(z.read(name));assert file_sha(dex)==pin
            run('java','-cp',jars/'*','org.jf.baksmali.Main','disassemble','--sequential-labels',dex,'-o',canonical/dex.stem)
    compiler=load_module('drawer_compiler',TASK/'compile_owner.py')
    # Compile API contains exact435 classes; the new helper's only app ABI is
    # CobraArrange.ownedField, whose accepted implementation remains untouched.
    # Use the existing pinned dex2jar-independent ABI from the original helper
    # compile: a minimal source declaration is NOT accepted as a replacement.
    api=out/'api.jar'
    # Java compiler accepts DEX only through an actual translation; the pinned
    # original tools below are supplied by the established signed owner job.
    dex2jar=Path(os.environ['DRAWER_DEX2JAR']);api_files=[]
    assert {p.name:file_sha(p) for p in (dex2jar/'lib').glob('*.jar')}==load(CARDS/'DEX2JAR-LIB-PINS.json')
    for i,dex in enumerate(sorted(out.glob('part-*.dex'))):
        jar=out/('api-'+str(i)+'.jar');errors=out/('api-errors-'+str(i)+'.zip')
        run('java','-cp',dex2jar/'lib/*','com.googlecode.dex2jar.tools.Dex2jarCmd',dex,'-o',jar,'-e',errors);assert not errors.exists();api_files.append(jar)
    with ZipFile(api,'w',ZIP_DEFLATED) as target:
        seen=set()
        for jar in api_files:
            with ZipFile(jar) as z:
                for n in z.namelist():
                    if not n.endswith('.class'):continue
                    assert n not in seen;seen.add(n);target.writestr(n,z.read(n))
    owner=out/'owner';compiler.build(baseline/'COBRA.zip',canonical,api,jars,android,d8,owner)
    pinned=load(TASK/'correction-host/OWNER-BUILD.json');built=load(owner/'BUILD.json')
    for key in ['baseline_source','baseline_Cobra_ZIP_sha256','source_sha256','compiler_sources','changed_methods','new_classes','unchanged_classes','output_DEX']:assert built[key]==pinned[key],key
    archive=owner/'VERIFIED-CANONICAL.zip';pins={}
    with ZipFile(archive,'w',ZIP_DEFLATED) as z:
        for folder in [owner/'verify-part-0',owner/'verify-part-1']:
            for p in folder.rglob('*.smali'):
                name=str(p.relative_to(owner));raw=p.read_bytes();pins[name]=digest(raw);z.writestr(name,raw)
    save(owner/'VERIFIED-CANONICAL-INVENTORY.json',pins)
    prepared=out/'prepared';package(baseline,owner,jars,archive,prepared,source)
    compare(prepared,signed435,sdk,out/'comparison',apk_out=out/'combined-unsigned.apk')
    evidence=out/'evidence';evidence.mkdir();mutable=out/'mutable';mutable.mkdir()
    for name in ['COBRA.zip','CHOOSER_SHELL.zip','catalog.json']:shutil.copyfile(prepared/'components'/name,mutable/name)
    for a,b in [(owner/'BUILD.json','OWNER-BUILD.json'),(prepared/'PREPARATION.json','PREPARATION.json'),(out/'comparison/APK-PRESERVATION.json','APK-PRESERVATION.json'),(out/'comparison/ALL-APK-MEMBERS.json','ALL-APK-MEMBERS.json'),(out/'comparison/ORIGINAL435-SIGNATURE.txt','ORIGINAL435-SIGNATURE.txt')]:shutil.copyfile(a,evidence/b)
    files={p.name:file_sha(p) for p in evidence.iterdir()}
    receipt=dict(status='PASS_DRAWER436_EXACT_OWNER_AND_UNSIGNED_APK_PREPARATION',source=source,run_id=int(os.environ['GITHUB_RUN_ID']),baseline_source=BASE,baseline_signing_run=41125367621,baseline_APK_sha256=APK_SHA,component_catalog=load(mutable/'catalog.json'),files=files,source_files={str(p.relative_to(REPO)):file_sha(p) for p in [HERE/'prepare.py',HERE/'produce.py',HERE/'register.py',HERE/'SCOPE.json',TASK/'compile_owner.py',TASK/'patch.py',TASK/'runtime/CobraCardsDrawerViewport.java',CARDS/'runtime/CobraCardsLayout.java']},reused_host_tests=5,host_tests_rerun=False,original_key='NOT_ACCESSED',shutdown='NOT_CHANGED_NOT_RUN',physical_Fold='NOT_RUN',accepted_pointer_updated=False)
    save(evidence/'PRODUCER.json',receipt)

if __name__=='__main__':
    p=argparse.ArgumentParser()
    for n in ['baseline','signed435','jars','android','d8','sdk','out']:p.add_argument('--'+n,type=Path,required=True)
    produce(**vars(p.parse_args()))
