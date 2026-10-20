#!/usr/bin/env python3
"""Read-only released-byte inspection and host integration tests.

No native engine compilation, workflow dispatch, signing, installing, user
profile mutation, or production source reconstruction occurs in this script.
Only original first-party APK code and upstream hash-pinned test inputs are used.
"""
from __future__ import annotations
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import urllib.request
import zipfile
import integration as i
import release as r

ROOT=r.ROOT
OUT=ROOT/'integration-preflight-output'
PARENT_SHA='778b84a5f0d8712f250c538bacfa3c01e1352a936e0b7b9aa79cbaada9b22dbb'

def one(root: str, pattern: str) -> Path:
    found=list((ROOT/root).rglob(pattern))
    if len(found)!=1:raise ValueError('Expected exactly one '+pattern+': '+repr(found))
    return found[0]

def save(name: str, data): (OUT/name).write_text(json.dumps(data,indent=2,sort_keys=True)+'\n')

def fixtures() -> dict[str,str]:
    apk=one('audit-original','Infinity-2103391-All-In-One-Bugfix-EXPERIMENTAL.apk')
    if r.sha(apk.read_bytes())!=r.APK_SHA:raise ValueError('Wrong signed 2103391 input')
    receipt=one('audit-original','INFINITY-2103391-SIGNED-EXPERIMENTAL.json')
    record=json.loads(receipt.read_text())
    if record['apk_sha256']!=r.APK_SHA or not record['signed_permanently']:raise ValueError('Original receipt mismatch')
    matches=[]
    for p in (ROOT/'audit-parent').rglob('*'):
        if p.is_file() and p.suffix=='.apk':
            data=p.read_bytes()
            if r.sha(data)==PARENT_SHA:matches.append(data)
        elif p.is_file() and p.suffix=='.zip':
            with zipfile.ZipFile(p) as z:
                for n in z.namelist():
                    if n.endswith('.apk'):
                        data=z.read(n)
                        if r.sha(data)==PARENT_SHA:matches.append(data)
    if len(matches)!=1:raise ValueError('Protected 2103390 APK not uniquely identified')
    data=Path('/mnt/data')
    parent=data/'Infinity-2103390-Nine-Item-Integration-EXPERIMENTAL.apk'
    parent.write_bytes(matches[0])
    alias=data/'integrated-2103390'/parent.name;alias.parent.mkdir(exist_ok=True)
    os.link(parent,alias)
    outer=data/'Infinity-2103390-Combined-Build-Artifact.zip'
    with zipfile.ZipFile(outer,'x',compression=zipfile.ZIP_STORED) as z:z.write(parent,parent.name)
    base=data/'infinity_group1_review/base'
    skin=data/'skin.infinity.diggz-1.0.5.228-from-Infinity-2103390.zip'
    with zipfile.ZipFile(parent) as z,zipfile.ZipFile(skin,'x',compression=zipfile.ZIP_DEFLATED) as dst:
        for n in z.namelist():
            if n.endswith('/'):continue
            if n.startswith('assets/addons/script.infinity.commandcenter/'):
                target=i.safe_path(base,n);target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(z.read(n))
            elif n.startswith('assets/addons/skin.infinity.diggz/'):
                dst.writestr(n[len('assets/addons/'):],z.read(n))
    env=dict(os.environ,INFINITY_2103390_APK=str(parent),INFINITY_2103390_ARTIFACT_ZIP=str(outer),
             INFINITY_2103391_APK=str(apk),INFINITY_2103391_RECEIPT=str(receipt),
             INFINITY_2103390_SKIN_ZIP=str(skin),INFINITY_GROUP1_CC_ROOT=str(base/'assets/addons/script.infinity.commandcenter'),
             INFINITY_2103390_HUB_PY=str(base/'assets/addons/script.infinity.commandcenter/resume_hub.py'))
    sys.path.insert(0,str(ROOT/'repairs/2103390-bugfixes/group2'))
    import native_addonbrowser_patch as browser
    native_ledger=json.loads(one('audit-original','GROUP7-NATIVE-SOURCE-ALLOWLIST.json').read_text())
    native_root=ROOT/'verified-native-test-fixtures'
    rows=[]
    for name in browser.FILES:
        expected=native_ledger['before'][name]
        url='https://raw.githubusercontent.com/xbmc/xbmc/21.3-Omega/'+name
        with urllib.request.urlopen(url,timeout=45) as response:body=response.read()
        actual=r.sha(body)
        rows.append(dict(path=name,expected_sha256=expected,actual_sha256=actual,match=actual==expected))
        if actual!=expected:
            save('native-fixture-provenance.json',rows)
            raise ValueError('Upstream fixture does not match original native-build input: '+name)
        staged=browser.patch_member(name,body)
        if r.sha(staged)!=native_ledger['after'][name]:raise ValueError('Patched fixture differs from actual 2103391 native build: '+name)
        target=i.safe_path(native_root,name);target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(body)
    save('native-fixture-provenance.json',rows)
    env['INFINITY_NATIVE_SOURCE_ROOT']=str(native_root)
    return env

