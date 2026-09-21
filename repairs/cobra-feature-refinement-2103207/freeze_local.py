"""Generate the reviewed patch/CI bundle from the known parent and local edits."""
from pathlib import Path
import difflib,hashlib,importlib.util,json,re,subprocess,tempfile,shutil
ROOT=Path(__file__).resolve().parent
WORK=ROOT.parent
PARENT=WORK/'cobra-2103206-baseline'
CANDIDATE=WORK/'cobra-2103207-work'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def load(name,path):
    s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
def main():
    files={};patch='';inventory={}
    allowed={'CobraPresentationEffects.java.in','CobraQuickPeekSession.java.in','InfinityLiveActivity.java.in'}
    for p in sorted(PARENT.rglob('*')):
        if not p.is_file():continue
        name=str(p.relative_to(PARENT));q=CANDIDATE/name;inventory[name]=sha(p)
        if p.read_bytes()==q.read_bytes():continue
        assert p.name in allowed,name
        files[name]={'before':sha(p),'after':sha(q)}
        patch+=''.join(difflib.unified_diff(p.read_text().splitlines(True),q.read_text().splitlines(True),fromfile='a/'+name,tofile='b/'+name))
    assert len(files)==3 and len(inventory)==226,(len(files),len(inventory))
    (ROOT/'features.patch').write_text(patch)
    with tempfile.TemporaryDirectory(prefix='cobra207-patch-') as temp:
        target=Path(temp)
        for name in files:(target/name).parent.mkdir(parents=True,exist_ok=True);shutil.copy2(PARENT/name,target/name)
        subprocess.run(['git','apply','--check',str(ROOT/'features.patch')],cwd=target,check=True)
        subprocess.run(['git','apply',str(ROOT/'features.patch')],cwd=target,check=True)
        assert all(sha(target/n)==r['after'] for n,r in files.items())
    parser=load('parser197',WORK/'cobra-ci-inputs/audit206/repairs/cobra-original-player-menu-2103197/apply.py')
    parent=load('parent206',WORK/'cobra-ci-inputs/audit206/repairs/cobra-media-calls-2103206/apply.py')
    activity='tools/android/packaging/xbmc/src/InfinityLiveActivity.java.in'
    before=(PARENT/activity).read_text();after=(CANDIDATE/activity).read_text();protected={}
    for kind,names in [('class',parent.PROTECTED_CLASSES),('method',parent.PROTECTED_METHODS)]:
        for name in names:
            if name=='buildPlayer':continue # same construction delegated to shared factory; buffer/network logic stays
            a=parser.member(before,name,kind) if kind=='class' else parser.member(before,name)
            b=parser.member(after,name,kind) if kind=='class' else parser.member(after,name)
            assert a==b,'Protected member changed: '+name
            protected[name]=hashlib.sha256(a.encode()).hexdigest()
    (ROOT/'protected-members.json').write_text(json.dumps(protected,indent=2)+'\n')
    cases={}
    for p in sorted((ROOT/'tests').glob('*.java')):
        owner='com.projectinfinity.kodi.'+p.stem
        names=re.findall(r'@Test\b(?:(?!@Test).)*?public void (\w+)\s*\(',p.read_text(),re.S)
        assert names and len(names)==len(set(names));cases[owner]=sorted([[owner,n] for n in names])
    (ROOT/'new-cases.json').write_text(json.dumps(cases,indent=2)+'\n')
    workflow=(WORK/'cobra-2103206-evidence/recipe/infinity-2103206-media-calls.yml').read_text()
    workflow=workflow.replace('name: Infinity | 2103206 Media During Calls','name: Infinity | 2103207 Feature Refinement')
    workflow=workflow.replace('branches: [infinity-cobra-2103206-media-calls-rc1]','branches: [infinity-cobra-2103207-feature-refinement-rc1]')
    workflow=workflow.replace("'.github/workflows/infinity-2103206-media-calls.yml'","'.github/workflows/infinity-2103207-feature-refinement.yml'")
    workflow=workflow.replace("'repairs/cobra-media-calls-2103206/**'","'repairs/cobra-feature-refinement-2103207/**'")
    workflow=workflow.replace('group: infinity-2103206-','group: infinity-2103207-')
    workflow=workflow.replace("with: {ref: '${{ github.sha }}', path: audit206, persist-credentials: false}","with: {ref: 6f18a77e83f961a870975e6686154bf7e5a3126f, path: audit206, persist-credentials: false}\n      - name: Isolated 207 candidate\n        uses: actions/checkout@v7\n        with: {ref: '${{ github.sha }}', path: audit207, persist-credentials: false}\n      - name: Exact locked 206 rollback\n        uses: actions/download-artifact@v8\n        with: {name: Infinity-2103206-Media-Calls-TEST-CANDIDATE-Replica-1-Attempt-1, run-id: 35589429412, github-token: '${{ github.token }}', path: baseline206}")
    start=workflow.index('      - name: Publish verified 2103206 TEST CANDIDATE')
    end=workflow.index('      - name: Preserve complete 2103206 audit evidence',start)
    workflow=workflow[:start]+'''      - name: Apply reviewed 207 refinement after original 665 parent tests pass
        run: |
          python3 audit207/repairs/cobra-feature-refinement-2103207/ci.py upgrade
          python3 audit205/repairs/cobra-final-features-2103205/host_timeshift_adapter.py --fixture audit199/repairs/cobra-power-audit-2103199/tests/host_timeshift.py --source kodi/tools/android/packaging/xbmc/src/InfinityLiveActivity.java.in --out audit207/host_timeshift
          python3 audit199/repairs/cobra-power-audit-2103199/tests/host_timeshift_stop.py --source kodi/tools/android/packaging/xbmc/src/InfinityLiveActivity.java.in --out audit207/host_timeshift_stop
          python3 audit199/repairs/cobra-power-audit-2103199/tests/display_geometry_host.py --activity kodi/tools/android/packaging/xbmc/src/InfinityLiveActivity.java.in --out audit207/display_geometry_host

      - name: Build and verify 207 without rebuilding native engine
        env:
          INFINITY_KEYSTORE_B64: ${{ secrets.INFINITY_KEYSTORE_B64 }}
          INFINITY_STORE_PASSWORD: ${{ secrets.INFINITY_STORE_PASSWORD }}
          INFINITY_KEY_PASSWORD: ${{ secrets.INFINITY_KEY_PASSWORD }}
          INFINITY_KEY_ALIAS: ${{ secrets.INFINITY_KEY_ALIAS }}
        run: |
          python3 scripts/package_background_resume.py --source kodi --base-apk baseline168native/Infinity-1.0.9-Cobra-Status-Bar-PythonInvoker-Stability-RC1.apk --build-dir refinement207-build --out signed207
          python3 audit207/repairs/cobra-feature-refinement-2103207/ci.py verify

      - name: Rerun every inherited case with documented supersessions and new 207 cases
        run: python3 audit207/repairs/cobra-feature-refinement-2103207/ci.py tests

      - name: Publish verified 207 TEST CANDIDATE only after all gates
        uses: actions/upload-artifact@v7
        with:
          name: Infinity-2103207-Feature-Refinement-TEST-CANDIDATE-Replica-${{ matrix.replica }}-Attempt-${{ github.run_attempt }}
          path: signed207/
          if-no-files-found: error
          compression-level: 0
          retention-days: 90

'''+workflow[end:]
    workflow=workflow.replace('Preserve complete 2103206 audit evidence','Preserve complete 207 and parent audit evidence')
    workflow=workflow.replace('name: Infinity-2103206-Media-Calls-Evidence-', 'name: Infinity-2103207-Feature-Refinement-Evidence-')
    workflow=workflow.replace('            audit206/\n','            audit206/\n            audit207/\n            signed207/*.json\n            signed207/*.txt\n')
    workflow=workflow.replace('name: Preserve exact locked 2103205 rollback','name: Preserve exact locked 2103206 rollback')
    workflow=workflow.replace('name: Infinity-2103205-Exact-Rollback-Before-2103206-', 'name: Infinity-2103206-Exact-Rollback-Before-2103207-')
    workflow=workflow.replace('          path: baseline205/\n','          path: baseline206/\n')
    (ROOT/'infinity-2103207-feature-refinement.yml').write_text(workflow)
    recipe={str(p.relative_to(ROOT)):sha(p) for p in ROOT.rglob('*') if p.is_file() and p.suffix not in ('.pyc',) and p.name not in ('reviewed.json','publish-tree.json') and '__pycache__' not in p.parts}
    (ROOT/'reviewed.json').write_text(json.dumps(dict(parent_commit='6f18a77e83f961a870975e6686154bf7e5a3126f',parent_inventory=inventory,files=files,recipe_hashes=recipe),indent=2)+'\n')
    trees=[]
    for p in sorted(ROOT.rglob('*')):
        if not p.is_file() or '__pycache__' in p.parts or p.name=='publish-tree.json':continue
        rel=str(p.relative_to(ROOT));name='repairs/cobra-feature-refinement-2103207/'+rel
        trees.append(dict(path=name,mode='100644',type='blob',content=p.read_text()))
        if p.suffix=='.yml':trees.append(dict(path='.github/workflows/'+p.name,mode='100644',type='blob',content=p.read_text()))
    (ROOT/'publish-tree.json').write_text(json.dumps(trees))
    print(json.dumps(dict(changed_files=len(files),parent_files=len(inventory),protected_members=len(protected),new_tests=sum(map(len,cases.values())),published_files=len(trees))))
if __name__=='__main__':main()
