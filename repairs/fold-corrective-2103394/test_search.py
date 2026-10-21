import ast,base64,hashlib,io,json,os,subprocess,tempfile,types,unittest,zipfile
from pathlib import Path
from urllib.parse import urlencode,parse_qs,urlsplit
from unittest.mock import patch
import search_native94

HERE=Path(__file__).resolve().parent

def source_functions():
 ns={'ast':ast,'hashlib':hashlib,'Path':Path,'urlencode':urlencode,'xbmc':types.SimpleNamespace(getCondVisibility=lambda _:True)}
 t=ast.parse((HERE/'infinity_search.py').read_text())
 nodes=[n for n in t.body if isinstance(n,ast.FunctionDef) and n.name in ('_read','_branch','_getter','_forwarded','recipe','route')]
 exec(compile(ast.Module(body=nodes,type_ignores=[]),'actual_search.py','exec'),ns)
 return ns

class Search(unittest.TestCase):
 def test_actual_official_router_receivers_and_history_no_provider_execution(self):
  raw=base64.b64decode((HERE/'PROVIDER-SEARCH-SOURCE.b64').read_bytes())
  self.assertEqual(hashlib.sha256(raw).hexdigest(),'d0589dcd98adaeee679f71a70255c17e239614c119b4eb8296372206db4a99d4')
  ns=source_functions()
  with tempfile.TemporaryDirectory() as d:
   root=Path(d)
   with zipfile.ZipFile(io.BytesIO(raw)) as z:z.extractall(root)
   for aid in ('umbrella','seren','pov'):
    for media in ('movie','tv'):
     contract=ns['recipe'](root/aid,media);self.assertIsNotNone(contract,(aid,media))
     p=dict(id='plugin.video.'+aid,root=str(root/aid),contract=contract)
     query='A real query & exact spaces'
     route=ns['route'](p,query);q=parse_qs(urlsplit(route).query)
     self.assertEqual(q[contract['query_key']],[query]);self.assertEqual(urlsplit(route).netloc,p['id'])
     history=parse_qs(urlsplit(ns['route'](p,history=True)).query)
     self.assertNotIn(contract['query_key'],history)
     if aid=='pov':self.assertEqual(history['action'],['movie' if media=='movie' else 'tvshow'])
     changed=root/aid/next(iter(contract['pins']));body=changed.read_bytes();changed.write_bytes(body+b'\n')
     with self.assertRaises(RuntimeError):ns['route'](p,query)
     changed.write_bytes(body)
   self.assertIsNone(ns['recipe'](root/'unsupported','movie'))
 def test_changed_or_disabled_source_is_not_silently_remapped(self):
  ns=source_functions();p={'id':'plugin.video.pov','root':'/unused','contract':{'pins':{},'params':{'mode':'test'},'query_key':'query'}}
  ns['xbmc'].getCondVisibility=lambda _:False
  with self.assertRaises(RuntimeError):ns['route'](p,'query')
 def test_exact_native_search_guards_and_no_stop_or_receipts(self):
  root=Path(os.environ['INFINITY_2103393_NATIVE'])
  paths=(search_native94.RUNNER,search_native94.HEADER,search_native94.PLUGIN)
  before={p:(root/p).read_bytes() for p in paths};after=search_native94.patches(before)
  runner=after[search_native94.RUNNER]
  for value in (b'InfinityAndroidCheckpoint::IsActive()',b'InfinitySearchOwnerVerified()',b'GetProtocolOptions()',b'infinityProviderPath = path.substr(0, separator)',b'scripts.size() >= 3'):
   self.assertIn(value,runner)
  self.assertEqual(runner.count(b'if (shutdownResultCancelled())'),4)
  self.assertNotIn('Stop(',search_native94.EXPIRY);self.assertNotIn('receipt',search_native94.EXPIRY.lower())
 def test_live_invocation_limit_keeps_timed_out_jobs_until_real_completion(self):
  source=search_native94.HELPERS
  start=source.index('struct InfinitySearchLeases');end=source.index('InfinitySearchLeases&',start)
  shim=r'''
#include <map>
#include <string>
#include <mutex>
#include <set>
#include <vector>
#include <thread>
#include <cassert>
struct CScriptInvocationManager {
 std::mutex mutex;std::set<int> live;
 static CScriptInvocationManager& GetInstance(){static CScriptInvocationManager v;return v;}
 bool IsRunning(int id){std::lock_guard<std::mutex> lock(mutex);return live.count(id);}
};
'''
  cases=r'''
int main(){InfinitySearchLeases jobs;
 auto& scripts=CScriptInvocationManager::GetInstance();scripts.live={1,2,3};
 for(int i=1;i<=3;++i){assert(jobs.Reserve(std::to_string(i)));jobs.Started(std::to_string(i),i);}
 assert(!jobs.Reserve("timeout-still-running"));
 scripts.live.erase(2);assert(jobs.Reserve("new"));jobs.Started("new",-1);
 std::vector<std::thread> peers;
 for(int i=0;i<30;++i)peers.emplace_back([&jobs,i](){jobs.Reserve("peer"+std::to_string(i));});
 for(auto& peer:peers)peer.join();assert(jobs.scripts.size()==3);
 assert(jobs.scripts.at("1")==1&&jobs.scripts.at("3")==3);
}
'''
  with tempfile.TemporaryDirectory() as d:
   p=Path(d);(p/'test.cpp').write_text(shim+source[start:end]+cases)
   subprocess.run(['g++','-std=c++17','-Wall','-Wextra','-Werror','-Wno-misleading-indentation','-pthread',str(p/'test.cpp'),'-o',str(p/'test')],check=True)
   subprocess.run([str(p/'test')],check=True,timeout=5)

if __name__=='__main__':unittest.main()
