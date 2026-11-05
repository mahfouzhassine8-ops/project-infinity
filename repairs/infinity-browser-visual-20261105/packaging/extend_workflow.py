"""Exact branch/version registration in the existing sole signer; no new signer."""
from pathlib import Path
import subprocess
R=Path(__file__).resolve().parents[3]
P=R/'.github/workflows/infinity-combined-release.yml'
BASE='924fd6e593c4f0fcc7cf96bcd5f9b3347b3a295d'
OLD='work/infinity-master-testing-from-2103451-20261105'
NEW='work/infinity-browser-visual-correction-from-2103456-20261105'
OLDP='repairs/infinity-master-testing-20261105'
NEWP='repairs/infinity-browser-visual-20261105/packaging'
def one(s,a,b):
 assert s.count(a)==1,a[:130]
 return s.replace(a,b,1)

def generate(s):
 s=one(s,'review-controlled456-457]','review-controlled456-457, prepare-browser458-459, review-browser458-459]')
 a=s.index('  prepare-controlled456-457:\n');b=s.index('  combined:\n',a)
 jobs=s[a:b].replace(OLD,NEW).replace(OLDP,NEWP).replace('controlled456-457','browser458-459').replace('2103456','2103458').replace('2103457','2103459').replace('VERSION456','VERSION458').replace('VERSION457','VERSION459').replace('AUTHORITY456','AUTHORITY458').replace('AUTHORITY457','AUTHORITY459').replace('ISSUED456','ISSUED458').replace('Infinity456457','Infinity458459')
 jobs=jobs.replace('work/infinity-browser-visual-correction-from-2103458-20261105',NEW)
 jobs=jobs.replace('controlled456 and higher457','browser458 and higher459')
 # Add actual signed456 to preparation and source/member checks.
 needle='      - name: Focused package metadata and source tests before key access\n'
 download="""      - uses: actions/download-artifact@v4
        with: {artifact-ids: '13397163155', run-id: '41988386798', merge-multiple: true, github-token: '${{ github.token }}', path: protected456}
"""
 jobs=one(jobs,needle,download+needle)
 jobs=one(jobs,'--native controlled-engine --sdk', '--previous456 protected456/Infinity-2103456-Combined-Original-Signer.apk --native controlled-engine --sdk')
 jobs=jobs.replace('protected451/Infinity-2103451-Combined-Original-Signer.apk\n        run:', 'protected451/Infinity-2103451-Combined-Original-Signer.apk\n        run:')
 s=s[:b]+jobs+s[b:]
 # Existing combined issuer: routing only, original gate and sign steps identical.
 s=one(s,"|| github.ref == 'refs/heads/"+OLD+"')","|| github.ref == 'refs/heads/"+OLD+"' || github.ref == 'refs/heads/"+NEW+"')")
 needle='          if [ "$GITHUB_REF" = \'refs/heads/'+OLD+'\' ]; then\n'
 assert s.count(needle)==2
 s=s.replace(needle,'          if [ "$GITHUB_REF" = \'refs/heads/'+NEW+'\' ]; then\n            python3 -m py_compile '+NEWP+'/release_controlled.py\n          elif'+needle[len('          if'):],1)
 declaration="          pctrl=os.environ['GITHUB_REF']=='refs/heads/"+OLD+"'"
 assert s.count(declaration)==2
 s=s.replace(declaration,"          pvisual=os.environ['GITHUB_REF']=='refs/heads/"+NEW+"'\n          pctrl=pvisual or os.environ['GITHUB_REF']=='refs/heads/"+OLD+"'")
 s=one(s,"require(a['candidate_versionCode'] in (2103456,2103457),'EXACT_CONTROLLED_RECOVERY_VERSIONS')","require(a['candidate_versionCode'] in ((2103458,2103459) if pvisual else (2103456,2103457)),'EXACT_CONTROLLED_RECOVERY_VERSIONS')")
 s=one(s,"version=a['candidate_versionCode'];generation=42 if version==2103456 else 43;baseline=2103451","version=a['candidate_versionCode'];generation=(44 if version==2103458 else 45) if pvisual else (42 if version==2103456 else 43);baseline=2103451")
 s=one(s,"owner='INFINITY_MASTER_CONTROLLED_TEST' if version==2103456 else 'INFINITY_MASTER_FORWARD_RECOVERY'","owner=('INFINITY_BROWSER_CONTROLLED_TEST' if version==2103458 else 'INFINITY_BROWSER_FORWARD_RECOVERY') if pvisual else ('INFINITY_MASTER_CONTROLLED_TEST' if version==2103456 else 'INFINITY_MASTER_FORWARD_RECOVERY')")
 s=one(s,"sys_path='"+OLDP+"'","sys_path='"+NEWP+"' if pvisual else '"+OLDP+"'")
 s=one(s,"if version==2103456 else controlled.FROZEN_NATIVE","if version in (2103456,2103458) else controlled.FROZEN_NATIVE")
 # New version preflight, keeping old branch operations intact.
 marker='      - uses: actions/download-artifact@v4\n        with:\n          run-id: ${{ steps.selected.outputs.baseline_run }}'
 added="""      - name: Recheck exact browser or recovery version before issuance
        if: github.ref == 'refs/heads/BRANCH'
        run: python3 PREFIX/release_controlled.py versions --version "${{ steps.selected.outputs.version }}" --out VERSION-AVAILABILITY.json
      - uses: actions/download-artifact@v4
        if: github.ref == 'refs/heads/BRANCH'
        with: {artifact-ids: '13397163155', run-id: '41988386798', merge-multiple: true, github-token: '${{ github.token }}', path: protected456}
""".replace('BRANCH',NEW).replace('PREFIX',NEWP)
 s=one(s,marker,added+marker)
 s=one(s,"sys.path.insert(0,'"+OLDP+"' if pctrl else", "sys.path.insert(0,'"+NEWP+"' if pvisual else ('"+OLDP+"' if pctrl else")
 # Balance the one extra nested route expression, leaving old routes untouched.
 line=next(x for x in s.splitlines() if "sys.path.insert(0,'"+NEWP+"' if pvisual" in x)
 s=one(s,line,line+')')
 needle='          if [ "$GITHUB_REF" = \'refs/heads/'+OLD+'\' ]; then\n'
 final="""          if [ "$GITHUB_REF" = 'refs/heads/BRANCH' ]; then
            python3 PREFIX/release_controlled.py compare \\
              --baseline protected-baseline/Infinity-2103451-Combined-Original-Signer.apk \\
              --previous456 protected456/Infinity-2103456-Combined-Original-Signer.apk \\
              --candidate signed-combined/Infinity-${{ steps.selected.outputs.version }}-Combined-Original-Signer.apk \\
              --plan prepared-owner/PREPARATION.json --out signed-combined/preservation --sdk "$ANDROID_HOME/build-tools/35.0.0"
            cp prepared-owner/RECOVERY-VERIFICATION.json prepared-owner/MODULE-AUTHENTICATION.txt prepared-owner/NATIVE-COMPATIBILITY.json signed-combined/
            cp VERSION-AVAILABILITY.json signed-combined/
          elif""".replace('BRANCH',NEW).replace('PREFIX',NEWP)
 s=one(s,needle,final+needle[len('          if'):])
 return s

if __name__=='__main__':
 raw=subprocess.check_output(['git','show',BASE+':.github/workflows/infinity-combined-release.yml'],cwd=R).decode()
 P.write_text(generate(raw))
 gate=R/'repairs/dual-experience-isolation-2103420/release_gate.py'
 original=subprocess.check_output(['git','show',BASE+':'+str(gate.relative_to(R))],cwd=R)
 needle=("AUTHORITY_BRANCH = '"+OLD+"'").encode();assert original.count(needle)==1
 gate.write_bytes(original.replace(needle,("AUTHORITY_BRANCH = '"+NEW+"'").encode()))
