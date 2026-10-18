"""Versioned Android 11 input repair over the exact signed 2103385 candidate.

Reuse existing permanent signing and version-only manifest tools. Reassemble
one DEX, verify every decoded class against the exact expected instruction
delta, and copy all native libraries/assets/resources/other DEX bytes verbatim.
"""
import argparse
import copy
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import subprocess
import urllib.request
import zipfile

import systembars_patch as patch

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
PARENT = 'f0cda703ae43c3e41c952411c5d71622c9473cb6db92d17355cf21cf135e9240'
# Packaged (stripped) engine; raw compiled fcd206cd... is separately retained.
ENGINE = '4b61414f05d67eb6df1f8a32f46d6b96c4991f91674401727d6ea4987f0d01af'
DEX = '67e556c37a534be95789b3d88a9468219ecc5ea47d81dd5aab9b5911ba1c6573'
CODE = 2103386
NAME = '1.0.9-UI-Restoration-Fold-TEST02'
FILENAME = 'Infinity-2103386-UI-Restoration-TEST2.apk'

def sha(data): return hashlib.sha256(data).hexdigest()
def save(path, value): path.write_text(json.dumps(value, indent=2, sort_keys=True) + '\n')
def module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    obj = importlib.util.module_from_spec(spec); spec.loader.exec_module(obj); return obj

signer = module('systembars_permanent_signer', HERE.parent/'full-system-20261017/package_2103384_vfs.py')
guard = module('systembars_instruction_guard', HERE.parent/'cobra-clean-restart/bytecode_guard.py')

def normalized(text):
    # Smali omits trailing encoded static defaults (DEX's specified initial
    # false/null values). Limit equivalence to correctly typed STATIC fields;
    # never normalize nonzero values, instructions, or instance-field metadata.
    text = re.sub(r'(?m)^(\.field (?=[^\n]*\bstatic\b)[^\n]*:Z) = false$', r'\1', text)
    text = re.sub(r'(?m)^(\.field (?=[^\n]*\bstatic\b)[^\n]*:(?:L[^\n;]+;|\[[^\n ]+)) = null$', r'\1', text)
    return guard.normalize(text)

def verify_comparison_guard():
    guard.selftest()
    for original, implicit in (
        ('.field private static f:Z = false', '.field private static f:Z'),
        ('.field private static f:Ljava/lang/Object; = null', '.field private static f:Ljava/lang/Object;')):
        assert normalized(original) == normalized(implicit)
    for original, changed in (
        ('.field private f:Z = false', '.field private f:Z'),
        ('.field private static f:Z = true', '.field private static f:Z'),
        ('.field private static f:I = 1', '.field private static f:I'),
        ('const/4 v1, 0x0', 'const/4 v1, 0x1')):
        assert normalized(original) != normalized(changed)

def tools(directory):
    directory.mkdir(parents=True, exist_ok=True)
    for row in json.loads((HERE/'ANDROID-TOOLS.json').read_text()):
        path = directory/Path(row['path']).name
        if not path.exists():
            with urllib.request.urlopen('https://repo.maven.apache.org/maven2/'+row['path'], timeout=60) as stream:
                path.write_bytes(stream.read())
        assert sha(path.read_bytes()) == row['sha256'], 'Unverified DEX tool: '+str(path)
    return os.pathsep.join(str(p.resolve()) for p in sorted(directory.glob('*.jar')))

def disassemble(dex, out, classpath):
    subprocess.run(['java', '-cp', classpath, 'org.jf.baksmali.Main', 'disassemble',
                    '--sequential-labels', str(dex), '-o', str(out)], check=True)

