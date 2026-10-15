#!/usr/bin/env python3
"""Run the existing Java wire/lease suite with the essential-first validator.

Native SAFE input is emitted by the compiled production coordinator harness.
Android peer APIs remain host adapters; this does not prove Android process death.
"""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import tempfile

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]

def once(text, old, new):
    assert text.count(old) == 1, old[:100]
    return text.replace(old, new, 1)

def main():
    p = argparse.ArgumentParser()
    p.add_argument('--android-jar', type=Path, required=True)
    p.add_argument('--native-receipt', type=Path, required=True)
    p.add_argument('--out', type=Path, required=True)
    args = p.parse_args()
    source = (ROOT/'repairs/android-checkpoint-shutdown/test_android_runtime.py').read_text()
    source = once(source, "names += ['InfinityCheckpointEvidence', 'InfinityInstalledCodeEvidence']",
                         "names += ['InfinityCheckpointEvidence', 'InfinityInstalledCodeEvidence', 'InfinityTaskLifecycleGate']")
    source = once(source, '  row.put("required_owners",names);row.put("owners",owners);', '''  row.put("required_owners",names);row.put("owners",owners);
  row.put("exit_policy","essential_first_process_exit_v1");
  row.put("essential_write_generation",7).put("essential_writes_sealed",true).put("essential_writes_durable",true);
  row.put("essential_write_blockers",new JSONArray()).put("process_death_confirmed",false);
  JSONArray essential=new JSONArray();
  for(int i=0;i<owners.length();i++){
   JSONObject value=owners.getJSONObject(i);boolean required=!"python_services".equals(value.getString("owner"));
   value.put("essential",required);if(required)essential.put(value.getString("owner"));
  }
  row.put("essential_owners",essential);''')
    source = once(source, '  gates();', '''  row=valid();row.getJSONArray("owners").getJSONObject(1).put("required_writes_finished",false)
    .put("dirty",true).put("dirty_remaining",true).put("result","PENDING");
  check(accepted(row),"unfinished optional retirement vetoed essential authorization");
  row.getJSONArray("owners").getJSONObject(1).put("result","FAILED");
  check(accepted(row),"optional failure vetoed independent essential authorization");
  row.getJSONArray("owners").getJSONObject(1).put("result","COMMITTED");
  check(!accepted(row),"fabricated optional save accepted");
  row=valid();row.getJSONArray("essential_owners").put("python_services");check(!accepted(row),"different essential registry accepted");
  row=valid();row.put("essential_writes_durable",false);check(!accepted(row),"undurable protected writes accepted");
  row=valid();row.put("essential_writes_sealed",false);check(!accepted(row),"unsealed protected writes accepted");
  row=valid();row.put("essential_write_generation",6);check(!accepted(row),"stale protected-write proof accepted");
  row=valid();row.getJSONArray("essential_write_blockers").put("pending_shared_transaction");check(!accepted(row),"protected transaction blocker ignored");
  row=valid();row.put("process_death_confirmed",true);check(!accepted(row),"native save receipt claimed process death");
  System.out.println("PASS 9 essential-first authorization and truthful optional receipt checks");
  gates();''')
    with tempfile.TemporaryDirectory(prefix='essential-java-') as temporary:
        work = Path(temporary)
        base = ROOT/'repairs/android-checkpoint-shutdown/runtime/android/overlay'
        shutil.copytree(base, work/'runtime')
        gate = ROOT/'repairs/shutdown-recents-2103377/lifecycle/InfinityTaskLifecycleGate.java.in'
        shutil.copyfile(gate, work/'runtime/tools/android/packaging/xbmc/src'/gate.name)
        # This unchanged peer predates the overlay. Reconstruct its published
        # source and require the original Android manifest's exact postimage.
        name = 'tools/android/packaging/xbmc/src/InfinityCloseProgress.java.in'
        patch = (ROOT/'repairs/live-closing-2103329/android.patch').read_text()
        section = patch.split('+++ b/'+name+'\n',1)[1].split('\n--- ',1)[0]
        progress = '\n'.join(line[1:] for line in section.splitlines() if line.startswith('+'))+'\n'
        progress = progress.replace('infinity-shutdown-2103327-v1','infinity-shutdown-2103334-v1')
        progress = progress.replace('session<0?status:"Finishing shutdown"','session<0?status:"Waiting for the next shutdown stage"')
        progress = progress.replace('name.equals("stop.cancel_jobs")||name.equals("pre.begin_job_shutdown")',
            'name.equals("stop.cancel_jobs")||name.equals("pre.begin_job_shutdown")||name.startsWith("directory.")')
        manifest = json.loads((base.parent/'manifest.json').read_text())
        assert hashlib.sha256(progress.encode()).hexdigest() == manifest['after'][name]
        (work/'runtime'/name).write_text(progress)
        shutil.copytree(HERE/'runtime/android', work/'runtime', dirs_exist_ok=True)
        script = work/'test.py'; script.write_text(source)
        result = subprocess.run(['python3', str(script), '--source', str(work/'runtime'),
            '--android-jar', str(args.android_jar), '--native-receipt', str(args.native_receipt)],
            capture_output=True, text=True, timeout=120)
        report = {'scope':'actual Android shutdown classes compiled; wire and UUID lease tests on host',
                  'exit_code':result.returncode,'stdout':result.stdout,'stderr':result.stderr,
                  'passed':result.returncode==0,'android_process_death_verified':False,'apk_deliverable':False}
        args.out.write_text(json.dumps(report,indent=2)+'\n')
        print(result.stdout);print(result.stderr)
        if result.returncode: raise SystemExit(result.returncode)

if __name__ == '__main__': main()
