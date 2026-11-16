"""Selected standalone Cast ARM64 link only. Never build Kodi or an APK."""
from pathlib import Path
import hashlib, importlib.util, json, os, re, subprocess, sys

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
WORK = ROOT / 'cast502-ptl-work'
BASE = 'f35b6e6015d91185d76a12b4f21cec17c9eaa65ef07b17d8fed91a547dfffb28'
ENGINE = 'ed2d955d1825bf838ea50a712782e54b69926d40605270a2f241efd913202ee7'
LIBRARY = '613907f98b2a180f372413c70e2369d52872fcc9dc04385583c1c6515f28d53a'

def sha(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()

def main():
    request = json.loads((HERE / 'CI-NATIVE.json').read_bytes())
    assert request['case'] == 'standalone_cast_ptl_arm64_only'
    assert request['baseline'] == 2103502 and request['Kodi_build'] is False
    assert request['APK_build'] is False and request['owner_data'] == 'NOT_ACCESSED'
    assert os.environ['GITHUB_REF'] == 'refs/heads/work/infinity-2103502-six-repairs-20261116'
    assert os.environ['GITHUB_REPOSITORY'] == 'mahfouzhassine8-ops/project-infinity'
    for name, expected in request['inputs'].items():
        assert sha(ROOT / name) == expected, name
    assert request['inputs']['repairs/infinity-six-repairs-2103502-20261116/cast/native/InfinityCastRemux.cpp'] == '7129d341bdc696e96d2fd106fa15bb00a2f2692a3efb5186d71867433f9103a8'
    changes = subprocess.check_output(['git', 'diff', '--name-only', request['source_commit'], os.environ['GITHUB_SHA']], cwd=ROOT, text=True).splitlines()
    assert changes == [str((HERE / 'CI-NATIVE.json').relative_to(ROOT))], changes
    WORK.mkdir()
    # Reuse the existing authenticated artifact downloader, not its APK assembly.
    stage_path = HERE.parent / 'lock/application/stage.py'
    spec = importlib.util.spec_from_file_location('retained_artifact_reader', stage_path)
    stage = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(stage)
    apk, artifact = stage.artifact(WORK, 'baseline')
    assert sha(apk) == BASE
    # Retain the original NDK21 / FFmpeg6.0.1 public API recipe. Only its exact
    # authenticated baseline and source directory are rebound to this repair.
    prior = ROOT / 'repairs/infinity-cast-mkv-2103494-20261113/build.py'
    sys.argv = [str(prior), 'native', str(WORK), str(apk)]
    scope = {'__file__': str(prior), '__name__': '_retained_cast_component_recipe'}
    exec(compile(prior.read_bytes(), str(prior), 'exec'), scope)
    scope.update(HERE=HERE, ROOT=ROOT, BASE=BASE, ENGINE=ENGINE)
    scope['native']()
    before = WORK / 'base-native/libinfinitycastremux.so'
    assert sha(before) == LIBRARY
    after = WORK / 'native/libinfinitycastremux.so'
    tool = Path(os.environ['ANDROID_HOME']) / 'ndk/21.4.7075529/toolchains/llvm/prebuilt/linux-x86_64/bin/llvm-readelf'
    def abi(path):
        raw = subprocess.check_output([str(tool), '--dyn-syms', '--wide', '-d', str(path)], text=True)
        symbols = []
        for line in raw.splitlines():
            fields = line.split()
            if len(fields) >= 8 and fields[4] in ('GLOBAL', 'WEAK') and fields[5] in ('DEFAULT', 'PROTECTED') and fields[6] != 'UND':
                symbols.append((fields[3], fields[4], fields[5], fields[7]))
        return {'exports': sorted(symbols), 'dependencies': sorted(re.findall(r'Shared library: \[([^\]]+)\]', raw))}
    old, new = abi(before), abi(after)
    assert old == new, 'CAST_ABI_OR_DEPENDENCIES_CHANGED'
    assert sha(WORK / 'base-native/libkodi.so') == ENGINE, 'KODI_MUST_REMAIN_EXACT502'
    proof = json.loads((WORK / 'CAST-MKV-NATIVE.json').read_bytes())
    proof.update(status='PASS_SELECTED_CAST_PTL_ARM64_ONLY', baseline=2103502,
                 baseline_artifact=artifact, source=os.environ['GITHUB_SHA'],
                 actual_library='libinfinitycastremux.so', prior_library_sha256=LIBRARY,
                 Kodi_compiled=False, APK_built=False, ABI_preserved=new,
                 Android_execution='NOT_RUN', physical_TV='NOT_RUN',
                 reviewed_inputs=request['inputs'])
    # The original recipe's historical filename is not a release provenance claim.
    (WORK / 'CAST-MKV-NATIVE.json').unlink()
    (WORK / 'CAST-PTL-ARM64.json').write_text(json.dumps(proof, sort_keys=True, indent=2) + '\n')
    print('PASS_STANDALONE_CAST_ARM64_KODI_NOT_REBUILT')

if __name__ == '__main__':
    main()
