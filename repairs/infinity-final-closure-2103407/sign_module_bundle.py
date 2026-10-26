"""Existing permanent signer -> native verification -> matching component ZIPs.

CI internal integration artifact only. No APK, app installation or behavioral
test is started here; no private signing input enters the output directory.
"""
import base64
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile

import compose_firstparty
import module_bundle
import module_dex

ROOT=Path(__file__).parent.resolve()


def run(argv,env=None):
    result=subprocess.run(list(map(str,argv)),env=env,text=True,capture_output=True)
    if result.returncode:raise RuntimeError(result.stdout+result.stderr)
    return result.stdout


def build(sources,out):
    sources=Path(sources).resolve();out=Path(out).absolute()
    if out.exists():raise ValueError('Fresh internal signed bundle output required')
    scope=json.loads((ROOT/'SCOPE.json').read_text())
    if scope['baseline']['commit']!='0e8739d2d0e1be0ab8f127519b526556426fb160' or scope['candidate']['version_code']!=2103409:
        raise ValueError('Exact final scope required')
    credentials={name:os.environ[name] for name in ('INFINITY_STORE_PASSWORD','INFINITY_KEY_PASSWORD','INFINITY_KEY_ALIAS')}
    if not all(credentials.values()) or not os.environ.get('INFINITY_KEYSTORE_B64'):
        raise ValueError('Existing original signing credentials required')
    out.mkdir(parents=True)
    addons=out/'assets/addons';composition=compose_firstparty.compose(sources,addons)
    report=module_bundle.prepare(addons)
    java=Path(os.environ['JAVA_HOME'])/'bin/java';javac=java.with_name('javac')
    # KeyStore bytes exist only in the private temporary signing workspace.
    # No exported private key, replacement certificate or fallback signer.
    with tempfile.TemporaryDirectory(prefix='infinity-module-sign-') as temp:
        work=Path(temp);key=work/'existing.jks'
        key.write_bytes(base64.b64decode(os.environ['INFINITY_KEYSTORE_B64'],validate=True));key.chmod(0o600)
        classes=work/'classes';classes.mkdir()
        run([javac,'--release','8','-g:none','-Xlint:all,-options','-Werror','-d',classes,ROOT/'SignInfinityModules.java'])
        environment={name:os.environ[name] for name in ('PATH','JAVA_HOME') if name in os.environ};environment.update(credentials)
        proof=run([java,'-cp',classes,'SignInfinityModules',key,addons/module_bundle.CC/module_bundle.MANIFEST],environment)
        (out/'ORIGINAL-MODULE-SIGNATURE.txt').write_text(proof)
    return complete(sources,out)


def complete(sources,out):
    """Resume only exact, already-signed source; never trust a prior PASS flag."""
    sources=Path(sources).resolve();out=Path(out).resolve()
    if (out/'SIGNED-MODULE-BUNDLE.json').exists():raise ValueError('Completed generation must not be overwritten')
    scope=json.loads((ROOT/'SCOPE.json').read_text());addons=out/'assets/addons'
    if scope['baseline']['commit']!='0e8739d2d0e1be0ab8f127519b526556426fb160' or scope['candidate']['version_code']!=2103409:
        raise ValueError('Exact final scope required')
    with tempfile.TemporaryDirectory(prefix='infinity-exact-module-recipe-') as temp:
        expected=Path(temp)/'addons';composition=compose_firstparty.compose(sources,expected)
        report=module_bundle.prepare(expected)
        wanted={p.relative_to(expected).as_posix():p.read_bytes() for p in expected.rglob('*') if p.is_file()}
        actual={p.relative_to(addons).as_posix():p.read_bytes() for p in addons.rglob('*') if p.is_file()}
        signature=module_bundle.CC+'/'+module_bundle.MANIFEST+'.sig'
        if set(actual)!=set(wanted)|{signature} or any(actual[n]!=raw for n,raw in wanted.items()):
            raise ValueError('Already-signed module generation differs from the exact reviewed recipe')
    java=Path(os.environ['JAVA_HOME'])/'bin/java';javac=java.with_name('javac')
    verifier=out/'verify-native-bundle'
    run(['g++','-std=c++17','-O2','-Wall','-Wextra','-Werror',ROOT/'verify_module_bundle.cpp',
         ROOT/'isolated-native/InfinityModuleManifest.cpp','-lcrypto','-o',verifier])
    verified=run([verifier,addons,ROOT/'ORIGINAL-INFINITY-PUBLIC-KEY.pem'])
    (out/'NATIVE-ORIGINAL-KEY-VERIFICATION.txt').write_text(verified)
    # Distinct integration check: use the actual production public key and
    # actual JCA adapter on disposable host filesystem transport. This is NOT
    # Android17, a persistence checkpoint or a user profile migration.
    with tempfile.TemporaryDirectory(prefix='infinity-module-original-jca-') as temp:
        work=Path(temp);source=work/'InfinityInstalledCheckpointInstaller.java';source.write_text(module_dex.source())
        classes=work/'classes';classes.mkdir()
        run([javac,'--release','8','-g:none','-Xlint:all,-options','-Werror','-d',classes,source,*sorted((ROOT/'host-java').rglob('*.java'))])
        storage=work/'storage';installed=storage/'.kodi/addons';shutil.copytree(sources,installed)
        proof=run([java,'-cp',classes,'com.projectinfinity.kodi.Main',storage,out/'assets'])
        if 'VERIFIED_VERSION=0.3.5.41' not in proof:raise ValueError('Actual original-key Java migration unconfirmed')
        proof+=run([verifier,installed,ROOT/'ORIGINAL-INFINITY-PUBLIC-KEY.pem'])
        (out/'JCA-ORIGINAL-KEY-HOST-MIGRATION.txt').write_text(proof+'Host transport only. Android17 and physical Fold NOT RUN.\n')
    checksums=module_bundle.archive(addons,out/'components')
    report.update(signed=True,original_certificate_sha256=scope['baseline']['certificate_sha256'],
        native_original_key_verified=True,production_JCA_original_key_host_migration=True,
        components=checksums,composition=composition,Android17='NOT RUN',physical_Fold='NOT RUN',
        release_ready=False,APK_produced=False,internal_artifact_only=True)
    (out/'SIGNED-MODULE-BUNDLE.json').write_text(json.dumps(report,indent=2)+'\n')
    return report


if __name__=='__main__':
    import argparse
    parser=argparse.ArgumentParser();parser.add_argument('sources',type=Path);parser.add_argument('out',type=Path)
    parser.add_argument('--complete-only',action='store_true')
    args=parser.parse_args();report=complete(args.sources,args.out) if args.complete_only else build(args.sources,args.out)
    print(json.dumps({k:v for k,v in report.items() if k!='composition'},indent=2))
