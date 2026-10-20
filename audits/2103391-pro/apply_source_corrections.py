#!/usr/bin/env python3
"""Apply only reproducible source corrections on the isolated Pro audit branch.

No signing, APK generation, installing, diagnostics publication or physical pass.
The native change still requires full native-build/source-ledger qualification.
"""
from __future__ import annotations
import hashlib,json,os,re,subprocess,sys,zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'repairs/2103390-bugfixes/group7'))
import release_coherence as c
OUT=ROOT/'pro-correction-output';OUT.mkdir(exist_ok=True)

def replace_once(text,old,new):
    if text.count(old)!=1:raise ValueError('Source anchor missing/ambiguous: '+old[:100])
    return text.replace(old,new,1)

def one(root,pattern):
    paths=list(Path(root).rglob(pattern))
    if len(paths)!=1:raise ValueError('Expected one '+pattern)
    return paths[0]

def prepare_group1_fixtures():
    """Use only unchanged first-party members of the verified parent APK.

    These are temporary disposable-runner fixtures, not Android installations.
    Native checkout omissions remain visible rather than replaced with stubs.
    """
    parent=Path(os.environ['INFINITY_2103390_APK'])
    if c.digest(parent.read_bytes())!='778b84a5f0d8712f250c538bacfa3c01e1352a936e0b7b9aa79cbaada9b22dbb':
        raise ValueError('Wrong original Group1 fixture APK')
    alias=Path('/mnt/data/integrated-2103390')/parent.name
    alias.parent.mkdir(parents=True,exist_ok=True)
    if alias.exists():
        if c.digest(alias.read_bytes())!=c.digest(parent.read_bytes()):raise ValueError('Existing fixture differs')
    else:
        os.link(parent,alias)
    base=Path('/mnt/data/infinity_group1_review/base')
    skin=Path('/mnt/data/skin.infinity.diggz-1.0.5.228-from-Infinity-2103390.zip')
    cc_count=0;skin_count=0
    with zipfile.ZipFile(parent) as src, zipfile.ZipFile(skin,'x',compression=zipfile.ZIP_DEFLATED) as dst:
        for name in src.namelist():
            if name.endswith('/'):continue
            if name.startswith('assets/addons/script.infinity.commandcenter/'):
                target=base/name
                if not target.resolve().is_relative_to(base.resolve()):raise ValueError('Invalid fixture path')
                target.parent.mkdir(parents=True,exist_ok=True)
                target.write_bytes(src.read(name));cc_count+=1
            elif name.startswith('assets/addons/skin.infinity.diggz/'):
                dst.writestr(name[len('assets/addons/'):],src.read(name));skin_count+=1
    if cc_count<13 or skin_count<14:raise ValueError('Incomplete verified Group1 fixtures')
    (OUT/'group1-fixture-provenance.json').write_text(json.dumps(dict(
        original_parent_sha256=c.digest(parent.read_bytes()),command_center_files=cc_count,
        skin_members=skin_count,fixture_members_byte_identical_to_signed_parent=True,
        native_checkout_synthesized=False,user_files_used=False),indent=2)+'\n')

