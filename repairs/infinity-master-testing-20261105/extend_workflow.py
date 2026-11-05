"""Create only the controlled owner route inside the existing sole signer."""
from pathlib import Path
import subprocess

ROOT=Path(__file__).resolve().parents[2]
PATH=Path('.github/workflows/infinity-combined-release.yml')
BASE='4c4094918845bd42649f50bcb094d2ba334a51bc'
BRANCH='work/infinity-master-testing-from-2103451-20261105'
PREFIX='repairs/infinity-master-testing-20261105'

def once(text,old,new):
    assert text.count(old)==1,old[:100]
    return text.replace(old,new,1)

def generate(original):
    s=once(original,'options: [final-combined, prepare-preview451, prepare-kodi452, prepare-kodi453, prepare-ui454-455]',
        'options: [final-combined, prepare-preview451, prepare-kodi452, prepare-kodi453, prepare-ui454-455, prepare-controlled456-457, review-controlled456-457]\n      prepared_run:\n        description: Completed official controlled preparation run for read-only authority review\n        type: string\n        required: false\n        default: "0"')
    jobs='''  prepare-controlled456-457:
    name: Frozen451 controlled456 and higher457 recovery preparation
    if: github.event_name == 'workflow_dispatch' && github.ref == 'refs/heads/BRANCH' && inputs.operation == 'prepare-controlled456-457'
    runs-on: ubuntu-22.04
    timeout-minutes: 60
    env:
      PYTHONDONTWRITEBYTECODE: '1'
      GH_TOKEN: ${{ github.token }}
    steps:
      - uses: actions/checkout@v4
        with: {fetch-depth: 0, persist-credentials: false}
      - uses: actions/setup-java@v4
        with: {distribution: temurin, java-version: '21'}
      - uses: actions/setup-python@v5
        with: {python-version: '3.12'}
      - uses: android-actions/setup-android@9fc6c4e9069bf8d3d10b2204b1fb8f6ef7065407
        with: {packages: 'build-tools;35.0.0', log-accepted-android-sdk-licenses: false}
      - name: Verify exact source versions sole signer and authenticated artifact pins
        id: pins
        run: |
          set -euo pipefail
          python3 -m pip install PyYAML==6.0.3
          python3 repairs/dual-experience-isolation-2103420/signer_policy.py check --out SIGNER-ROUTES.json
          python3 PREFIX/release_controlled.py versions --version 2103456 --out VERSION456.json
          python3 PREFIX/release_controlled.py versions --version 2103457 --out VERSION457.json
          python3 PREFIX/release_controlled.py metadata --out INPUT-METADATA.json
          python3 - <<'PYCODE'
          import json,os
          from pathlib import Path
          p=json.loads(Path('PREFIX/ENGINE-INPUT.json').read_text())['artifact_identity']
          with open(os.environ['GITHUB_OUTPUT'],'a') as f:f.write('native_id='+str(p[0])+'\\nnative_run='+str(p[1])+'\\n')
          PYCODE
      - uses: actions/download-artifact@d3f86a106a0bac45b974a628896c90dbdf5c8093
        with: {artifact-ids: '13200361701', run-id: '41568721264', merge-multiple: true, github-token: '${{ github.token }}', path: protected451}
      - uses: actions/download-artifact@d3f86a106a0bac45b974a628896c90dbdf5c8093
        with: {artifact-ids: '13200925524', run-id: '41568721264', merge-multiple: true, github-token: '${{ github.token }}', path: protected451-components}
      - uses: actions/download-artifact@d3f86a106a0bac45b974a628896c90dbdf5c8093
        with:
          artifact-ids: ${{ steps.pins.outputs.native_id }}
          run-id: ${{ steps.pins.outputs.native_run }}
          merge-multiple: true
          github-token: ${{ github.token }}
          path: controlled-engine
      - name: Focused package metadata and source tests before key access
        env:
          INFINITY_CONTROLLED_BASELINE: protected451/Infinity-2103451-Combined-Original-Signer.apk
        run: python3 PREFIX/test_release.py
      - name: Original-key modules exact preservation and verified forward-recovery preparation
        env:
          INFINITY_KEYSTORE_B64: ${{ secrets.INFINITY_KEYSTORE_B64 }}
          INFINITY_STORE_PASSWORD: ${{ secrets.INFINITY_STORE_PASSWORD }}
          INFINITY_KEY_PASSWORD: ${{ secrets.INFINITY_KEY_PASSWORD }}
          INFINITY_KEY_ALIAS: ${{ secrets.INFINITY_KEY_ALIAS }}
        run: |
          python3 PREFIX/release_controlled.py prepare \
            --bundles protected451-components --baseline protected451/Infinity-2103451-Combined-Original-Signer.apk \
            --native controlled-engine --sdk "$ANDROID_HOME/build-tools/35.0.0" --out prepared-controlled
      - uses: actions/upload-artifact@v4
        with: {name: 'Infinity2103456-Prepared-${{ github.run_id }}', path: prepared-controlled/2103456/publish/, if-no-files-found: error, retention-days: 90, compression-level: 0}
      - uses: actions/upload-artifact@v4
        with: {name: 'Infinity2103457-Prepared-${{ github.run_id }}', path: prepared-controlled/2103457/publish/, if-no-files-found: error, retention-days: 90, compression-level: 0}
      - if: always()
        uses: actions/upload-artifact@v4
        with:
          name: Infinity456457-Preparation-Evidence-${{ github.run_id }}
          path: |
            SIGNER-ROUTES.json
            VERSION456.json
            VERSION457.json
            INPUT-METADATA.json
            prepared-controlled/BASELINE-SIGNATURE.txt
            prepared-controlled/RECOVERY-VERIFICATION.json
            prepared-controlled/NATIVE-COMPATIBILITY.json
            prepared-controlled/*/UNSIGNED-SOURCE-GATE.json
            prepared-controlled/*/MODULE-AUTHENTICATION.txt
            prepared-controlled/*/PREPARATION.json
            prepared-controlled/*/preservation/
          if-no-files-found: warn
          retention-days: 90
  review-controlled456-457:
    name: Read-only official controlled artifacts and authority proposals - no keys
    if: github.event_name == 'workflow_dispatch' && github.ref == 'refs/heads/BRANCH' && inputs.operation == 'review-controlled456-457'
    runs-on: ubuntu-22.04
    timeout-minutes: 40
    env:
      PYTHONDONTWRITEBYTECODE: '1'
      GH_TOKEN: ${{ github.token }}
      PREPARED_RUN: ${{ inputs.prepared_run }}
    steps:
      - uses: actions/checkout@v4
        with: {fetch-depth: 0, persist-credentials: false}
      - uses: actions/setup-python@v5
        with: {python-version: '3.12'}
      - uses: actions/download-artifact@v4
        with: {run-id: '${{ inputs.prepared_run }}', name: 'Infinity2103456-Prepared-${{ inputs.prepared_run }}', github-token: '${{ github.token }}', path: reviewed/2103456}
      - uses: actions/download-artifact@v4
        with: {run-id: '${{ inputs.prepared_run }}', name: 'Infinity2103457-Prepared-${{ inputs.prepared_run }}', github-token: '${{ github.token }}', path: reviewed/2103457}
      - name: Verify full official archives and prepare exact authority data without repository writes
        run: |
          python3 - <<'PYCODE'
          import os,sys
          from pathlib import Path
          sys.path.insert(0,'PREFIX')
          import release_controlled as r
          run=int(os.environ['PREPARED_RUN']);out=Path('authority-proposals');out.mkdir()
          a=r.proposed(Path('reviewed/2103456'),run)
          r.save(out/'AUTHORITY456.json',a)
          r.save(r.HERE/'ISSUED456-AUTHORITY.json',a)
          b=r.proposed(Path('reviewed/2103457'),run)
          r.save(out/'AUTHORITY457.json',b)
          r.save(out/'REVIEW.json',dict(status='PASS_FULL_OFFICIAL_PREPARED_ARCHIVES_AND_EXACT_AUTHORITIES',prepared_run=run,source=os.environ['GITHUB_SHA'],APK_signed=False,keys_used=False,accepted_pointer_updated=False))
          PYCODE
      - uses: actions/upload-artifact@v4
        with: {name: 'Infinity456457-Authority-Proposals-${{ github.run_id }}', path: authority-proposals/, if-no-files-found: error, retention-days: 90}
'''.replace('BRANCH',BRANCH).replace('PREFIX',PREFIX)
    s=once(s,'  combined:\n',jobs+'  combined:\n')
    old="|| github.ref == 'refs/heads/work/infinity-kodi-ui-2103454-2103455-packaging-20261104')"
    s=once(s,old,old[:-1]+" || github.ref == 'refs/heads/"+BRANCH+"')")
    marker='          if [ "$GITHUB_REF" = \'refs/heads/work/infinity-kodi-ui-2103454-2103455-packaging-20261104\' ]; then\n'
    first='          if [ "$GITHUB_REF" = \'refs/heads/'+BRANCH+'\' ]; then\n            python3 -m py_compile '+PREFIX+'/release_controlled.py\n          elif'
    assert s.count(marker)==2 # admission and signed comparison; replace admission first
    s=s.replace(marker,first+marker[len('          if'):],1)
    decl="          p453=os.environ['GITHUB_REF']=='refs/heads/work/infinity-kodi-2103453-controlled-test-20261104'"
    # Both the admission and official-artifact import blocks need the exact flag.
    assert s.count(decl)==2
    s=s.replace(decl,"          pctrl=os.environ['GITHUB_REF']=='refs/heads/"+BRANCH+"'\n"+decl)
    marker="          require(a['candidate_versionCode']==version and a['generation']==generation,'EXACT_SELECTED_AUTHORITY')"
    addition="""          if pctrl:
              require(a['candidate_versionCode'] in (2103456,2103457),'EXACT_CONTROLLED_RECOVERY_VERSIONS')
              version=a['candidate_versionCode'];generation=42 if version==2103456 else 43;baseline=2103451
              owner='INFINITY_MASTER_CONTROLLED_TEST' if version==2103456 else 'INFINITY_MASTER_FORWARD_RECOVERY'
              sys_path='PREFIX'
              import sys
              sys.path.insert(0,sys_path)
              import release_controlled as controlled
              require(a['owner_update_evidence']['native_sha256']==(controlled.engine_record()['native_sha256'] if version==2103456 else controlled.FROZEN_NATIVE),'EXACT_CONTROLLED_NATIVE')
              require(a['owner_update_evidence']['Android']==controlled.RUNTIME,'TRUTHFUL_ANDROID_NOT_RUN')
""".replace('PREFIX',PREFIX)
    s=once(s,marker,addition+marker)
    s=once(s,"41783963413 if pui else (41742368066 if p453 else (41568721264 if p0 else 41541654995))","41568721264 if pctrl else (41783963413 if pui else (41742368066 if p453 else (41568721264 if p0 else 41541654995)))")
    s=once(s,"('Infinity'+str(version) if pui else", "('Infinity'+str(version) if pui or pctrl else")
    s=once(s,'      - uses: actions/download-artifact@v4\n        with:\n          run-id: ${{ steps.selected.outputs.baseline_run }}',
        "      - name: Recheck exact controlled or recovery version before issuance\n        if: github.ref == 'refs/heads/"+BRANCH+"'\n        run: python3 "+PREFIX+'/release_controlled.py versions --version "${{ steps.selected.outputs.version }}" --out VERSION-AVAILABILITY.json\n      - uses: actions/download-artifact@v4\n        with:\n          run-id: ${{ steps.selected.outputs.baseline_run }}')
    s=once(s,"sys.path.insert(0,'repairs/infinity-kodi-ui-2103454-2103455-packaging' if pui else", "sys.path.insert(0,'"+PREFIX+"' if pctrl else ('repairs/infinity-kodi-ui-2103454-2103455-packaging' if pui else")
    tail="'repairs/infinity-preview-2103450-fullscreen-display')))\n          if pui: import release_ui as r"
    s=once(s,tail,"'repairs/infinity-preview-2103450-fullscreen-display'))))\n          if pctrl: import release_controlled as r\n          elif pui: import release_ui as r")
    # The later signed comparison has its own shell if, distinct from admission.
    marker='          if [ "$GITHUB_REF" = \'refs/heads/work/infinity-kodi-ui-2103454-2103455-packaging-20261104\' ]; then\n'
    new='''          if [ "$GITHUB_REF" = 'refs/heads/BRANCH' ]; then
            python3 PREFIX/release_controlled.py compare \
              --baseline protected-baseline/Infinity-2103451-Combined-Original-Signer.apk \
              --candidate signed-combined/Infinity-${{ steps.selected.outputs.version }}-Combined-Original-Signer.apk \
              --plan prepared-owner/PREPARATION.json --out signed-combined/preservation --sdk "$ANDROID_HOME/build-tools/35.0.0"
            cp prepared-owner/RECOVERY-VERIFICATION.json prepared-owner/MODULE-AUTHENTICATION.txt prepared-owner/NATIVE-COMPATIBILITY.json signed-combined/
            cp VERSION-AVAILABILITY.json signed-combined/
          elif'''.replace('BRANCH',BRANCH).replace('PREFIX',PREFIX)
    s=once(s,marker,new+marker[len('          if'):])
    return s

if __name__=='__main__':
    original=subprocess.check_output(['git','show',BASE+':'+str(PATH)],cwd=ROOT,text=True)
    target=ROOT/PATH;target.parent.mkdir(parents=True,exist_ok=True);target.write_text(generate(original))
