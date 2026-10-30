"""Prepare only exact accepted signed431 projection QA; never uses old host guards."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
from zipfile import ZipFile, ZIP_DEFLATED

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[3]
APK_SHA = '3fbf5abebdbdd9f96f30a69a213f086c617d2a9395f892dd1ce0142bf1b64471'
SOURCE = '9ccc4c362a65118eeba38a8e7e4b0de5723c69af'


def sha(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def prepare(apk, dex2jar, out):
    apk = apk.resolve(); dex2jar = dex2jar.resolve(); out = out.resolve()
    assert sha(apk) == APK_SHA, 'Exact accepted signed431 APK required'
    verification = json.loads((REPO/'repairs/cobra-next-from-2103427/results/signed2103431/INDEPENDENT-VERIFICATION.json').read_text())
    assert verification['source'] == SOURCE and verification['apk_sha256'] == APK_SHA
    assert verification['versionCode'] == 2103431
    pins = {row['apk']: row['sha256'] for row in verification['ordered_DEX_exact']}
    assert set(pins) == {'classes.dex', 'classes2.dex', 'classes3.dex', 'classes4.dex', 'classes5.dex'}
    # Check every source DEX before any translation or preparation mutation.
    with ZipFile(apk) as archive:
        dex = {name: archive.read(name) for name in pins}
    assert {name: hashlib.sha256(raw).hexdigest() for name, raw in dex.items()} == pins
    out.mkdir(parents=True, exist_ok=False)
    errors = out/'translation-errors'; errors.mkdir()
    translated = {}
    for name, raw in dex.items():
        source = out/name; source.write_bytes(raw)
        target = out/(Path(name).stem+'-translated.jar')
        command = ['java', '-cp', str(dex2jar/'lib/*'), 'com.googlecode.dex2jar.tools.Dex2jarCmd',
                   str(source), '-o', str(target), '-e', str(errors/(Path(name).stem+'.zip'))]
        subprocess.run(command, check=True)
        translated[name] = target
    for group, names in [('production', ('classes4.dex', 'classes5.dex')),
                         ('support', ('classes.dex', 'classes2.dex', 'classes3.dex'))]:
        seen = set()
        with ZipFile(out/(group+'.jar'), 'w', ZIP_DEFLATED) as target:
            for name in names:
                with ZipFile(translated[name]) as archive:
                    for member in archive.namelist():
                        if not member.endswith('.class') or member in seen:
                            continue
                        if member.startswith(('com/google/common/', 'com/google/thirdparty/')):
                            continue
                        if group == 'support' and not member.startswith(('com/projectinfinity/kodi/', 'androidx/')):
                            continue
                        seen.add(member); target.writestr(member, archive.read(member))
    tests = out/'src/test/java/com/projectinfinity/kodi'; tests.mkdir(parents=True)
    test = HERE/'CobraProjectionBenchmarkTest.java'; shutil.copyfile(test, tests/test.name)
    pom = (REPO/'repairs/dual-experience-isolation-2103420/tests/pom.xml').read_text()
    pom = pom.replace('${runtime.work}/changed-host.jar', str(out/'production.jar')).replace('${baseline.dex}/application-host.jar', str(out/'support.jar'))
    sdk = Path.home()/'.m2/repository/org/robolectric/android-all-instrumented/15-robolectric-12650502-i7'
    if (sdk/('android-all-instrumented-'+sdk.name+'.jar')).exists():
        pom = pom.replace('<systemPropertyVariables>', '<systemPropertyVariables><robolectric.offline>true</robolectric.offline><robolectric.dependency.dir>'+str(sdk)+'</robolectric.dependency.dir><projection.output>'+str(out/'measurements')+'</projection.output>')
    else:
        pom = pom.replace('<systemPropertyVariables>', '<systemPropertyVariables><projection.output>'+str(out/'measurements')+'</projection.output>')
    (out/'pom.xml').write_text(pom)
    libs = out/'android-test-libs'; libs.mkdir()
    for artifact, name in [('monitor', 'monitor.jar'), ('espresso-idling-resource', 'espresso.jar')]:
        archives = sorted((Path.home()/'.m2/repository/androidx/test').rglob(artifact+'-*.aar'))
        assert archives, 'Existing trusted Android test dependency cache required: '+artifact
        with ZipFile(archives[-1]) as archive:
            (libs/name).write_bytes(archive.read('classes.jar'))
    record = {'runtime': 'Robolectric API35 HOST actual accepted431 DEX; no Activity.onCreate/network/player/shutdown',
              'source': SOURCE, 'versionCode': 2103431, 'APK_sha256': APK_SHA, 'DEX_sha256': pins,
              'test_SHA256': sha(test), 'prepare_SHA256': sha(Path(__file__)),
              'translated_jar_SHA256': {name: sha(path) for name, path in translated.items()},
              'translation_error_archives': [p.name for p in errors.iterdir()],
              'physical_Fold': 'NOT_RUN', 'shutdown': 'NOT_RUN', 'production_changes': 'NONE'}
    (out/'INPUTS.json').write_text(json.dumps(record, indent=2)+'\n')
    print(json.dumps(record, indent=2))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    for name in ('apk', 'dex2jar', 'out'):
        parser.add_argument('--'+name, type=Path, required=True)
    prepare(**vars(parser.parse_args()))
