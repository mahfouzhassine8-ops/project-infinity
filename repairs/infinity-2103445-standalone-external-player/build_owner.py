"""Compile the new feature; preserve every original class except two Splash methods."""
import hashlib,json,os,re,shutil,subprocess,sys
from pathlib import Path
from zipfile import ZipFile,ZIP_DEFLATED
H=Path(__file__).resolve().parent;R=H.parents[1];ISO=R/'repairs/dual-experience-isolation-2103420'
sys.path.insert(0,str(ISO))
from inventory import file_sha,digest,load,save
from compile_runtime import ANDROID_SHA,D8_SHA
from patch_manifest import patch as patch_manifest
BASELINE='6cf75639a46ec6b0c858ae32abc102450fdc0974'
SPLASH='Lcom/projectinfinity/kodi/Splash;'
METHODS={'onCreate(Landroid/os/Bundle;)V','onNewIntent(Landroid/content/Intent;)V'}

def run(*args):subprocess.run(list(map(str,args)),check=True)
def classes(directory):return {p.read_text().splitlines()[0].split()[-1]:p for p in directory.rglob('*.smali')}
def methods(raw):return {m.group(1).split()[-1]:m.group(0) for m in re.finditer(r'^\.method ([^\n]+)\n.*?^\.end method',raw,re.M|re.S)}
def canonical_body(body):
    names={}
    def name(m):
        label=m.group(0)
        if label not in names:names[label]=':label_'+str(len(names))
        return names[label]
    return '\n'.join(line.strip() for line in re.sub(r':[A-Za-z_]+_[0-9a-f]+',name,body).splitlines() if line.strip())
def original_instructions_preserved(original,revised):
    # Cut exactly the new early routing block, then compare the complete old
    # method body with labels normalized for baksmali's sequential renumbering.
    old=original[original.index('\n',original.index('    .registers'))+1:]
    marker=re.search(r'    invoke-static \{p0, v0\}, Lcom/projectinfinity/kodi/ExternalVideoRoute;->open\(Landroid/app/Activity;Landroid/content/Intent;\)V\s+return-void\s*((?:\.line \d+\s*)*):cond_[0-9a-f]+\n',revised)
    assert marker is not None
    assert canonical_body(old)==canonical_body(marker.group(1)+revised[marker.end():])
def patch_splash(raw):
    before=methods(raw)
    for name in METHODS:
        method=before[name]
        at=method.index('\n',method.index('    .registers'))+1
        prefix='\n    invoke-virtual {p0}, Landroid/app/Activity;->getIntent()Landroid/content/Intent;\n    move-result-object v0\n' if name.startswith('onCreate') else '\n    move-object v0, p1\n'
        prefix+='''    invoke-static {v0}, Lcom/projectinfinity/kodi/ExternalVideoRoute;->accepts(Landroid/content/Intent;)Z
    move-result v1
    if-eqz v1, :external_original_path
'''
        prefix+= '    invoke-super {p0, p1}, Landroid/app/Activity;->'+name+'\n'
        prefix+='''    invoke-static {p0, v0}, Lcom/projectinfinity/kodi/ExternalVideoRoute;->open(Landroid/app/Activity;Landroid/content/Intent;)V
    return-void
    :external_original_path
'''
        raw=raw.replace(method,method[:at]+prefix+method[at:],1)
    assert set(methods(raw))==set(before)
    return raw

