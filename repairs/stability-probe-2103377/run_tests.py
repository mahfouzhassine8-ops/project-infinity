from pathlib import Path
import argparse,ast,json,os,shlex,shutil,subprocess,tempfile,time
HERE=Path(__file__).resolve().parent
def run(cmd):
    r=subprocess.run(cmd,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
    if r.returncode:raise RuntimeError(r.stdout)
    return r.stdout
def verify(source=None,out=None):
    out=Path(out or HERE/'host-results');out.mkdir(parents=True,exist_ok=True)
    if source is None:
        source=Path(tempfile.mkdtemp(prefix='infinity-probe-test-'))
        p=source/'xbmc/threads';p.mkdir(parents=True)
        text=(HERE/'fixture/xbmc/threads/Lockables.h').read_text()
        # The fixture transport added one newline; use the unchanged pinned text.
        import hashlib
        if hashlib.sha256(text.encode()).hexdigest()!='11640649df716783a636da54cc4bf3a1bab82b566369dca3a8344e37ef7e0718':text=text[:-1]
        module=ast.parse((HERE/'patch_native.py').read_text())
        fn=next(n for n in ast.walk(module) if isinstance(n,ast.FunctionDef) and n.name=='locks')
        ns={'once':lambda s,a,b:s.replace(a,b,1),'inc':'#if defined(TARGET_ANDROID)\n#include "threads/InfinityStabilityProbe.h"\n#endif\n'}
        exec(compile(ast.Module(body=[fn],type_ignores=[]),'<production-lock-patch>','exec'),ns)
        (p/'Lockables.h').write_text(ns['locks'](text))
        for name in ['InfinityStabilityProbe.h','InfinityPythonWaitProbe.h']:shutil.copyfile(HERE/name,p/name)
    include=Path(source)/'xbmc'
    cxx=os.environ.get('CXX','g++')
    common=[cxx,'-std=c++17','-O1','-pthread','-DTARGET_ANDROID','-I'+str(include)]
    run(common+[str(HERE/'test_probe.cpp'),'-o',str(out/'mutex-test')])
    a=run([str(out/'mutex-test'),str(out/'mutex-snapshot.jsonl')])
    config=shlex.split(os.environ.get('PYTHON_CONFIG','python3-config'))
    includes=shlex.split(run(config+['--includes']).strip());links=shlex.split(run(config+['--embed','--ldflags']).strip())
    # Some managed runtimes retain a stale unversioned development symlink.
    for index,flag in enumerate(links):
        if flag.startswith('-lpython'):
            for directory in [Path(f[2:]) for f in links if f.startswith('-L')]:
                real=directory/('lib'+flag[2:]+'.so.1.0')
                if real.is_file():links[index]=str(real);links+=['-Wl,-rpath,'+str(directory)];break
    run(common+includes+[str(HERE/'test_python.cpp'),'-o',str(out/'python-test')]+links)
    b=run([str(out/'python-test'),str(out/'python-snapshot.jsonl')])
    run(common+includes+[str(HERE/'blocked_wait_check.cpp'),'-o',str(out/'blocked-wait-check')]+links)
    c=run([str(out/'blocked-wait-check'),str(out/'blocked-wait-snapshot.jsonl')])
    rows=[json.loads(l) for l in (out/'mutex-snapshot.jsonl').read_text().splitlines()]
    blocked=next(r for r in rows if r['reason']=='controlled_contention')
    owner=next(r for r in blocked['locks'] if r['operation']=='owner_operation')
    assert any(t['waiting_slot']==owner['slot'] and t['tid']!=owner['owner_tid'] for t in blocked['threads'])
    receipt={'passed':True,'real_os_mutex_owner_waiter':True,'real_host_cpython_parent_child':True,'real_blocked_python_waits':True,'android_runtime_tested':False,'observational_candidate_not_a_fix':True}
    (out/'PROBE-HOST-RESULT.json').write_text(json.dumps(receipt,indent=2)+'\n')
    (out/'PROBE-HOST-RESULT.txt').write_text(a+b+c)
    print(a+b+c);return receipt
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--source',type=Path);p.add_argument('--out',type=Path);args=p.parse_args();verify(args.source,args.out)
