"""Compile only the proven drawer-coordinate delta from exact signed435.

The two existing sizing methods are patched at their coordinate-read calls.
Only the new drawer-coordinate helper classes come from javac/D8 output. All other
definitions remain original signed435 DEX definitions, without optimization.
No release version, APK, signing, provider or application execution occurs.
"""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys
from zipfile import ZipFile,ZIP_DEFLATED
import patch

HERE=Path(__file__).resolve().parent
REPO=HERE.parents[2]
CARDS=patch.CARDS
ISO=REPO/'repairs/dual-experience-isolation-2103420'
sys.path.insert(0,str(ISO))
from compile_runtime import ANDROID_SHA,D8_SHA

def sha(p):
    with p.open('rb') as stream:return hashlib.file_digest(stream,'sha256').hexdigest()
def digest(raw):return hashlib.sha256(raw).hexdigest()
def save(p,x):p.write_text(json.dumps(x,indent=2)+'\n')
def run(*args):subprocess.run([str(a) for a in args],check=True)

def build(bundle,canonical,api,jars,android,d8,out):
    assert not out.exists();out.mkdir(parents=True)
    assert sha(bundle)=='e67dd28dab95206dcda8cb88903828453da57670468c532a32cd1db077663893'
    assert sha(android)==ANDROID_SHA and sha(d8)==D8_SHA
    assert {p.name:sha(p) for p in jars.glob('*.jar')}==json.loads((REPO/'repairs/universal-persistence-2103401/RECEIPT-TOOL-PINS.json').read_text())
    with ZipFile(bundle) as z:
        meta=json.loads(z.read('component.json'));inputs=[]
        for name,pin in sorted(meta['dex'].items()):
            raw=z.read(name);assert digest(raw)==pin
            target=out/Path(name).name;target.write_bytes(raw);inputs.append(target)
    originals={}
    for p in canonical.rglob('*.smali'):
        raw=p.read_text();name=raw.splitlines()[0].split()[-1]
        assert name not in originals
        assert digest(raw.encode())==meta['payload']['class:'+name]['sha256'],name
        originals[name]=raw
    expected={n[6:] for n in meta['payload'] if n.startswith('class:')}
    assert originals.keys()==expected,'Complete actual435 canonical binding required'
    source=HERE/'runtime/CobraCardsDrawerViewport.java';source_pin=sha(source)
    layout_source=CARDS/'runtime/CobraCardsLayout.java'
    compiled=out/'compiled';compiled.mkdir()
    run('java','-m','jdk.compiler/com.sun.tools.javac.Main','-source','8','-target','8','-g:none','-Xlint:-options','-cp',str(android)+':'+str(api),'-d',compiled,source)
    with ZipFile(out/'helpers.jar','w',ZIP_DEFLATED) as z:
        for p in compiled.rglob('*.class'):z.write(p,p.relative_to(compiled).as_posix())
    generated=out/'generated';generated.mkdir()
    run('java','-cp',d8,'com.android.tools.r8.D8','--min-api','21','--lib',android,'--output',generated,out/'helpers.jar')
    assert sha(source)==source_pin
    generated_smali=out/'generated-smali'
    run('java','-cp',str(jars/'*'),'org.jf.baksmali.Main','disassemble','--sequential-labels',generated/'classes.dex','-o',generated_smali)
    prefix='Lcom/projectinfinity/kodi/'
    activity=prefix+'InfinityLiveActivity;';state=prefix+'CobraCardsLayout$State;'
    revised={activity:patch.patch(originals[activity]),state:patch.physical(originals[state])}
    added={}
    for p in generated_smali.rglob('*.smali'):
        raw=p.read_text();name=raw.splitlines()[0].split()[-1]
        assert name not in originals;added[name]=raw
    assert set(added)=={prefix+'CobraCardsDrawerViewport;',prefix+'CobraCardsDrawerViewport$Journey;'}
    budget={activity:[patch.SIGNATURE],state:[patch.PHYSICAL]}
    for name,raw in revised.items():
        before,after=patch.methods(originals[name]),patch.methods(raw)
        assert sorted(k for k in before.keys()|after.keys() if before.get(k)!=after.get(k))==budget[name]
    changes=out/'changes';changes.mkdir()
    for name,raw in {**revised,**added}.items():
        p=changes/(name[1:-1]+'.smali');p.parent.mkdir(parents=True,exist_ok=True);p.write_text(raw)
    run('java','-cp',str(jars/'*'),'org.jf.smali.Main','assemble','--api','21',changes,'-o',out/'patch.dex')
    empty=out/'empty';empty.mkdir();run('java','-cp',str(jars/'*'),'org.jf.smali.Main','assemble',empty,'-o',out/'empty.dex')
    (out/'assignments.tsv').write_text(''.join(n+'\tCOBRA\n' for n in sorted(originals.keys()|added.keys())))
    (out/'origins.tsv').write_text(''.join(n+'\t'+n+'\n' for n in sorted(revised)))
    writer=out/'writer';writer.mkdir();cp=':'.join(str(p) for p in sorted(jars.glob('*.jar')))
    run('java','-m','jdk.compiler/com.sun.tools.javac.Main','-source','8','-target','8','-g:none','-Xlint:-options','-cp',cp,'-d',writer,ISO/'ModuleDexWriter.java')
    run('java','-cp',str(writer)+':'+cp,'org.jf.dexlib2.writer.pool.ModuleDexWriter',out/'owner-dex',out/'assignments.tsv',out/'origins.tsv',out/'patch.dex',out/'empty.dex',*inputs)
    # Re-disassemble the ACTUAL output, compare all original class definitions.
    observed={}
    for dex in sorted((out/'owner-dex/COBRA').glob('*.dex')):
        dest=out/('verify-'+dex.stem)
        run('java','-cp',str(jars/'*'),'org.jf.baksmali.Main','disassemble','--sequential-labels',dex,'-o',dest)
        for p in dest.rglob('*.smali'):
            raw=p.read_text();name=raw.splitlines()[0].split()[-1];assert name not in observed;observed[name]=raw
    assert observed.keys()==originals.keys()|added.keys()
    for name,raw in added.items():assert observed[name]==raw
    actual_changes={}
    for name,raw in originals.items():
        if raw==observed[name]:continue
        before,after=patch.methods(raw),patch.methods(observed[name])
        changed=sorted(k for k in before.keys()|after.keys() if before.get(k)!=after.get(k))
        assert name in budget and changed==budget[name],(name,changed)
        # No class-level field, interface, annotation or source drift permitted.
        def nonmethods(s):
            for body in patch.methods(s).values():s=s.replace(body,'')
            return ''.join(s.split())
        assert nonmethods(raw)==nonmethods(observed[name]),name
        actual_changes[name]=changed
    assert actual_changes==budget
    save(out/'BUILD.json',dict(status='PASS_EXACT435_DRAWER_DELTA_OWNER_ONLY',baseline_source='e0c6153588992001d84076d33fdf8f0d676c0d00',baseline_Cobra_ZIP_sha256=sha(bundle),baseline_DEX=meta['dex'],source_sha256=source_pin,compiler_sources={str(p.relative_to(REPO)):sha(p) for p in [HERE/'compile_owner.py',HERE/'patch.py',source,layout_source,ISO/'ModuleDexWriter.java']},changed_methods=actual_changes,new_classes=sorted(added),unchanged_classes=len(originals)-len(revised),output_DEX={p.name:sha(p) for p in sorted((out/'owner-dex/COBRA').glob('*.dex'))},APK='NOT_BUILT',release_version='NOT_RESERVED',Infinity='UNTOUCHED',shutdown='NOT_CHANGED_NOT_RUN',physical_Fold='NOT_RUN'))

if __name__=='__main__':
    p=argparse.ArgumentParser()
    for name in ('bundle','canonical','api','jars','android','d8','out'):p.add_argument('--'+name,type=Path,required=True)
    build(**vars(p.parse_args()))