def main():
    apk=one('audit-original','Infinity-2103391-All-In-One-Bugfix-EXPERIMENTAL.apk')
    receipt=one('audit-original','INFINITY-2103391-SIGNED-EXPERIMENTAL.json')
    if c.digest(apk.read_bytes())!='47609f2ada1d6bbc7cdbddb791d11815bdbf1100a083bd8205d60ac21c882151':raise ValueError('Wrong signed APK')
    with zipfile.ZipFile(apk) as z:
        payload={n[len('assets/addons/'):]:z.read(n) for n in z.namelist() if n.startswith('assets/addons/') and not n.endswith('/') and n[len('assets/addons/'):].split('/')[0] in (c.CC,)+c.CONSUMERS}
    before={};after={}
    def stage(path,value):
        p=ROOT/path
        before[path]=c.digest(p.read_bytes());after[path]=c.digest(value.encode())
        if before[path]==after[path]:raise ValueError('No source correction: '+path)
        p.write_text(value)
    native=(ROOT/c.NATIVE_PATH).read_text()
    if subprocess.check_output(['git','hash-object',c.NATIVE_PATH],text=True).strip()!='98034cea15287905d6ef0e53e22daefadcd9c0f8':raise ValueError('Unexpected native preimage')
    fixed=c.append_reviewed_group1_contracts(native,payload)
    stage(c.NATIVE_PATH,fixed)
    path='repairs/2103390-bugfixes/group7/export_matched_addons.py'
    text=(ROOT/path).read_text()
    text=replace_once(text,'from zipfile import ZIP_DEFLATED, ZipFile\n','from zipfile import ZIP_DEFLATED, ZipFile\n\nfrom release_coherence import require_export_coherence\n')
    text=replace_once(text,'    report = verify_signed_receipt(apk, signed_receipt)\n','    report = verify_signed_receipt(apk, signed_receipt)\n    # Before any output: manifest, controller and compiled native identity agree.\n    require_export_coherence(apk, PACKAGES)\n')
    for old,new in [('"0.3.5.20", "0.3.5.21"','"0.3.5.20", "0.3.5.20"'),('"1.0.1", "1.0.2"','"1.0.1", "1.0.1"'),('"0.1.2", "0.1.3"','"0.1.2", "0.1.2"'),('"1.0.5.228", "1.0.5.229"','"1.0.5.228", "1.0.5.228"')]:text=replace_once(text,old,new)
    text=replace_once(text,'EXPECTED_CHANGED_ADDONS = {\n    "skin.infinity.diggz",\n    "script.infinity.commandcenter",\n    "script.infinity.watchedbridge",\n    "script.infinity.uirepair",\n}','EXPECTED_CHANGED_ADDONS = set()  # No manifest rewrites after native compilation/signing.')
    text=replace_once(text,'For four changed add-ons, bump the standalone addon.xml version attribute only\nto make normal Kodi install-over upgrades unambiguous; every OTHER addon\nmember must be byte-identical to the permanently signed 2103391 APK.','Export must preserve EVERY signed member, including addon.xml. A required\ninstall-over version must be finalized across the controller, dependent guards\nand native compilation BEFORE signing, never invented by ZIP distribution.\nThe original 2103391 binary is intentionally rejected by the coherence gate;\nthis source correction is NOT an installable repair or downgrade instruction.')
    stage(path,text)
    # Correct the audit itself: complete alternatives are OR, not an AND of all
    # historical pins. Inactive legacy compat variants are not rollout failures.
    path='audits/2103391-pro/inspect_release.py';text=(ROOT/path).read_text()
    start=text.index('    pairs=sorted(set(re.findall(')
    end=text.index("    report['standalone_member_changes']",start)
    replacement="""    import sys
    sys.path.insert(0,str(ROOT/'repairs/2103390-bugfixes/group7'))
    from release_coherence import controller_report
    original_source=subprocess.check_output(['git','show','83df773b742dc3f7e576a90157a04c15bc61fdb3:'+str(contract.relative_to(ROOT))],cwd=ROOT,text=True)
    comparisons=[dict(payload=label,**controller_report(payload,original_source,native))
                 for label,payload in [('embedded',embedded),('standalone',installed)]]
    report['native_contract_comparisons']=comparisons
    report['native_contract_mismatches']=[v for v in comparisons if not v['coherent']]
    report['legacy_contract_variants_are_alternatives']=True
    report['inactive_compat_072_preserved_not_activated']=True
"""
    text=text[:start]+replacement+text[end:];stage(path,text)
    path='repairs/2103390-bugfixes/group2/test_native_addonbrowser_patch.py';text=(ROOT/path).read_text()
    old='''                for old,new in p.PATCHES[filename]:
                    self.assertIn(new,patched)
                    self.assertNotIn(old,patched)
'''
    new='''                expected=original.decode()
                for old,new in p.PATCHES[filename]:
                    self.assertEqual(expected.count(old),1)
                    expected=expected.replace(old,new,1)
                    self.assertEqual(patched.count(new),1)
                    # Additive include/constructor hooks intentionally retain
                    # the old text inside the replacement. Assert exact output,
                    # not the false premise that every old substring vanishes.
                    if old not in new:
                        self.assertNotIn(old,patched)
                self.assertEqual(patched,expected)
'''
    stage(path,replace_once(text,old,new))
    prepare_group1_fixtures()
    # Expose real fixture requirements so missing source cannot become a pass.
    fixtures=[]
    for p in sorted((ROOT/'repairs/2103390-bugfixes').glob('group*/test*.py')):
        lines=p.read_text().splitlines()
        for i,line in enumerate(lines):
            if any(x in line for x in ('environ','/mnt/data','ORIGINAL_TOAST','SOURCE_ROOT','skipUnless','BASE_DIR','ADDONS =','ADDONS=')):
                fixtures.append(str(p.relative_to(ROOT))+':'+str(i+1)+': '+' | '.join(lines[max(0,i-1):min(len(lines),i+3)]))
    (OUT/'fixture-requirements.txt').write_text('\n'.join(line.rstrip() for line in fixtures)+'\n')
    (OUT/'source-correction-scope.json').write_text(json.dumps(dict(before=before,after=after,
        old_apk_unchanged=True,new_apk_built=False,physical_fold_tested=False,
        old_apk_release_gate='REJECTED',native_change='three exact complete CC20 Group1 variants; all legacy variants and classification logic retained',
        no_shutdown_owner_count_or_policy_change=True,cobra_code_changed=False,
        known_open=['CC21 installed-profile recovery and duplicate resident ownership','full Android compilation and source ledgers','seven-group physical Fold acceptance','SIGSEGV 139 root cause','Group1 task19 deferred'],
        final_lock=False),indent=2)+'\n')
    (OUT/'old-apk-controller-report.json').write_text(json.dumps(c.controller_report(payload,native),indent=2)+'\n')
    print('=== STAGED SOURCE CORRECTIONS ===\n'+(OUT/'source-correction-scope.json').read_text())
    print('=== FIXTURE REQUIREMENTS ===\n'+(OUT/'fixture-requirements.txt').read_text())
    with open(os.environ['GITHUB_ENV'],'a') as f:
        f.write('INFINITY_2103391_APK='+str(apk.resolve())+'\nINFINITY_2103391_RECEIPT='+str(receipt.resolve())+'\n')
    subprocess.run(['git','diff','--check'],check=True)

if __name__=='__main__':main()
