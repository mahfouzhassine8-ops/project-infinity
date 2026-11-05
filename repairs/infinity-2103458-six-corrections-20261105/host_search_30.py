"""Real Search worker/admission code with synthetic RPC; NOT Android stress."""
import ast,hashlib,json,os,sys,threading,time
from pathlib import Path
R=Path(__file__).resolve().parents[2]
S=R/'repairs/infinity-master-corrective-20261105/overlay/assets/addons/script.infinity.commandcenter/infinity_search.py'
os.environ['FINAL_SIGNED_SEARCH']=str(S);os.environ['FINAL_PATCHED_SEARCH']=str(S)
sys.path.insert(0,str(R/'repairs/infinity-final-closure-2103407'))
from test_search_lifetime import load,Home,RPC,PATH
fds=len(os.listdir('/proc/self/fd'));threads=threading.active_count();records=[]
for i in range(30):
 rpc=RPC(error=i%7==6);rpc.release.set();home=Home();scope=load(S,rpc)
 status,answer=scope['_leased_directory'](PATH+'&fixture='+str(i),home)
 assert rpc.count==1 and rpc.inflight==0 and rpc.peak==1
 assert not home.props and len(home.clear_attempts)==3
 assert threading.active_count()==threads and len(os.listdir('/proc/self/fd'))==fds
 assert ('error' in answer)==(i%7==6)
 records.append({'iteration':i+1,'rpc_calls':rpc.count,'peak_rpc':rpc.peak,'tokens_remaining':len(home.props),'threads_after':threading.active_count(),'fds_after':len(os.listdir('/proc/self/fd')),'synthetic_rpc_error':i%7==6})
print(json.dumps({'status':'PASS_30_HOST_WORKER_LIFETIME_ONLY','source_sha256':hashlib.sha256(S.read_bytes()).hexdigest(),'records':records,'native_RPC':'MOCKED','actual_provider_searches':0,'Android':'NOT_RUN','reported_native_crash_reproduced':False,'native_memory_pressure':'NOT_MEASURED'},indent=2))
