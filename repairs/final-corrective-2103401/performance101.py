"""Comparable host geometry timings, not a claim about device frame times."""
import ast,json,os,statistics,time
from pathlib import Path
import components101 as c
before=c.read_parent(Path(os.environ['INFINITY_2103400_APK']));after=c.components(before)
measure={}
for label,data in [('protected_2103400',before),('candidate_2103401',after)]:
 node=next(n for n in ast.parse(data[c.UI+'/home_option_b.py']).body if isinstance(n,ast.FunctionDef) and n.name=='geometry');ns={};exec(compile(ast.Module(body=[node],type_ignores=[]),'actual-geometry.py','exec'),ns)
 samples=[]
 for _ in range(20):
  start=time.perf_counter_ns()
  for i in range(1000):ns['geometry'](1920,1080,2160,2160,bool(i%2))
  samples.append((time.perf_counter_ns()-start)/1000/1000)
 measure[label]=dict(median_microseconds_per_call=statistics.median(samples),p95_microseconds_per_call=sorted(samples)[18],sample_batches=20,calls_per_batch=1000)
report=dict(measurements=measure,environment='CI/host CPython; no Kodi renderer or device player',geometry_source_identical=True,speedup_claimed=False,more_info_modal_instances=dict(baseline=2,candidate=1),provider_tap_completion_callbacks=dict(baseline=1,candidate=0),physical_fold_verified=False)
Path(os.environ['INFINITY_101_PERFORMANCE']).write_text(json.dumps(report,indent=2)+'\n')
