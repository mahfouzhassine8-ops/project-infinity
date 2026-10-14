"""Host filesystem stress. Does not measure Kodi, Android RAM or GPU frames."""
import gc,json,statistics,sys,tempfile,time,tracemalloc
from pathlib import Path
HERE=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(HERE/'addons/script.infinity.rails/resources'))
from lib.store import Store
from lib.menu import geometry

def run():
 timings=[];tracemalloc.start()
 with tempfile.TemporaryDirectory() as tmp:
  s=Store(tmp)
  for i in range(500):
   aid='plugin.video.fixture'+str(i%20);start=time.perf_counter()
   s.add(aid,['movies'],{});s.move('movies','c:'+aid,None,[]);s.remove('movies',aid);geometry(1080,2400,5)
   timings.append((time.perf_counter()-start)*1000)
   if i==249:
    gc.collect();memory_mid=tracemalloc.get_traced_memory()[0]
  gc.collect();memory_end,peak=tracemalloc.get_traced_memory()
  data,w=s.load();assert not w;assert not data['rails']['movies']['custom']
 report={'scope':'500 host filesystem add/move/remove cycles and geometry computations; not Kodi frame pacing','cycles':len(timings),'cycle_ms_p50':statistics.median(timings),'cycle_ms_p95':sorted(timings)[int(.95*len(timings))-1],'cycle_ms_max':max(timings),'python_traced_bytes_mid':memory_mid,'python_traced_bytes_end':memory_end,'python_traced_peak_bytes':peak,'allocation_scope':'includes retained benchmark timing samples and bookkeeping; not a Kodi leak test','device_fps_measured':False,'native_menu_open_latency_measured':False,'frame_pacing_measured':False,'android_shutdown_measured':False}
 (HERE/'evidence/host-performance.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
if __name__=='__main__':run()
