"""Reconcile changed Infinity bundle contents with the actual staged APK.

Packaging helper only. Never changes either staged application DEX or engine.
The permanent signer and release-authority validators remain separate gates.
"""
from pathlib import Path
from zipfile import ZipFile
import hashlib, json, re, shutil, subprocess

MAIN='Lcom/projectinfinity/kodi/Main;'
LOCK=re.compile(r'^Lcom/projectinfinity/kodi/InfinityVideoLock(?:Bridge|Dialog|State)(?:\$[^;]+)?;$')

def sha(raw):return hashlib.sha256(raw).hexdigest()

def payload(baseline, actual, new_classes, allowed_members):
    """Keep every existing owner; only reviewed lock classes acquire ownership."""
    expected_new={'class:'+name for name in new_classes}
    assert all(LOCK.fullmatch(name) for name in new_classes)
    assert set(actual)-set(baseline)==expected_new
    assert not set(baseline)-set(actual)
    result={}
    for name,digest in actual.items():
        if name in baseline:
            owner=baseline[name]['owner']
            if digest!=baseline[name]['sha256']:
                assert name=='class:'+MAIN or name.startswith('member:') and name[7:] in allowed_members,name
                assert owner in ('INFINITY','CHOOSER_SHELL'),name
        else:
            assert name in expected_new;owner='INFINITY'
        result[name]={'owner':owner,'sha256':digest}
    assert baseline['class:'+MAIN]['owner']=='INFINITY'
    return result

def _class_files(root):
    result={}
    for path in sorted(Path(root).rglob('*.smali')):
        raw=path.read_bytes();name=raw.decode().splitlines()[0].split()[-1]
        assert name.startswith('L') and name.endswith(';') and name not in result
        result[name]=(path,sha(raw))
    return result

def rebuild_owned_main_dex(original, jars, work, actual_smali, expected_classes, new_classes):
    """Update only the affected owner archive, then verify every class identity.

    This archive DEX is needed by the existing ownership registry. The APK's
    already verified classes3/classes7 bytes are reused unchanged in the APK.
    """
    work.mkdir();before=work/'original.dex';before.write_bytes(original)
    folder=work/'before';tools=str(Path(jars).resolve()/'*')
    subprocess.run(['java','-cp',tools,'org.jf.baksmali.Main','disassemble','--sequential-labels',str(before),'-o',str(folder)],check=True)
    files=_class_files(folder)
    if MAIN not in files:return None
    for name,(_,digest) in files.items():
        assert name in expected_classes
        if name!=MAIN:assert expected_classes[name]==digest,('PREEXISTING_OWNER_CLASS_DIFFERS',name)
    copies={MAIN}|set(new_classes)
    for name in copies:
        assert name in actual_smali
        target=folder/(name[1:-1]+'.smali');target.parent.mkdir(parents=True,exist_ok=True)
        shutil.copyfile(actual_smali[name][0],target)
    after=work/'updated.dex'
    subprocess.run(['java','-cp',tools,'org.jf.smali.Main','assemble',str(folder),'-o',str(after)],check=True)
    check=work/'after'
    subprocess.run(['java','-cp',tools,'org.jf.baksmali.Main','disassemble','--sequential-labels',str(after),'-o',str(check)],check=True)
    verified=_class_files(check)
    assert set(verified)==set(files)|set(new_classes)
    for name,(_,digest) in verified.items():assert digest==expected_classes[name],('OWNED_DEX_CLASS_CHANGED',name)
    return after.read_bytes()

def rewrite(source, destination, apk, owner, actual, actual_smali, new_classes, jars, work,
            version, source_commit, inventory, bundles, copy_entry):
    """Preserve the archive format and unrelated DEX; replace changed bytes only."""
    work.mkdir(parents=True,exist_ok=False)
    with ZipFile(source) as before,ZipFile(apk) as app:
        meta=json.loads(before.read('component.json'));assert meta['owner']==owner
        changes={};rewritten_main=0
        for name,row in meta['members'].items():
            raw=app.read(name)
            if sha(raw)!=row['sha256']:
                changes['payload/'+name]=raw;row['sha256']=sha(raw)
        expected={name[6:]:row['sha256'] for name,row in actual.items() if row['owner']==owner and name.startswith('class:')}
        if new_classes and owner=='INFINITY':
            for index,name in enumerate(meta['dex']):
                value=rebuild_owned_main_dex(before.read(name),jars,work/('dex-'+str(index)),
                                             actual_smali,expected,new_classes)
                if value is not None:
                    assert rewritten_main==0,'DUPLICATE_MAIN_OWNER'
                    rewritten_main+=1;changes[name]=value;meta['dex'][name]=sha(value)
            assert rewritten_main==1,'ACTUAL_MAIN_OWNER_DEX_REQUIRED'
        meta['payload']={name:row for name,row in actual.items() if row['owner']==owner}
        meta.update(version=str(version)+'.'+owner.lower()+'.six502.1',approved_source=source_commit)
        meta['digest']=bundles.component_digest(meta['payload'],owner)
        with ZipFile(destination,'w',allowZip64=True) as out:
            for name in before.namelist():
                copy_entry(before,out,name,inventory.canonical(meta) if name=='component.json' else changes.get(name))
    return meta
