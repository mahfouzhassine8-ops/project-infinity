"""Exact existing lease algorithm; synthetic invoker liveness. Not Kodi execution."""
from pathlib import Path
import hashlib,json,subprocess,tempfile
HERE=Path(__file__).resolve().parent
src=Path('/tmp/kodi451-restored-native/xbmc/interfaces/generic/ScriptRunner.cpp').read_text()
start=src.index('struct InfinitySearchLeases\n');end=src.index('\nInfinitySearchLeases& InfinitySearchJobs()',start)
body=src[start:end]
assert body.endswith('};')
prefix='''#include <map>
#include <string>
#include <mutex>
#include <cassert>
#include <iostream>
struct CScriptInvocationManager {
 std::map<int,bool> live;
 static CScriptInvocationManager& GetInstance(){static CScriptInvocationManager v;return v;}
 bool IsRunning(int id){return live[id];}
};
'''
main='''
int main(){
 auto& manager=CScriptInvocationManager::GetInstance();
 {InfinitySearchLeases x;assert(x.Reserve("one"));assert(!x.Reserve("one"));std::cout<<"PASS duplicate token refused\\n";}
 {InfinitySearchLeases x;assert(x.Reserve("one"));x.Started("one",-1);assert(x.scripts.empty());std::cout<<"PASS failed start retires reservation\\n";}
 {InfinitySearchLeases x;for(int id=1;id<=3;++id){manager.live[id]=true;assert(x.Reserve(std::to_string(id)));x.Started(std::to_string(id),id);}assert(!x.Reserve("four"));std::cout<<"PASS three live distinct invokers block fourth lease\\n";}
 {InfinitySearchLeases x;manager.live[7]=true;for(int n=1;n<=3;++n){assert(x.Reserve(std::to_string(n)));x.Started(std::to_string(n),7);}assert(x.scripts.size()==3);assert(!x.Reserve("four"));std::cout<<"PASS conditional same-live-invoker accounting counts three tokens\\n";}
 {InfinitySearchLeases x;manager.live[8]=true;assert(x.Reserve("done-result"));x.Started("done-result",8);assert(x.Reserve("next"));assert(x.scripts.count("done-result")==1);std::cout<<"PASS no liveness retirement inferred from subsequent admission\\n";}
 {InfinitySearchLeases x;manager.live[9]=true;for(int n=1;n<=3;++n){assert(x.Reserve(std::to_string(n)));x.Started(std::to_string(n),9);}manager.live[9]=false;assert(x.Reserve("fresh"));assert(x.scripts.size()==1);std::cout<<"PASS observed invoker completion retires old leases\\n";}
}
'''
(HERE/'EXTRACTED-LEASE-SOURCE.cpp.txt').write_text(prefix+body+main)
with tempfile.TemporaryDirectory(prefix='infinity-lease-accounting-') as tmp:
 p=Path(tmp);(p/'proof.cpp').write_text(prefix+body+main)
 compile_result=subprocess.run(['c++','-std=c++17','-pthread',str(p/'proof.cpp'),'-o',str(p/'proof')],capture_output=True,text=True)
 (HERE/'LEASE-COMPILE.txt').write_text(compile_result.stdout+compile_result.stderr)
 compile_result.check_returncode()
 run=subprocess.run([str(p/'proof')],capture_output=True,text=True,timeout=10)
 (HERE/'LEASE-RESULT.txt').write_text(run.stdout+run.stderr);run.check_returncode()
(HERE/'LEASE-BINDING.json').write_text(json.dumps({'source':'xbmc/interfaces/generic/ScriptRunner.cpp','source_sha256':hashlib.sha256(src.encode()).hexdigest(),'extracted_struct_sha256':hashlib.sha256(body.encode()).hexdigest(),'extraction':'Exact source substring, no algorithm modifications','liveness':'synthetic manager, not actual native invokers','cases':6,'result':'PASS_ALGORITHM_CASES_ONLY','Android':'NOT_RUN','Search_provider_execution':'NOT_RUN','crash_reproduction':'NOT_RUN','production_edits':False},indent=2)+'\n')
print(run.stdout)
