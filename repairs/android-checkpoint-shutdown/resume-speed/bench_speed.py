"""Host workload comparison; these timings do not measure Fold startup/frames."""
import argparse,json,runpy,sys,time
from pathlib import Path
from unittest import mock
p=argparse.ArgumentParser();p.add_argument('--runtime',required=True);a=p.parse_args()
sys.argv=[sys.argv[0],'--runtime',a.runtime]
f=runpy.run_path(str(Path(__file__).parents[1]/'runtime-tests/test_runtime_checkpoint.py'),run_name='bench_fixtures')
t=f['RuntimeTests']();t.setUp()
try:
 hub=f['hub'];data=hub.load(t.profile)
 for bucket,count in [('items',100),('watched',600),('collection',1000)]:
  data[bucket]={format(i+1,'064x'):dict(key=format(i+1,'064x'),media='movie',title='Title '+str(i),updated=i,position=417.125,duration=900,poster='poster') for i in range(count)}
 hub.save(t.profile,data)
 fn=getattr(hub,'poll_kodi_sync',hub.flush_kodi_sync)
 with mock.patch.object(hub,'load',wraps=hub.load) as reads:
  start=time.perf_counter()
  for _ in range(100):assert fn(t.profile)
  elapsed=time.perf_counter()-start
  print(json.dumps(dict(variant='candidate' if hasattr(hub,'poll_kodi_sync') else 'green2103362',iterations=100,verified_history_reads=reads.call_count,host_idle_poll_ms=round(elapsed*1000,3),items=100,watched=600,collection=1000,fold_measured=False)))
finally:t.tearDown()
