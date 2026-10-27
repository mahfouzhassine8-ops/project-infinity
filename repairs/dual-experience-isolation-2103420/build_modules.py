"""Build independently addressable DEX payloads using explicit owner identities.

This is a build operation, not an ownership approval or signing gate bypass.
Unreviewed identities fail classification; release approval is a separate gate.
"""
import argparse
from pathlib import Path
import subprocess
from inventory import HERE, APP, load, save, file_sha, digest
from review_ownership import class_owner

def build(work,jars,baseline):
    original=load(HERE/'evidence/DEX-MEMBERS.json.gz');delta=load(work/'DELTA.json')
    baseline_members=load(HERE/'evidence/OWNERSHIP-MAP.json')['members']
    expected_dex={n:v['sha256'] for n,v in baseline_members.items() if n.startswith('classes') and n.endswith('.dex')}
    if {p.name:file_sha(p) for p in baseline.glob('classes*.dex')}!=expected_dex:
        raise ValueError('Raw DEX inputs must match the signed baseline exactly')
    for p in [work/'changed.dex',work/'helpers/classes.dex']:
        folder=work/(p.parent.name+'-checked-smali' if p.parent.name=='helpers' else 'changed-checked-smali')
        subprocess.run(['java','-cp',str(jars/'*'),'org.jf.baksmali.Main','disassemble','--sequential-labels',
                        str(p),'-o',str(folder)],check=True)
    definitions={p.read_text().splitlines()[0].split()[-1]:p.read_text()
                 for p in work.glob('*-checked-smali/**/*.smali')}
    selected={p.read_text().splitlines()[0].split()[-1]:p.read_text() for p in baseline.glob('*-smali/**/*.smali')}
    selected.update(definitions)
    policy=load(HERE/'ownership-reviewed-roots.json')
    owners={n:class_owner(n,text,policy) for n,text in selected.items()}
    assignments=work/'ASSIGNMENTS.tsv';assignments.write_text(''.join(n+'\t'+o+'\n' for n,o in sorted(owners.items())))
    origins=work/'ORIGINS.tsv';origins.write_text(''.join(n+'\t'+d['origin']+'\n' for n,d in sorted(delta['classes'].items())))
    host=work/'host';host.mkdir(exist_ok=True)
    cp=':'.join(str(p) for p in sorted(jars.glob('*.jar')))
    subprocess.run(['java','-m','jdk.compiler/com.sun.tools.javac.Main','-source','8','-target','8','-g:none','-Xlint:-options',
                    '-cp',cp,'-d',str(host),str(HERE/'ModuleDexWriter.java')],check=True)
    subprocess.run(['java','-cp',str(host)+':'+cp,'org.jf.dexlib2.writer.pool.ModuleDexWriter',str(work/'owner-dex'),str(assignments),str(origins),
                    str(work/'changed.dex'),str(work/'helpers/classes.dex'),*map(str,sorted(baseline.glob('classes*.dex')))],check=True)
    # Resolve symbolic references again after actual DEX repacking.
    checked={};modules={}
    for p in sorted((work/'owner-dex').glob('*/*.dex')):
        folder=p.with_suffix('')
        subprocess.run(['java','-cp',str(jars/'*'),'org.jf.baksmali.Main','disassemble','--sequential-labels',str(p),'-o',str(folder)],check=True)
        names=[]
        for smali in folder.rglob('*.smali'):
            raw=smali.read_bytes();n=raw.decode().splitlines()[0].split()[-1]
            if n in checked:raise ValueError('Duplicate assembled class')
            checked[n]=digest(raw);names.append(n)
        modules[str(p.relative_to(work))]={'sha256':file_sha(p),'owner':p.parent.name,'classes':sorted(names)}
    if set(checked)!=set(owners):raise ValueError('Assembly class set differs')
    untouched=set(original)-set(delta['classes'])
    for n in untouched:
        if checked[n]!=original[n]['sha256']:raise ValueError('Unchanged original definition altered: '+n)
    save(work/'MODULE-BUILD.json',{'status':'BUILT_PENDING_OWNERSHIP_AND_RUNTIME_REVIEW',
         'untouched_baseline_classes_verified':len(untouched),'classes':{n:{'owner':owners[n],'sha256':s} for n,s in checked.items()},
         'modules':modules,'release_approved':False})

if __name__=='__main__':
    p=argparse.ArgumentParser()
    for n in ('work','jars','baseline'):p.add_argument('--'+n,required=True,type=Path)
    build(**vars(p.parse_args()))
