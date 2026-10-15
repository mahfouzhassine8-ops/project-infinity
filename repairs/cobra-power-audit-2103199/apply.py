#!/usr/bin/env python3
"""Apply independently reproduced repairs to the exact 2103198 Android source."""
from pathlib import Path
import argparse, hashlib, importlib.util, json, shutil, zipfile

ROOT = Path(__file__).resolve().parent
ACT = 'tools/android/packaging/xbmc/src/InfinityLiveActivity.java.in'
ARCHIVE = 'tools/android/packaging/xbmc/src/CobraDiagnosticArchive.java.in'
DIAGNOSTICS = 'tools/android/packaging/xbmc/src/InfinityCobraDiagnostics.java.in'
RECORDING = 'tools/android/packaging/xbmc/src/InfinityCobraRecordingService.java.in'
MANIFEST = 'tools/android/packaging/xbmc/AndroidManifest.xml.in'
YTDL = 'tools/android/packaging/xbmc/src/content/XBMCYTDLContentProvider.java.in'

def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()

def require(v, message):
    if not v:
        raise RuntimeError(message)

def module(name):
    spec = importlib.util.spec_from_file_location(name, ROOT / (name + '.py'))
    loaded = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(loaded)
    return loaded

def apply(source, receipt, out):
    data = json.loads(receipt.read_text())
    require(data['version_code'] == 2103198, 'Requires exact passed 2103198 source reconstruction')
    for path, row in data['files'].items():
        require(sha(source/path) == row['after'], 'Parent source mismatch: ' + path)
    out.mkdir(parents=True, exist_ok=False)
    # Retain every Android packaging input before changing any source.
    with zipfile.ZipFile(out/'pre-change-android-source.zip', 'w', zipfile.ZIP_DEFLATED) as z:
        for folder in ('tools/android/packaging', 'media'):
            for p in sorted((source/folder).rglob('*')):
                if p.is_file():
                    z.write(p, str(p.relative_to(source)))
        z.write(source/'cmake/scripts/android/Install.cmake', 'cmake/scripts/android/Install.cmake')
    shutil.copy2(receipt, out/'pre-change-source-receipt.json')
    transforms = [
        (ACT, 'apply_timeshift', 'transform'),
        (ACT, 'apply_display', 'transform'),
        (ACT, 'apply_ui', 'transform'),
        (ACT, 'apply_timeshift_stop', 'transform'),
        (ARCHIVE, 'apply_diagnostics', 'transform_archive'),
        (DIAGNOSTICS, 'apply_diagnostics', 'transform_diagnostics'),
        (RECORDING, 'apply_recording', 'transform'),
        (MANIFEST, 'apply_packaging', 'transform'),
        (YTDL, 'apply_ytdl', 'transform'),
    ]
    files = {}
    for path, name, function in transforms:
        p = source/path
        before = p.read_text()
        files.setdefault(path, {'before': sha(p)})
        after = getattr(module(name), function)(before)
        require(isinstance(after, str), 'Repair returned no source: ' + name)
        p.write_text(after)
        files[path]['after'] = sha(p)
    # Every unrelated receipt file must be unchanged. Native code is never an input.
    for path, row in data['files'].items():
        if path not in files:
            require(sha(source/path) == row['after'], 'Unrelated source changed: ' + path)
    report = {'parent_build':2103198, 'protected_baseline':2103197, 'files':files,
              'native_engine_recompiled':False, 'new_controls':False,
              'physical_device_verified':False}
    (out/'patch.json').write_text(json.dumps(report, indent=2)+'\n')
    print('PASS: surgical repairs applied; unrelated source hashes preserved')

if __name__ == '__main__':
    p=argparse.ArgumentParser()
    p.add_argument('--source',type=Path,required=True)
    p.add_argument('--receipt',type=Path,required=True)
    p.add_argument('--out',type=Path,required=True)
    a=p.parse_args(); apply(a.source,a.receipt,a.out)
