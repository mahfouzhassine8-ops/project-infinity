#!/usr/bin/env python3
"""Run exact generated diagnostic Java against host/Android/SAF doubles.

This does not execute Android, claim Robolectric coverage, or verify a physical device.
"""
from pathlib import Path
import argparse,importlib.util,json,shutil,subprocess,hashlib
HERE=Path(__file__).resolve().parent
LEGACY=HERE.parents[1]/'cobra-diagnostics-2103156/tests'

def main():
    p=argparse.ArgumentParser();p.add_argument('--source',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args()
    actual=a.source/'tools/android/packaging/xbmc/src'
    if not actual.is_dir(): actual=a.source
    out=a.out.resolve();src=out/'src';classes=out/'classes';src.mkdir(parents=True,exist_ok=True)
    spec=importlib.util.spec_from_file_location('diagnostic_host_doubles',LEGACY/'runtime_host.py');legacy=importlib.util.module_from_spec(spec);spec.loader.exec_module(legacy)
    for name,text in legacy.STUBS.items():f=src/name;f.parent.mkdir(parents=True,exist_ok=True);f.write_text(text)
    package=src/'com/projectinfinity/kodi';digests={}
    for name in ['InfinityCobraDiagnostics','CobraDiagnosticArchive']:
        f=actual/f'{name}.java.in';body=f.read_text();digests[f.name]=hashlib.sha256(f.read_bytes()).hexdigest();(package/f'{name}.java').write_text(body.replace('@APP_PACKAGE@','com.projectinfinity.kodi'))
    for f in [LEGACY/'ArchiveTest.java',HERE/'EndpointRedactionTest.java',HERE/'DiagnosticExportHostTest.java']:shutil.copyfile(f,package/f.name)
    compiler=['javac'] if shutil.which('javac') else ['java','com.sun.tools.javac.Main']
    subprocess.run(compiler+['--release','8','-d',str(classes)]+[str(f) for f in src.rglob('*.java')],check=True)
    results=[]
    for name in ['ArchiveTest','EndpointRedactionTest','DiagnosticExportHostTest']:
        cmd=['java','-cp',str(classes),'com.projectinfinity.kodi.'+name]
        if name=='DiagnosticExportHostTest':cmd.append(str(out/'manifest.json'))
        r=subprocess.run(cmd,text=True,capture_output=True,timeout=40)
        results.append({'test':name,'exit_code':r.returncode,'output':r.stdout+r.stderr});print(r.stdout+r.stderr)
    extra=0
    if results[-1]['exit_code']==0:
        manifest=json.loads((out/'manifest.json').read_text())
        assert manifest['event_history_retained_limit']==47
        assert manifest['attachment_metadata']['kodi.log.txt']['file_modified_at_ms']==1577836800000
        assert manifest['attachment_metadata']['kodi.old.log.txt']['file_state']=='unavailable'
        assert 'file_age_ms' not in manifest['attachment_metadata']['kodi.old.log.txt']
        extra=4
    report={'source_sha256':digests,'results':results,'export_manifest_semantic_assertions':extra,'test_level':'production Java on host using disclosed Android lifecycle, PackageManager, exit-history, JSON serialization and SAF doubles','android_runtime_tested':False,'robolectric_tested':False,'physical_device_tested':False}
    (out/'results.json').write_text(json.dumps(report,indent=2)+'\n')
    raise SystemExit(any(r['exit_code'] for r in results))
if __name__=='__main__':main()
