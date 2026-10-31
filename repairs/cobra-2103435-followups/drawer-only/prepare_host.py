"""Bind selected native-view host tests to the exact compiled435 owner delta."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys
from zipfile import ZipFile,ZIP_DEFLATED
import patch
sys.path.insert(0,str(patch.CARDS))
import ci_host

HERE=Path(__file__).resolve().parent
def sha(p):
    with p.open('rb') as s:return hashlib.file_digest(s,'sha256').hexdigest()
def load(p):return json.loads(p.read_text())
def save(p,x):p.write_text(json.dumps(x,indent=2)+'\n')

def prepare(trusted,owner,dex2jar,out,baseline=False):
    assert not out.exists()
    binding=load(trusted/'SOURCE-BINDINGS.json')
    assert sha(trusted/'production.jar')==binding['production_jar_sha256']
    assert sha(trusted/'support.jar')==binding['support_jar_sha256']
    assert sha(trusted/'production.jar')=='38011f664cbd85aeb9743a152687a5e53a6256ec474cef09957579b0d9f518ea','Exact previously source/canonical-bound435 host required'
    assert sha(trusted/'support.jar')=='016a9ca405468cbc86fb6da8634e943ada67ffa615a3b804a1d9680fca84f1ad'
    assert {p.name:sha(p) for p in (dex2jar/'lib').glob('*.jar')}==load(patch.CARDS/'DEX2JAR-LIB-PINS.json')
    scope=load(HERE/'SCOPE.json');assert scope['selected_before_execution']
    tests=[patch.CARDS/'layout-qa/CobraCardsLayoutTest.java',HERE/'CobraDrawerCorrectionTest.java']
    ci_host.prepare_plain(trusted,out,tests)
    expected=['coverAndOtherModesMatchSigned435'] if baseline else scope['selected_host_methods']
    ci_host.set_properties(out,{'drawer.output':str(out/'measurements'),'cards.layout.output':str(out/'measurements'),'drawer.baseline':str(out.parent/'drawer435-negative-baseline/measurements'),'drawer.candidate':str(not baseline).lower()})
    production={}
    with ZipFile(trusted/'production.jar') as z:
        for n in z.namelist():production[n]=z.read(n)
    overlay={}
    if not baseline:
        build=load(owner/'BUILD.json');assert build['status']=='PASS_EXACT435_DRAWER_DELTA_OWNER_ONLY'
        for name,pin in build['output_DEX'].items():assert sha(owner/'owner-dex/COBRA'/name)==pin
        jar=out/'translated.jar';errors=out/'translation-errors.zip'
        subprocess.run(['java','-cp',str(dex2jar/'lib/*'),'com.googlecode.dex2jar.tools.Dex2jarCmd',str(owner/'owner-dex/COBRA/part-0.dex'),'-o',str(jar),'-e',str(errors)],check=True)
        assert not errors.exists(),'No substituted or incomplete owner translation allowed'
        with ZipFile(jar) as z:
            for descriptor in [*build['changed_methods'],*build['new_classes']]:
                n=descriptor[1:-1]+'.class';overlay[n]=z.read(n)
        assert len(overlay)==4
        with ZipFile(out/'production.jar','w',ZIP_DEFLATED) as z:
            for n,raw in production.items():z.writestr(n,overlay.get(n,raw))
            for n in sorted(overlay.keys()-production.keys()):z.writestr(n,overlay[n])
        with ZipFile(out/'production.jar') as z:
            changed={n for n in production if production[n]!=z.read(n)}
            assert changed|set(z.namelist())-production.keys()==overlay.keys()
    save(out/'SELECTION.json',dict(recorded_before_execution=True,test_class='CobraDrawerCorrectionTest',methods=expected,maven_selector='CobraDrawerCorrectionTest#'+'+'.join(expected),scope_sha256=sha(HERE/'SCOPE.json'),source_SHA256={str(p):sha(p) for p in tests},baseline_source_bindings_sha256=sha(trusted/'SOURCE-BINDINGS.json'),owner_build_sha256=sha(owner/'BUILD.json') if not baseline else None,production_sha256=sha(out/'production.jar'),support_sha256=sha(out/'support.jar'),changed_host_classes={n:hashlib.sha256(raw).hexdigest() for n,raw in overlay.items()},Infinity='NOT_EXECUTED',shutdown='NOT_EXECUTED',physical_Fold='NOT_RUN'))

if __name__=='__main__':
    p=argparse.ArgumentParser()
    for name in ('trusted','owner','dex2jar','out'):p.add_argument('--'+name,type=Path,required=True)
    p.add_argument('--baseline',action='store_true');prepare(**vars(p.parse_args()))
