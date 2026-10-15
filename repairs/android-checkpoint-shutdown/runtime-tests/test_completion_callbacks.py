#!/usr/bin/env python3
"""Execute actual two completion paths with controlled database results."""
import argparse,subprocess,tempfile
from pathlib import Path
from test_job_checkpoint import function
PEERS=r'''
#include <cassert>
#include <memory>
#include <string>
#include <stdexcept>
#include <mutex>
#include <set>
#include <functional>
using CCriticalSection=std::recursive_mutex;
struct CDateTime{static int GetCurrentDateTime(){return 1;}};
struct CJob{enum {PRIORITY_LOW};};
struct Job{std::string owner,operation;std::function<void()> work;};
template<class F>struct CLambdaJob:Job{CLambdaJob(const char*o,const char*p,F&&f){owner=o;operation=p;work=std::move(f);}};
struct Manager{std::unique_ptr<Job>job;void AddJob(Job*j,void*,int){job.reset(j);}};static Manager manager;
struct CServiceBroker{static Manager*GetJobManager(){return &manager;}};
struct DB{bool ok=true;bool SetLastUsed(const std::string&,int){return ok;}};
struct Info{int updates=0;void SetLastUsed(int){++updates;}};
namespace AddonType{constexpr int UNKNOWN=0;}
namespace AddonEvents{struct MetadataChanged{explicit MetadataChanged(const std::string&){}};}
struct Events{int published=0;void Publish(AddonEvents::MetadataChanged){++published;}};
class CAddonMgr{public:CCriticalSection m_critSection;std::shared_ptr<DB>m_database=std::make_shared<DB>();std::shared_ptr<Info>info=std::make_shared<Info>();Events m_events;auto GetAddonInfo(const std::string&,int){return info;}void UpdateLastUsed(const std::string&);};
struct Details{bool hashRevalidated=false,updateable=true;};
struct CTextureCacheJob{std::string m_url="fixture";Details m_details;bool receipt=false;void SetCheckpointCompletionReceipt(bool ok){receipt=ok;}};
struct Event{int calls=0;void Set(){++calls;}};
class CTextureCache{public:bool ok=true;int adds=0,validates=0;CCriticalSection m_processingSection;std::set<std::string>m_processinglist;Event m_completeEvent;
bool SetCachedTextureValid(const std::string&,bool){++validates;return ok;}bool AddCachedTexture(const std::string&,Details){++adds;return ok;}void OnCachingComplete(bool,CTextureCacheJob*);};
'''
TEST=r'''
int main(){CAddonMgr addons;addons.UpdateLastUsed("plugin.video.thecrew");assert(manager.job->owner=="native_databases"&&manager.job->operation=="addon-last-used");manager.job->work();assert(addons.info->updates==1&&addons.m_events.published==1);
addons.m_database->ok=false;addons.UpdateLastUsed("plugin.video.thecrew");bool failed=false;try{manager.job->work();}catch(const std::runtime_error&){failed=true;}assert(failed&&addons.info->updates==1&&addons.m_events.published==1);
for(bool revalidate:{false,true})for(bool dbOk:{false,true}){CTextureCache cache;cache.ok=dbOk;CTextureCacheJob job;job.m_details.hashRevalidated=revalidate;cache.m_processinglist.insert(job.m_url);cache.OnCachingComplete(true,&job);assert(job.receipt==dbOk);assert(cache.validates==int(revalidate)&&cache.adds==int(!revalidate));assert(cache.m_processinglist.empty()&&cache.m_completeEvent.calls==1);}
CTextureCache cache;cache.ok=false;CTextureCacheJob job;cache.OnCachingComplete(false,&job);assert(job.receipt&&cache.adds==0&&cache.validates==0);
}
'''
def main():
 p=argparse.ArgumentParser();p.add_argument('--runtime',type=Path,required=True);a=p.parse_args();r=a.runtime/'xbmc'
 code=PEERS+function((r/'addons/AddonManager.cpp').read_text(),'void CAddonMgr::UpdateLastUsed(')+function((r/'TextureCache.cpp').read_text(),'void CTextureCache::OnCachingComplete(')+TEST
 with tempfile.TemporaryDirectory(prefix='actual-completion-') as t:
  t=Path(t);(t/'test.cpp').write_text(code);subprocess.run(['g++','-std=c++17','-Wall','-Wextra','-Werror',str(t/'test.cpp'),'-o',str(t/'test')],check=True);subprocess.run([str(t/'test')],check=True)
 print('PASS: actual Last Used and Texture Cache callbacks; SQL failure never produces success or false metadata events')
if __name__=='__main__':main()