def build(out,bundles):
    out=out.resolve();out.mkdir(parents=True)
    tools=Path(os.environ.get('CARDS_TOOLS_ROOT','/workspace/cobra-evidence/tools'))
    jars=tools/'receipt-evidence/tool-jars';android=tools/'receipt-evidence/android-34.jar';d8=tools/'d8.jar'
    assert file_sha(android)==ANDROID_SHA and file_sha(d8)==D8_SHA
    assert {p.name:file_sha(p) for p in jars.glob('*.jar')}==load(R/'repairs/universal-persistence-2103401/RECEIPT-TOOL-PINS.json')
    authority=json.loads(subprocess.check_output(['git','show',BASELINE+':repairs/dual-experience-isolation-2103420/release-authority.json']))
    originals={};metadata={};original_paths={}
    for owner in ['CHOOSER_SHELL','INFINITY']:
        bundle=bundles/(owner+'.zip');assert file_sha(bundle)==authority['bundle_catalog']['bundles'][owner]['sha256']
        with ZipFile(bundle) as z:
            m=json.loads(z.read('component.json'));metadata[owner]=m
            assert len(m['dex'])==1
            p=out/(owner+'.dex');p.write_bytes(z.read('dex/part-0.dex'))
            target=out/('original-'+owner)
            run('java','-cp',jars/'*','org.jf.baksmali.Main','disassemble','--sequential-labels',p,'-o',target)
            paths=classes(target);original_paths[owner]=paths
            assert set(paths)=={n[6:] for n in m['payload'] if n.startswith('class:')}
            for n,p in paths.items():assert file_sha(p)==m['payload']['class:'+n]['sha256']
            originals[owner]={n:p.read_text() for n,p in paths.items()}
    compiled=out/'compiled';compiled.mkdir()
    sources=sorted((H/'runtime').glob('*.java'))
    run('java','-m','jdk.compiler/com.sun.tools.javac.Main','-source','8','-target','8','-g:none','-Xlint:-options','-cp',android,'-d',compiled,*sources)
    with ZipFile(out/'feature.jar','w',ZIP_DEFLATED) as z:
        for p in sorted(compiled.rglob('*.class')):z.write(p,p.relative_to(compiled).as_posix())
    generated=out/'generated';generated.mkdir()
    run('java','-cp',d8,'com.android.tools.r8.D8','--min-api','21','--lib',android,'--output',generated,out/'feature.jar')
    run('java','-cp',jars/'*','org.jf.baksmali.Main','disassemble','--sequential-labels',generated/'classes.dex','-o',out/'new-smali')
    additions=classes(out/'new-smali');all_hashes={};deltas={}
    for owner in ['CHOOSER_SHELL','INFINITY']:
        target=out/('edited-'+owner);shutil.copytree(out/('original-'+owner),target)
        if owner=='CHOOSER_SHELL':
            p=target/'com/projectinfinity/kodi/Splash.smali';p.write_text(patch_splash(p.read_text()))
        for n,p in additions.items():
            selected='CHOOSER_SHELL' if n.startswith('Lcom/projectinfinity/kodi/ExternalVideoRoute') else 'INFINITY'
            if owner==selected:
                dest=target/(n[1:-1]+'.smali');dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(p,dest)
        dex=out/(owner+'-new.dex')
        run('java','-cp',jars/'*','org.jf.smali.Main','assemble','--api','21','--jobs','1',target,'-o',dex)
        verify=out/('verify-'+owner)
        run('java','-cp',jars/'*','org.jf.baksmali.Main','disassemble','--sequential-labels',dex,'-o',verify)
        current=classes(verify);before=originals[owner];changed=[]
        assert set(before)<=set(current)
        for n,old in before.items():
            new=current[n].read_text()
            if old!=new:
                assert n==SPLASH and owner=='CHOOSER_SHELL'
                # Label numbering shifts after the added branch. Compare code
                # after removing only its approved prefix then normalize labels.
                a=methods(old);b=methods(new);assert a.keys()==b.keys()
                altered={k for k in a if a[k]!=b[k]};assert altered==METHODS
                for k in METHODS:original_instructions_preserved(a[k],b[k])
                for k in a.keys()-METHODS:assert a[k]==b[k]
                assert re.sub(r'^\.method [^\n]+\n.*?^\.end method','',old,flags=re.M|re.S)==re.sub(r'^\.method [^\n]+\n.*?^\.end method','',new,flags=re.M|re.S)
                changed.append(n)
        deltas[owner]={'changed':changed,'added':sorted(set(current)-set(before)), 'unchanged':len(before)-len(changed),'dex_sha256':file_sha(dex)}
        all_hashes[owner]={n:file_sha(p) for n,p in current.items()}
    with ZipFile(bundles/'MINIMAL_ANDROID_CONTRACT.zip') as z:
        original=z.read('payload/AndroidManifest.xml')
        (out/'AndroidManifest.xml').write_bytes(patch_manifest(original))
    sources={str(p.relative_to(R)):file_sha(p) for p in sorted(H.rglob('*')) if p.suffix in ('.java','.py')}
    save(out/'OWNER-BUILD.json',dict(baseline=BASELINE,sources=sources,deltas=deltas,manifest_sha256=file_sha(out/'AndroidManifest.xml'),no_446_code=True))
    save(out/'CLASS-HASHES.json',all_hashes)
    print(json.dumps(deltas,indent=2))

if __name__=='__main__':
    import argparse
    p=argparse.ArgumentParser();p.add_argument('--out',type=Path,required=True);p.add_argument('--bundles',type=Path,required=True)
    a=p.parse_args();build(a.out,a.bundles)
