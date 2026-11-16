"""Build only com.projectinfinity.lockqa from actual State/Dialog and disposable instrumentation."""
from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED
import argparse
import hashlib
import json
import subprocess
import xml.etree.ElementTree as ET

HERE = Path(__file__).resolve().parent
LOCK = HERE.parent
PACKAGE = 'com.projectinfinity.lockqa'
ORIGINAL_CERT = 'd7adeb68e9341596a02bd3262b737a0f45fc6e771ed7e60285437e833b58c6d7'


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run(args):
    result = subprocess.run([str(arg) for arg in args], text=True, capture_output=True)
    if result.returncode:
        raise RuntimeError(result.stdout + result.stderr)
    return result.stdout + result.stderr


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--work', type=Path, required=True)
    parser.add_argument('--android-jar', type=Path, default=Path('/workspace/scratch/cast-sdk86/tools/android.jar'))
    parser.add_argument('--ecj', type=Path, default=Path('/workspace/scratch/network-baseline-2103477/ecj-3.37.0.jar'))
    parser.add_argument('--d8', type=Path, default=Path('/workspace/scratch/cast-sdk86/tools/d8.jar'))
    parser.add_argument('--aapt2', type=Path, default=Path('/workspace/scratch/cast-sdk86/tools/aapt2'))
    parser.add_argument('--apksigner', type=Path)
    parser.add_argument('--compile-only', action='store_true')
    parser.add_argument('--debug-sign', action='store_true')
    parser.add_argument('--receipt', type=Path)
    args = parser.parse_args()
    args.work.mkdir(parents=True, exist_ok=True)
    manifest = HERE / 'AndroidManifest.xml'
    assert ET.parse(manifest).getroot().get('package') == PACKAGE
    assert not ET.parse(manifest).getroot().findall('uses-permission')
    assert digest(args.android_jar) == '6cea1df3efb77103ac3e2beb9bf4718964b0e0869ab16d39d29d5cbae1c147ad', 'Unreviewed Android API jar'
    sources = [LOCK / 'java/com/projectinfinity/kodi' / name for name in ('InfinityVideoLockState.java', 'InfinityVideoLockDialog.java')]
    sources += [HERE / 'InfinityLockProbeActivity.java', HERE / 'InfinityLockProbeInstrumentation.java']
    snapshot = args.work / 'source'; snapshot.mkdir(exist_ok=True)
    inputs = []
    hashes = {}
    for source in sources:
        data = source.read_bytes(); hashes[str(source.relative_to(LOCK))] = hashlib.sha256(data).hexdigest()
        target = snapshot / source.name; target.write_bytes(data); inputs.append(target)
    classes = args.work / 'classes'; classes.mkdir(exist_ok=True)
    compile_log = run(['java', '-jar', args.ecj, '-1.8', '-classpath', args.android_jar, '-d', classes, *inputs])
    report = {'status': 'PASS_COMPONENT_COMPILE_ONLY', 'package': PACKAGE, 'sources': hashes,
              'android_jar_sha256': digest(args.android_jar), 'compiler_sha256': digest(args.ecj),
              'compile_output': compile_log, 'actual_Android': 'NOT_RUN', 'native_bridge': 'NOT_INCLUDED',
              'production_Main_or_stubs': 'NOT_INCLUDED', 'Kodi_shutdown': 'NOT_RUN', 'owner_installer': False}
    if not args.compile_only:
        jar = args.work / 'probe.jar'
        with ZipFile(jar, 'w', ZIP_DEFLATED) as archive:
            for source in sorted(classes.rglob('*.class')):
                archive.writestr(source.relative_to(classes).as_posix(), source.read_bytes())
        dex = args.work / 'dex'; dex.mkdir(exist_ok=True)
        run(['java', '-cp', args.d8, 'com.android.tools.r8.D8', '--min-api', '26', '--lib', args.android_jar, '--output', dex, jar])
        shell = args.work / 'shell.apk'
        run([args.aapt2, 'link', '--manifest', manifest, '-I', args.android_jar, '-o', shell])
        apk = args.work / 'CI-LOCK-PROBE-UNSIGNED-NOT-OWNER.apk'
        with ZipFile(apk, 'w', ZIP_DEFLATED) as out, ZipFile(shell) as base:
            for name in base.namelist(): out.writestr(name, base.read(name))
            for source in sorted(dex.glob('*.dex')): out.writestr(source.name, source.read_bytes())
        assert "package: name='" + PACKAGE + "'" in run([args.aapt2, 'dump', 'badging', apk])
        report['status'] = 'PASS_DISPOSABLE_UNSIGNED_PROBE_BUILD'
        if args.debug_sign:
            if args.apksigner is None: raise ValueError('--apksigner jar is required for disposable debug signing')
            key = args.work / 'DISPOSABLE-LOCK-PROBE-ONLY.jks'
            if not key.exists():
                run(['java', 'sun.security.tools.keytool.Main', '-genkeypair', '-keystore', key,
                     '-storepass', 'android', '-keypass', 'android', '-alias', 'lockqa', '-keyalg', 'RSA',
                     '-keysize', '2048', '-validity', '30', '-dname', 'CN=Disposable Lock Component CI'])
            signed = args.work / 'CI-LOCK-PROBE-DEBUG-NOT-OWNER.apk'
            run(['java', '-jar', args.apksigner, 'sign', '--ks', key, '--ks-key-alias', 'lockqa',
                 '--ks-pass', 'pass:android', '--key-pass', 'pass:android', '--out', signed, apk])
            signature = run(['java', '-jar', args.apksigner, 'verify', '--verbose', '--print-certs', signed])
            assert ORIGINAL_CERT not in signature.replace(':', '').lower(), 'Owner signer forbidden in component probe'
            report['debug_signature'] = signature; apk = signed
            report['status'] = 'PASS_DISPOSABLE_DEBUG_PROBE_BUILD'
        report.update(apk=str(apk), apk_sha256=digest(apk))
    receipt = args.receipt or args.work / 'BUILD.json'
    receipt.write_text(json.dumps(report, indent=2) + '\n')
    print(report['status']); print(compile_log, end='')


if __name__ == '__main__':
    main()
