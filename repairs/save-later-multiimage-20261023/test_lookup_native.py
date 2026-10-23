"""Compile the actual patched lease admission, expiration and owner-slot code."""
from pathlib import Path
import subprocess
import tempfile

SHIM = r'''
#define TARGET_ANDROID 1
#include <cassert>
#include <chrono>
#include <map>
#include <mutex>
#include <set>
#include <string>
#include <thread>
#include <vector>
static bool guiThread=false, checkpoint=false, stopping=false, owner=true;
static std::string skin="skin.infinity.diggz";
static std::map<std::string,std::string> properties;
struct Messenger { bool IsProcessThread(){return guiThread;} };
struct CServiceBroker { static Messenger* GetAppMessenger(){static Messenger m;return &m;} };
namespace XBMCAddon { namespace xbmc { std::string getSkinDir(){return skin;} } }
namespace InfinityAndroidCheckpoint { bool IsActive(){return checkpoint;} }
bool InfinitySearchOwnerVerified(){return owner;}
std::string InfinitySearchProperty(const std::string& key,const char* value=nullptr){
 if(value)properties[key]=value;
 return properties[key];
}
struct CScriptInvocationManager {
 std::set<int> live;
 static CScriptInvocationManager& GetInstance(){static CScriptInvocationManager v;return v;}
 bool IsShutdownRequested(){return stopping;}
 bool IsRunning(int id){return live.count(id);}
};
struct Addon { std::string id="plugin.video.current";const std::string& ID(){return id;} };
struct CURL {
 std::string value;explicit CURL(std::string v):value(v){}
 std::string GetProtocolOptions(){auto p=value.find('|');return p==std::string::npos?"":value.substr(p+1);}
 std::string GetProtocolOption(const std::string& key){
  auto options=GetProtocolOptions(), prefix=key+"=";
  if(options.compare(0,prefix.size(),prefix)!=0)return "";
  auto token=options.substr(prefix.size());return token.substr(0,token.find('&'));
 }
 std::string GetProtocol(){return value.substr(0,value.find(':'));}
 std::string GetHostName(){auto p=value.find("://");return value.substr(p+3,value.find('/',p+3)-p-3);}
};
namespace KODI { namespace UTILITY { struct CDigest {
 enum class Type{SHA256};
 static std::string Calculate(Type,const std::string& path){return "digest:"+path;}
};} }
'''

CLASS = r'''
class CScriptRunner {
public:
 bool m_infinitySearch=false;
 std::string m_infinitySearchToken;
 std::chrono::steady_clock::time_point m_infinitySearchDeadline;
 bool InfinitySearchExpired();
 bool Prepare(Addon* addon,const std::string& path){
'''

