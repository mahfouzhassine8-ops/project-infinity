"""Build independently addressable owner DEX payloads, preserving unknowns.

This is a build operation, not an ownership approval or signing gate bypass.
Unresolved classes remain visibly UNRESOLVED until separately reviewed.
"""
import argparse
from pathlib import Path
import subprocess
from inventory import HERE, APP, load, save, file_sha, digest
from prepare_runtime import COBRA_ROOTS,SHELL_ROOTS

def build(work,jars,baseline):
    original=load(HERE/'evidence/DEX-MEMBERS.json.gz');delta=load(work/'DELTA.json')
    for p in [work/'changed.dex',work/'helpers/classes.dex']:
        folder=work/(p.parent.name+'-checked-smali' if p.parent.name=='helpers' else 'changed-checked-smali')
        subprocess.run(['java','-cp',str(jars/'*'),'org.jf.baksmali.Main','disassemble','--sequential-labels',
                        str(p),'-o',str(folder)],check=True)
    definitions={p.read_text().splitlines()[0].split()[-1]:p.read_text()
                 for p in work.glob('*-checked-smali/**/*.smali')}
    owners={n:v['owner'] for n,v in original.items()}
    for n in definitions:
        root=n.removeprefix(APP).split('$')[0].removesuffix(';')
        if root in COBRA_ROOTS or root in ('CobraJavaPersistence','CobraJavaWriteBarrier','CobraBackgroundService',
                                         'CobraBackgroundSettings','CobraRuntimeLease','CobraBackgroundApiOutline','CobraPreferencePort'):owners[n]='COBRA'
        elif root in SHELL_ROOTS or root in ('ShellJavaPersistence','ShellJavaWriteBarrier','ExperienceLaunchPreferences'):owners[n]='CHOOSER_SHELL'
        elif root in ('CombinedDurability','OwnerDurabilityWiring','ExperienceChooserRefresh'):owners[n]='MINIMAL_ANDROID_CONTRACT'
        elif root in ('InfinityJavaPersistence','InfinityJavaWriteBarrier','InfinityExtendedBackgroundService',
                       'InfinityCloseNativeLease','InfinityCloseGuardService'):owners[n]='INFINITY'
        elif n not in owners:raise ValueError('Unowned generated definition: '+n)
    for n in owners:
        root=n.removeprefix(APP).split('$')[0].removesuffix(';')
        if root in SHELL_ROOTS:owners[n]='CHOOSER_SHELL'
        elif root in COBRA_ROOTS and 'ExternalSyntheticApiModelOutline' not in n:owners[n]='COBRA'
        if root in ('InfinityJavaPersistence','InfinityJavaWriteBarrier','InfinityExtendedBackgroundService'):owners[n]='INFINITY'
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
