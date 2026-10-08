#!/usr/bin/env python3
"""Exact 3327 Android parent; keep 329's reader without its extra Activity."""
from pathlib import Path
import importlib.util,hashlib,json,re,subprocess
HERE=Path(__file__).resolve().parent
SRC='tools/android/packaging/xbmc/src/'
GUARD=SRC+'InfinityCloseGuardService.java.in'
PROGRESS=SRC+'InfinityCloseProgress.java.in'
POWER=SRC+'InfinityPowerControlActivity.java.in'
MANIFEST='tools/android/packaging/xbmc/AndroidManifest.xml.in'
INSTALL='cmake/scripts/android/Install.cmake'
OLD_NATIVE='a3f95a64b4433a999df37c18ecc48a3a43876c0cc49ae6c5433e82c98835764c'
PARENT_MAP='7a40be4f2515ed1304af01debb25529298b1db043c1af20fce7397b368c31e15'
PLACEHOLDER='0'*64
DYNAMIC={SRC+'InfinityHealthExport.java.in', SRC+'InfinityExitDiagnostics.java.in'}
ALLOWED={GUARD,PROGRESS,INSTALL}|DYNAMIC

def sha(b):return hashlib.sha256(b).hexdigest()
def snapshot(root):return {p.relative_to(root).as_posix():sha(p.read_bytes()) for p in root.rglob('*') if p.is_file()}
def require(ok,msg):
    if not ok:raise ValueError(msg)
def load(n,p):
    s=importlib.util.spec_from_file_location(n,p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m

def transform(source):
    original={n:(source/n).read_bytes() for n in (MANIFEST,POWER)}
    p328=load('polish328',HERE.parent/'closing-infinity-2103328/android_polish.py')
    guard=source/GUARD;guard.write_text(p328.transform(guard.read_text()))
    p329=load('live329',HERE.parent/'live-closing-2103329/live_apply.py')
    before=snapshot(source)
    require(sha(json.dumps(before,sort_keys=True,separators=(',',':')).encode())==p329.PARENT_MAP,'Not exact 328 presentation source')
    delta=json.loads((HERE.parent/'live-closing-2103329/android-delta.json').read_text())
    require({n:before.get(n) for n in delta['before']}==delta['before'],'329 reader preimage mismatch')
    subprocess.run(['patch','--batch','--fuzz=0','-p1','-i',str(HERE.parent/'live-closing-2103329/android.patch')],cwd=source,check=True)
    after=snapshot(source)
    require({n:after[n] for n in delta['after']}==delta['after'],'329 reader postimage mismatch')
    # Remove the entire extra task/window, not just its animations or deadline.
    for n,b in original.items():(source/n).write_bytes(b)
    (source/(SRC+'InfinityClosingActivity.java.in')).unlink()
    p=source/INSTALL;t=p.read_text();line='                  src/InfinityClosingActivity.java\n'
    require(t.count(line)==1,'Closing Activity registration mismatch');p.write_text(t.replace(line,''))
    t=guard.read_text()
    old='Intent open=InfinityClosingActivity.intent(this,session.pid,session.owner,session.started);'
    require(t.count(old)==1,'Closing Activity notification route mismatch')
    t=t.replace(old,'Intent open=new Intent(this,Splash.class).addFlags(Intent.FLAG_ACTIVITY_NEW_TASK|Intent.FLAG_ACTIVITY_SINGLE_TOP);')
    old='final String note=progress.note();'
    t=t.replace(old,old+'\n      final String message=progress.limited?"Last reported: "+phase.text:phase.text;')
    t=t.replace('phase.name,progress.limited?"Last reported: "+phase.text:phase.text,false);','phase.name,message,false);')
    t=t.replace('notice(phase.text)','notice(message)')
    guard.write_text(t)
    p=source/PROGRESS;t=p.read_text()
    require(t.count('infinity-shutdown-2103327-v1')==1,'Wrong reader native tag')
    t=t.replace('infinity-shutdown-2103327-v1','infinity-shutdown-2103330-v1')
    t=t.replace('session<0?status:"Finishing shutdown"','session<0?status:"Waiting for the next shutdown stage"')
    t=t.replace('name.equals("stop.cancel_jobs")||name.equals("pre.begin_job_shutdown")','name.equals("stop.cancel_jobs")||name.equals("pre.begin_job_shutdown")||name.startsWith("directory.")')
    p.write_text(t)
    for n in DYNAMIC:
        p=source/n;t=p.read_text();require(t.count(OLD_NATIVE)==1,'Native identity preimage missing: '+n)
        t=t.replace(OLD_NATIVE,PLACEHOLDER).replace('infinity-shutdown-2103327-v1','infinity-shutdown-2103330-v1')
        p.write_text(t)

def apply(source,proof,receipt,native_sha):
    require(re.fullmatch('[0-9a-f]{64}',native_sha) is not None and native_sha!=PLACEHOLDER,'Actual native hash required')
    parent=json.loads(proof.read_text());before=snapshot(source)
    require(parent['candidate']==2103327 and before==parent['after'],'Not exact 3327 Android parent')
    require(sha(json.dumps(before,sort_keys=True,separators=(',',':')).encode())==PARENT_MAP,'Full 3327 Android map mismatch')
    transform(source)
    templated=snapshot(source);delta=json.loads((HERE/'android-delta.json').read_text())
    changed={n for n in before.keys()|templated.keys() if before.get(n)!=templated.get(n)}
    require(changed==ALLOWED and {n:templated[n] for n in changed}==delta['after_template'],'Unexpected Android presentation delta')
    for n in DYNAMIC:
        p=source/n;t=p.read_text();require(t.count(PLACEHOLDER)==1,'Unbound identity marker missing');p.write_text(t.replace(PLACEHOLDER,native_sha))
    after=snapshot(source)
    result=dict(candidate=2103330,parent=2103327,locked_rollback=2103327,before=before,after=after,changed=sorted(changed),native_sha256=native_sha,extra_closing_activity=False,physical_device_verified=False,locked=False)
    receipt.write_text(json.dumps(result,indent=2)+'\n');return result

def verify(source,receipt):
    p=json.loads(receipt.read_text());require(p['candidate']==2103330,'Wrong Android receipt')
    require(p['changed']==sorted(ALLOWED) and snapshot(source)==p['after'],'Android source changed after tests')
    for n in (MANIFEST,POWER,SRC+'Splash.java.in',SRC+'Main.java.in',SRC+'InfinityKodiShutdown.java.in',SRC+'InfinityExitCompletion.java.in',SRC+'InfinityCloseNativeLease.java.in'):
        require(p['before'][n]==p['after'][n],'Protected shutdown/chooser source changed: '+n)