CASES = r'''
void reset(){
 properties.clear();InfinitySearchJobs().scripts.clear();
 CScriptInvocationManager::GetInstance().live.clear();
 guiThread=checkpoint=stopping=false;owner=true;skin="skin.infinity.diggz";
}
std::string request(const std::string& token,bool saved=true,
                    const std::string& path="plugin://plugin.video.current/?mode=list"){
 properties["Infinity.Search.Request."+token]="digest:"+path;
 if(saved)properties["Infinity.SavedNavigation.Lookup."+token]="digest:"+path;
 return path+"|infinity_search="+token;
}
void allowance(CScriptRunner& r,int seconds){
 auto left=std::chrono::duration_cast<std::chrono::milliseconds>(
  r.m_infinitySearchDeadline-std::chrono::steady_clock::now()).count();
 assert(left>seconds*1000-1000&&left<=seconds*1000);
}
int main(){
 Addon addon;const std::string token(32,'a');CScriptRunner r;
 reset();assert(r.Prepare(&addon,"plugin://plugin.video.current/?mode=list"));assert(!r.m_infinitySearch);
 reset();assert(r.Prepare(&addon,request(token,false)));allowance(r,20);
 reset();assert(r.Prepare(&addon,request(token)));allowance(r,60);
 assert(properties["Infinity.SavedNavigation.Lookup."+token].empty());
 assert(properties["Infinity.Search.Request."+token].empty());
 assert(!r.InfinitySearchExpired());
 // No title, provider name or ordinary Search request implicitly gets more time.
 reset();auto path=request(token);properties["Infinity.SavedNavigation.Lookup."+token]="wrong";
 assert(r.Prepare(&addon,path));allowance(r,20);
 reset();Addon probe;probe.id="script.infinity.commandcenter";
 assert(r.Prepare(&probe,request(token,false,"plugin://script.infinity.commandcenter/?action=search-probe")));
 assert(!r.m_infinitySearch&&InfinitySearchJobs().scripts.empty());
 assert(properties["Infinity.Search.Protocol"]=="1");
 assert(properties["Infinity.SavedNavigation.Lookup.Protocol"]=="1");
 // Existing guards precede reservation and the added allowance.
 for(int guard=0;guard<9;++guard){
  reset();path=request(token);
  if(guard==0)guiThread=true;
  if(guard==1)skin="skin.cobra";
  if(guard==2)checkpoint=true;
  if(guard==3)stopping=true;
  if(guard==4)owner=false;
  if(guard==5)properties["Infinity.Search.Request."+token]="wrong";
  if(guard==6)path+="&unsupported=1";
  if(guard==7)path=request("short");
  if(guard==8)path=request(token,true,"plugin://plugin.video.other/?mode=list");
  assert(!r.Prepare(&addon,path));assert(!r.m_infinitySearch);assert(InfinitySearchJobs().scripts.empty());
 }
 reset();std::vector<CScriptRunner> jobs(4);auto& manager=CScriptInvocationManager::GetInstance();
 for(int i=0;i<3;++i){
  auto key=std::string(32,char('a'+i));assert(jobs[i].Prepare(&addon,request(key,i!=1)));
  InfinitySearchJobs().Started(key,i);manager.live.insert(i);
 }
 assert(!jobs[3].Prepare(&addon,request(std::string(32,'d'))));
 // Consumer timeout is failure, never a slot release or script retirement.
 jobs[0].m_infinitySearchDeadline=std::chrono::steady_clock::now()-std::chrono::seconds(1);
 assert(jobs[0].InfinitySearchExpired());assert(properties["Infinity.Search.Result."+token]=="timeout");
 assert(InfinitySearchJobs().scripts.size()==3&&manager.live.size()==3);
 assert(!jobs[3].Prepare(&addon,request(std::string(32,'d'))));
 // User cancellation has priority even before the 60-second deadline.
 properties["Infinity.Search.Cancel."+std::string(32,'c')]="1";
 assert(jobs[2].InfinitySearchExpired());
 assert(properties["Infinity.Search.Result."+std::string(32,'c')]=="cancelled");
 assert(InfinitySearchJobs().scripts.size()==3&&manager.live.size()==3);
 manager.live.erase(0);
 assert(jobs[3].Prepare(&addon,request(std::string(32,'d'))));
 assert(InfinitySearchJobs().scripts.size()==3);
 // Concurrent callers still share the same original capacity bound.
 std::vector<std::thread> peers;
 for(int i=0;i<30;++i)peers.emplace_back([i](){assert(!InfinitySearchJobs().Reserve("peer"+std::to_string(i)));});
 for(auto& peer:peers)peer.join();
 assert(InfinitySearchJobs().scripts.size()==3);
}
'''


def run(path):
    source = path.read_text()
    start = source.index('struct InfinitySearchLeases')
    end = source.index('std::string InfinitySearchProperty(', start)
    leases = source[start:end]
    start = source.index('#if defined(TARGET_ANDROID)\n  // INFINITY_2103394_BOUNDED_SEARCH:')
    end = source.index('  int scriptId = ExecuteScript(', start)
    prepare = source[start:end]
    start = source.index('bool CScriptRunner::InfinitySearchExpired()')
    expiry = source[start:source.index('\n#endif', start)]
    with tempfile.TemporaryDirectory(prefix='saved-lookup-native-') as directory:
        work = Path(directory)
        (work/'test.cpp').write_text(SHIM + leases + CLASS + prepare +
            '\nreturn true;\n}\n};\n' + expiry + CASES)
        subprocess.run(['g++', '-std=c++17', '-Wall', '-Wextra', '-Werror', '-pthread',
                        str(work/'test.cpp'), '-o', str(work/'test')], check=True)
        subprocess.run([str(work/'test')], check=True, timeout=10)
    return dict(passed=True, actual_patched_native_code=True,
                ordinary_search_seconds=20, saved_lookup_seconds=60,
                admission_negative_controls=9, invocation_capacity=3,
                timeout_does_not_retire_owner=True, cancellation_does_not_retire_owner=True)
