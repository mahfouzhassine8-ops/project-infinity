"""Execute the production new and retained source verifiers on Android17 ART."""
import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import subprocess
from zipfile import ZipFile

HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1]

def run(args):subprocess.run([str(x) for x in args],check=True)
def main():
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('apk','parent','out'):p.add_argument('--'+name,type=Path,required=True)
    a=p.parse_args();a.out.mkdir(parents=True,exist_ok=True)
    spec=importlib.util.spec_from_file_location('adb_probe',ROOT/'repairs/android-checkpoint-shutdown/runtime-tests/essential_android_probe.py')
    probe=importlib.util.module_from_spec(spec);spec.loader.exec_module(probe)
    if probe.shell('getprop','ro.kernel.qemu').strip()!='1' or probe.shell('getprop','ro.build.version.sdk').strip()!='37':
        raise RuntimeError('Disposable Android17/API37 required')
    probe.adb('root');probe.adb('wait-for-device')
    classes=a.out/'classes';classes.mkdir()
    run(['javac','--release','8','-g:none','-Xlint:all','-Werror','-d',classes,HERE/'NavigationBindingProbe.java'])
    dex=a.out/'dex';dex.mkdir()
    sdk=Path(os.environ['ANDROID_HOME'])
    run([sdk/'build-tools/34.0.0/d8','--release','--min-api','21','--output',dex,*classes.rglob('*.class')])
    for label,apk in [('current',a.apk),('legacy',a.parent)]:
        with ZipFile(apk) as z:
            for name in z.namelist():
                prefix='assets/addons/script.infinity.commandcenter/'
                if name.startswith(prefix) and not name.endswith('/'):
                    path=a.out/label/'script.infinity.commandcenter'/name[len(prefix):]
                    path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(z.read(name))
    target='/data/local/tmp/infinity-navigation-binding'
    probe.shell('mkdir','-p',target)
    probe.adb('push',a.apk,target+'/candidate.apk')
    probe.adb('push',dex/'classes.dex',target+'/probe.dex')
    for label in ('current','legacy'):probe.adb('push',a.out/label,target+'/'+label)
    results=[]
    def check(label,method,expected):
        output=probe.shell('env','CLASSPATH='+target+'/candidate.apk:'+target+'/probe.dex',
            'app_process','/system/bin','infinity.qa.NavigationBindingProbe',method,target+'/'+label,str(expected).lower())
        if 'VERIFIED_PRODUCTION_BINDING='+method+':'+str(expected).lower() not in output:
            raise RuntimeError('Production ART verifier did not finish')
        results.append(dict(fixture=label,method=method,expected=expected,output=output.strip(),passed=True))
    check('current','verify',True)
    check('legacy','verifyReviewedController29',True)
    check('legacy','verify',False)
    file=target+'/current/script.infinity.commandcenter/saved_navigation.py'
    probe.shell('mv',file,file+'.original')
    check('current','verify',False)
    probe.shell('ln','-s',file+'.original',file)
    check('current','verify',False)
    probe.shell('rm','--',file)
    altered=a.out/'altered.py';altered.write_bytes((a.out/'current/script.infinity.commandcenter/saved_navigation.py').read_bytes()+b'\n# altered fixture\n')
    probe.adb('push',altered,file)
    check('current','verify',False)
    oversized=a.out/'oversized.py';oversized.write_bytes(b'x'*4194305);probe.adb('push',oversized,file)
    check('current','verify',False)
    probe.shell('rm','--',file);probe.shell('mv',file+'.original',file)
    check('current','verify',True)
    report=dict(passed=True,scope='production classes.dex on actual Android17 ART',
        candidate_apk_sha256=hashlib.sha256(a.apk.read_bytes()).hexdigest(),cases=results,
        original_cc29_verifier_preserved=True,probe_packaged=False,physical_fold_verified=False)
    (a.out/'ART-BINDING.json').write_text(json.dumps(report,indent=2)+'\n')

if __name__=='__main__':main()
