"""Validate frozen source, exact inherited identities and reproducible Java-only workflow."""
from pathlib import Path
import argparse, ast, json, subprocess, yaml
from apply import ROOT, checked_review

def main():
    p=argparse.ArgumentParser();p.add_argument('--require-frozen',action='store_true');args=p.parse_args()
    repo=ROOT.parents[1];prior=repo/'repairs/cobra-final-features-2103205'
    for path in ROOT.glob('*.py'):ast.parse(path.read_text(),filename=str(path))
    inherited=json.loads((ROOT/'inherited-android-cases.json').read_text())
    assert inherited==json.loads((prior/'inherited-android-cases.json').read_text())|json.loads((prior/'new-android-cases.json').read_text())
    assert len(inherited)==64 and sum(map(len,inherited.values()))==637
    text=(repo/'.github/workflows/infinity-2103206-media-calls.yml').read_text()
    old=(repo/'.github/workflows/infinity-2103205-final-features.yml').read_text()
    workflow=yaml.safe_load(text);job=workflow['jobs']['audit-package']
    assert job['strategy']=={'fail-fast':False,'matrix':{'replica':[1,2]}}
    assert workflow['concurrency']['cancel-in-progress'] is False
    assert workflow['permissions']=={'contents':'read','actions':'read'}
    assert 'ref: d4abe960873929ebee3f13af6a976c19011d0cdc, path: audit205' in text
    assert 'run-id: 35582474904' in text and 'path: baseline205' in text
    parent='python3 audit205/repairs/cobra-final-features-2103205/ci.py upgrade'
    current='python3 audit206/repairs/cobra-media-calls-2103206/ci.py upgrade'
    assert text.count(parent)==text.count(current)==1
    assert text.index(parent)<text.index(current)<text.index('id: build206')
    for phase in ['verify','deliver']:assert text.count('python3 audit206/repairs/cobra-media-calls-2103206/ci.py '+phase)==1
    assert 'steps.build206.outcome' in text
    assert '--base-apk baseline168native/Infinity-1.0.9-Cobra-Status-Bar-PythonInvoker-Stability-RC1.apk' in text
    for line in old.splitlines():
        if "'--tests'," in line or 'adapt_inherited_tests.py' in line or 'theme-fixture-adapter.py' in line:assert line in text,line
    assert "'--tests','com.projectinfinity.kodi.Cobra2103206*'" in text
    for step in job['steps']:
        if 'run' not in step:continue
        result=subprocess.run(['bash','-n'],input=step['run'],capture_output=True,text=True)
        assert result.returncode==0,(step.get('name'),result.stderr)
        inside=False;lines=[]
        for line in step['run'].splitlines():
            if "python3 - <<'PY'" in line:inside=True;lines=[]
            elif inside and line=='PY':compile('\n'.join(lines),str(step.get('name')),'exec');inside=False
            elif inside:lines.append(line)
        assert not inside
    if args.require_frozen:
        review=checked_review();new=json.loads((ROOT/'new-android-cases.json').read_text())
        assert not(set(inherited)&set(new)) and review['new_android_cases']==sum(map(len,new.values()))
        assert set(review['files'])=={'tools/android/packaging/xbmc/src/InfinityLiveActivity.java.in'}
        assert review['new_source_files']==0
    print('PASS: 637 inherited identities preserved, isolated audio-policy delta, two Java-only replicas')
if __name__=='__main__':main()