def inspect_dex(apk: Path, classpath: str):
    descriptor='L'+i.TARGET_CLASS.removesuffix('.smali')+';'
    work=ROOT/'dex-inspection';work.mkdir()
    classes={};owner=[]
    with zipfile.ZipFile(apk) as z:
        for name in z.namelist():
            if not i.DEX.fullmatch(name):continue
            p=work/name;p.write_bytes(z.read(name))
            listed=subprocess.check_output(['java','-cp',classpath,'org.jf.baksmali.Main','list','classes',str(p)],text=True)
            items=[line.strip() for line in listed.splitlines() if line.strip()]
            if len(items)!=len(set(items)):raise ValueError('Duplicate classes inside DEX')
            for c in items:
                if c in classes:raise ValueError('Duplicate runtime class across DEX shards')
                classes[c]=name
            if descriptor in items:owner.append((name,p))
    if len(owner)!=1:raise ValueError('Startup router must occur in exactly one DEX shard')
    name,path=owner[0];dest=work/'original-smali'
    subprocess.run(['java','-cp',classpath,'org.jf.baksmali.Main','disassemble','--sequential-labels',str(path),'-o',str(dest)],check=True)
    target=dest/i.TARGET_CLASS;body=target.read_text()
    (OUT/'original-startup-router.smali.txt').write_text(body)
    save('original-dex-identity.json',dict(original_apk_sha256=r.APK_SHA,router_dex=name,
        router_dex_sha256=r.sha(path.read_bytes()),router_smali_sha256=r.sha(body.encode()),
        total_classes=len(classes),router_descriptor=descriptor,
        classes_modified=False,dex_rebuilt=False,android_execution=False))
    print('=== ORIGINAL STARTUP ROUTER BYTECODE ===\n'+body,flush=True)

def tests(env: dict[str,str]):
    rows=[]
    suites=[(f'group{g}',ROOT/f'repairs/2103390-bugfixes/group{g}') for g in range(1,8)]
    suites.append(('coherent92-and-integration',Path(__file__).resolve().parent))
    for name,path in suites:
        command=[sys.executable,'-m','unittest','discover','-s',str(path),'-p','test*.py','-v']
        try:
            result=subprocess.run(command,env=env,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,timeout=420)
            text=result.stdout;code=result.returncode
        except subprocess.TimeoutExpired as error:
            text=str(error.stdout or '')+'\nHOST TEST TIMEOUT';code=124
        (OUT/(name+'.log')).write_text(text)
        total=re.search(r'Ran (\d+) tests?',text);skips=re.search(r'skipped=(\d+)',text)
        row=dict(suite=name,returncode=code,tests=int(total.group(1)) if total else 0,
                 skipped=int(skips.group(1)) if skips else 0,android_execution=False,physical_fold_verified=False)
        row['passed']=code==0 and row['tests']>0 and row['skipped']==0
        rows.append(row)
        print('=== '+name+' ===\n'+text,flush=True)
    save('host-integration-results.json',rows)
    if not all(row['passed'] for row in rows):raise ValueError('Integration host suite incomplete; inspect saved failures/skips')
    return rows

def main():
    OUT.mkdir(exist_ok=True)
    env=fixtures()
    plan=i.prepare(Path(env['INFINITY_2103391_APK']),ROOT/'coherent92-integration-inputs')
    save('integration-input-summary.json',{k:v for k,v in plan.items() if k!='source_hashes'})
    cp=(ROOT/'integration-tools-classpath.txt').read_text().strip()
    inspect_dex(Path(env['INFINITY_2103391_APK']),cp)
    rows=tests(env)
    save('PREFLIGHT-STATUS.json',dict(state='SOURCE_AND_RELEASED_BYTECODE_PREFLIGHT_PASSED_NOT_AN_APK_BUILD',
        source_commit=os.environ['GITHUB_SHA'],run_id=os.environ['GITHUB_RUN_ID'],
        host_tests=sum(row['tests'] for row in rows),skipped=sum(row['skipped'] for row in rows),
        all_seven_groups_retained=True,source_inputs_staged=True,
        full_native_tree_bound=False,native_engine_compiled=False,
        java_dex_integrated=False,new_signed_apk=False,physical_fold_verified=False,final_lock=False))

if __name__=='__main__':main()
