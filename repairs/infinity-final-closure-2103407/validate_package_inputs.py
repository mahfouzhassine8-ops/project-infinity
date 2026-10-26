"""Exact successful native/module producers for one authorized internal APK."""
import json
import os
from pathlib import Path
import subprocess
import urllib.request

ROOT=Path(__file__).parent


def api(path):
    request=urllib.request.Request('https://api.github.com/repos/mahfouzhassine8-ops/project-infinity/'+path,
        headers={'Authorization':'Bearer '+os.environ['GITHUB_TOKEN'],'Accept':'application/vnd.github+json',
                 'X-GitHub-Api-Version':'2022-11-28'})
    with urllib.request.urlopen(request,timeout=60) as r:return json.load(r)


def main():
    scope=json.loads((ROOT/'SCOPE.json').read_text());plan=json.loads((ROOT/'APK-PACKAGING-PLAN.json').read_text())
    if (scope['candidate']['version_code']!=2103409 or plan['candidate_versionCode']!=2103409 or
        not plan['internal_APK_not_final'] or scope['release_ready']):raise ValueError('Exact unaccepted candidate scope required')
    subprocess.run(['git','merge-base','--is-ancestor',plan['source_inputs']['module_source'],'HEAD'],check=True)
    records=[]
    for run,source,artifact,wanted in [
        (plan['source_inputs']['native_run'],plan['source_inputs']['native_source'],plan['source_inputs']['native_artifact_id'],plan['source_inputs']['native_artifact_sha256']),
        (plan['source_inputs']['module_run'],plan['source_inputs']['module_source'],plan['source_inputs']['module_artifact_id'],plan['source_inputs']['module_artifact_sha256'])]:
        job=api('actions/runs/'+str(run));item=api('actions/artifacts/'+str(artifact))
        if (job['conclusion']!='success' or job['head_sha']!=source or item['expired'] or
            item['digest']!='sha256:'+wanted or item['workflow_run']['id']!=run):
            raise ValueError('Matching successful build/artifact identity differs')
        records.append(dict(run=run,source=source,artifact_id=artifact,artifact_sha256=wanted,status='SUCCESS'))
    Path('internal-package-inputs.json').write_text(json.dumps(dict(inputs=records,physical_Fold='NOT RUN',
        release_ready=False,shutdown_test='NOT SELECTED; independent',purpose='InternalAPKforseparatelyselectedAPI37verification'),indent=2)+'\n')


if __name__=='__main__':main()