def build(parent, out, tool_dir, sign):
    verify_comparison_guard()
    assert sha(parent.read_bytes()) == PARENT, 'Exact signed 2103385 parent required'
    assert not out.exists(), 'Refusing stale output directory'
    out.mkdir(parents=True)
    classpath = tools(tool_dir)
    with zipfile.ZipFile(parent) as source:
        assert source.testzip() is None and len(source.namelist()) == len(set(source.namelist()))
        assert sha(source.read('classes.dex')) == DEX
        assert sha(source.read('lib/arm64-v8a/libkodi.so')) == ENGINE
        original = out/'original.dex'; original.write_bytes(source.read('classes.dex'))
        smali = out/'smali'; disassemble(original, smali, classpath)
        before = {str(p.relative_to(smali)): p.read_text() for p in smali.rglob('*.smali')}
        assert len(before) == 7855 and patch.MAIN in before
        changed = patch.apply(before[patch.MAIN])
        (smali/patch.MAIN).write_text(changed)
        expected = dict(before, **{patch.MAIN: changed})
        rebuilt = out/'classes.dex'
        subprocess.run(['java', '-cp', classpath, 'org.jf.smali.Main', 'assemble',
                        str(smali), '-o', str(rebuilt)], check=True)
        decoded = out/'verified-smali'; disassemble(rebuilt, decoded, classpath)
        after = {str(p.relative_to(decoded)): p.read_text() for p in decoded.rglob('*.smali')}
        assert set(after) == set(before), 'Class inventory changed'
        differences = [name for name in expected if normalized(expected[name]) != normalized(after[name])]
        save(out/'DEX-INSTRUCTION-PRESERVATION.json', dict(
            classes_checked=len(before), unexpected_differences=differences,
            static_default_encoding_only_classes=[name for name in expected
                if guard.normalize(expected[name]) != guard.normalize(after[name])
                and normalized(expected[name]) == normalized(after[name])],
            only_changed_method='com.projectinfinity.kodi.Main.onResume()V',
            expected_delta='SDK_INT == 30: preserve flags, clear IMMERSIVE, set IMMERSIVE_STICKY',
            main_preimage_sha256=patch.PREIMAGE,
            main_expected_sha256=sha(changed.encode()),
            classes_dex_before=DEX, classes_dex_after=sha(rebuilt.read_bytes()),
            native_engine_sha256=ENGINE, native_engine_unchanged=True,
            shutdown_instructions_unchanged=True, input_candidate_2103385_retained=True))
        assert not differences, 'Unexpected decoded instructions: '+repr(differences)
        manifest = module('systembars_version_only_manifest', HERE.parent/'critical-preview-2103376/manifest_patch.py')
        manifest.PARENT_CODE=2103385; manifest.CODE=CODE
        manifest.PARENT_NAME='1.0.9-UI-Restoration-Fold-TEST01'; manifest.NAME=NAME
        xml, edits = manifest.patch(source.read('AndroidManifest.xml'))
        assert {e['field'] for e in edits} == {'versionCode','versionName'}
        unsigned=out/('unsigned-'+FILENAME)
        with zipfile.ZipFile(unsigned,'w') as target:
            for info in source.infolist():
                if signer.SIGNATURE.fullmatch(info.filename): continue
                payload = xml if info.filename=='AndroidManifest.xml' else rebuilt.read_bytes() if info.filename=='classes.dex' else source.read(info)
                target.writestr(copy.copy(info),payload)
        target_path=unsigned
        if sign:
            for key in ('INFINITY_KEYSTORE_B64','INFINITY_STORE_PASSWORD','INFINITY_KEY_PASSWORD','INFINITY_KEY_ALIAS'):
                assert os.environ.get(key), 'Missing permanent signing secret: '+key
            bt=Path(os.environ['ANDROID_HOME'])/'build-tools/34.0.0'
            signer.verify_signed(parent,bt)
            target_path=out/FILENAME
            subprocess.run(['bash',str(ROOT/'scripts/sign-infinity71.sh'),str(unsigned),str(target_path)],check=True)
            signer.verify_signed(target_path,bt)
            signer.output(bt/'zipalign','-c','-p','4',target_path)
            badge=signer.output(bt/'aapt','dump','badging',target_path)
            assert f"package: name='com.projectinfinity.kodi' versionCode='{CODE}'" in badge
            assert f"versionName='{NAME}'" in badge and 'application-debuggable' not in badge
        with zipfile.ZipFile(target_path) as final:
            assert final.testzip() is None
            names=lambda z:{n for n in z.namelist() if not signer.SIGNATURE.fullmatch(n)}
            assert names(final)==names(source)
            delta=sorted(n for n in names(source) if source.read(n)!=final.read(n))
            assert delta==['AndroidManifest.xml','classes.dex'], delta
        receipt=dict(source_commit=os.environ.get('GITHUB_SHA','local'),
            file=target_path.name,sha256=sha(target_path.read_bytes()),version_code=CODE,
            parent_sha256=PARENT,changed_unsigned_payload=delta,
            signer_sha256=signer.CERT if sign else None,permanently_signed=sign,
            native_engine_sha256=ENGINE,native_engine_unchanged=True,
            skin_and_helper_unchanged=True,only_api30_system_bar_compatibility=True,
            android_verified=False,physical_fold_verified=False,crash_fixed=False,locked=False)
        save(out/'SIGNED-2103386.json' if sign else out/'UNSIGNED-2103386.json',receipt)
        if sign: unsigned.unlink()
        print(json.dumps(receipt,indent=2),flush=True)
        return receipt

if __name__=='__main__':
    p=argparse.ArgumentParser()
    for name in ('parent','out','tools'): p.add_argument('--'+name,type=Path,required=True)
    p.add_argument('--sign',action='store_true')
    a=p.parse_args();build(a.parent,a.out,a.tools,a.sign)
