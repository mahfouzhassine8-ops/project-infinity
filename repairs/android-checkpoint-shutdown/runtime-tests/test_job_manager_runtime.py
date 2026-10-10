#!/usr/bin/env python3
"""Compile complete production JobManager.cpp; deterministic thread/event peers."""
from pathlib import Path
import argparse
import shutil
import subprocess
import tempfile

STUBS={
 'threads/CriticalSection.h':'#pragma once\n#include <mutex>\nusing CCriticalSection=std::recursive_mutex;\n',
 'threads/Thread.h':r'''#pragma once
#include <chrono>
#include <thread>
class CEvent {public:void Set(){}template<class T>bool Wait(T){return false;}};
enum class ThreadPriority {LOWEST};
class CThread {public:explicit CThread(const char*){}virtual~CThread()=default;void Create(bool){}bool IsAutoDelete()const{return true;}void StopThread(){}void SetPriority(ThreadPriority){}virtual void Process(){}};
''',
 'ServiceBroker.h':'#pragma once\nclass CJobManager;class CServiceBroker{public:static CJobManager*GetJobManager();};\n',
 'utils/XTimeUtils.h':'#pragma once\n',
 'utils/log.h':'#pragma once\nconstexpr int LOGERROR=1;class CLog{public:template<class...T>static void Log(T...) {}};\n',
 'platform/android/activity/InfinityShutdownTrace.h':'#pragma once\nnamespace InfinityShutdownTrace{struct Scope{template<class...T>Scope(T...) {}};template<class...T>void Event(T...) {}}\n',
 'platform/android/activity/InfinityAndroidCheckpoint.h':r'''#pragma once
#include <string>
namespace InfinityAndroidCheckpoint {
inline bool active=false;inline int failures=0,leases=0;
inline bool IsActive(){return active;}inline bool IsPersistingOnThisThread(){return false;}
inline bool IsAcceptedPlaybackWorkOnThisThread(){return false;}
inline bool IsRequiredOwner(const std::string&s){return s=="playback"||s=="native_databases";}
inline void RecordFailure(const char*,const char*){++failures;}
class CheckpointWriteGuard{bool admitted;public:explicit CheckpointWriteGuard(const char*):admitted(!active){if(admitted)++leases;}~CheckpointWriteGuard(){if(admitted)--leases;}explicit operator bool()const{return admitted;}};
}
'''
}
HARNESS=r'''
#include "utils/JobManager.h"
#include "ServiceBroker.h"
#include "platform/android/activity/InfinityAndroidCheckpoint.h"
#include <cassert>
#include <stdexcept>
static CJobManager*manager;
CJobManager*CServiceBroker::GetJobManager(){return manager;}
class MemoryJob final:public CJob{public:bool DoWork()override{return false;}CheckpointResponsibility GetCheckpointResponsibility(const IJobCallback*callback)const override{return callback?CheckpointResponsibility::Unknown:CheckpointResponsibility::NonPersistent;}};
class RequiredJob:public CJob{bool success;public:explicit RequiredJob(bool ok=true):success(ok){}bool DoWork()override{return success;}
 CheckpointResponsibility GetCheckpointResponsibility(const IJobCallback*)const override{return CheckpointResponsibility::Required;}
 const char*GetCheckpointPersistenceOwner()const override{return "native_databases";}
 ~RequiredJob(){assert(CJobManager::AndroidCheckpointSnapshot().required>0);}};
class UnknownJob:public CJob{public:bool DoWork()override{return true;}bool operator==(const CJob*other)const override{return this==other;}};
class ReceiptJob final:public RequiredJob{public:explicit ReceiptJob(bool ok=true):RequiredJob(ok){}bool RequiresCheckpointCompletionReceipt()const override{return true;}};
class ThrowingCallback:public IJobCallback{public:void OnJobComplete(unsigned int,bool,CJob*)override{throw std::runtime_error("callback write failed");}};
class Callback:public IJobCallback{public:int called=0;void OnJobComplete(unsigned int,bool,CJob*)override{++called;auto s=CJobManager::AndroidCheckpointSnapshot();assert(s.required>0);bool saw=false;for(const auto&e:s.blockers)if(e.phase=="callback")saw=true;assert(saw);}};
int main(int argc,char**argv){assert(argc==2);std::string mode=argv[1];manager=new CJobManager;
 if(mode=="queue"){
  CJobQueue queue(false,1,CJob::PRIORITY_NORMAL,"playback");
  assert(queue.AddJob(new UnknownJob));assert(queue.AddJob(new UnknownJob));
  auto s=CJobManager::AndroidCheckpointSnapshot();assert(s.required==2&&s.unknown==0);
  InfinityAndroidCheckpoint::active=true;CJobWorker worker(manager);worker.Process();
  assert(!queue.IsProcessing());assert(CJobManager::AndroidCheckpointSnapshot().required==0);assert(InfinityAndroidCheckpoint::failures==0);return 0;
 }
 Callback callback;ThrowingCallback throwing;
 if(mode=="receipt-canceled"){
  auto id=manager->AddJob(new ReceiptJob,nullptr);assert(id);manager->CancelJob(id);
  auto s=CJobManager::AndroidCheckpointSnapshot();assert(s.required==1&&s.unknown==0);assert(s.blockers[0].phase=="completed_without_owner_receipt");return 0;
 }
 if(mode=="memory")manager->AddJob(new MemoryJob,nullptr);
 else if(mode=="failure")manager->AddJob(new RequiredJob(false),nullptr);
 else if(mode=="callback")manager->AddJob(new RequiredJob,&callback);
 else if(mode=="unknown")manager->AddJob(new UnknownJob,nullptr);
 else if(mode=="receipt")manager->AddJob(new ReceiptJob,nullptr);
 else if(mode=="receipt-failure" || mode=="preclose-failure")manager->AddJob(new ReceiptJob(false),nullptr);
 else if(mode=="callback-failure")manager->AddJob(new ReceiptJob,&throwing);
 else assert(false);
 assert(InfinityAndroidCheckpoint::leases==0);
 InfinityAndroidCheckpoint::active=mode!="preclose-failure";
 if(InfinityAndroidCheckpoint::active)assert(manager->AddJob(new MemoryJob,nullptr)==0);
 CJobWorker worker(manager);worker.Process();
 auto s=CJobManager::AndroidCheckpointSnapshot();
 if(mode=="unknown"){assert(s.unknown==1&&s.required==1);assert(s.blockers[0].phase=="completed_without_owner_receipt");}
 else if(mode=="receipt-failure" || mode=="preclose-failure" || mode=="callback-failure"){
  assert(s.required==1&&s.unknown==0);assert(s.blockers[0].phase=="completed_write_failed");
 }
 else assert(s.required==0);
 assert(InfinityAndroidCheckpoint::failures==((mode=="failure" || mode=="callback-failure")?1:0));
 if(mode=="callback")assert(callback.called==1);
}
'''
def main():
 p=argparse.ArgumentParser();p.add_argument('--runtime',type=Path,required=True);a=p.parse_args();source=a.runtime/'xbmc'
 with tempfile.TemporaryDirectory(prefix='actual-job-manager-') as temp:
  temp=Path(temp)
  for name in ['Job.h','JobManager.h','JobManager.cpp','JobCheckpoint.h']:
   target=temp/'utils'/name;target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(source/'utils'/name,target)
  for relative,content in STUBS.items():
   target=temp/relative;target.parent.mkdir(parents=True,exist_ok=True);target.write_text(content)
  (temp/'test.cpp').write_text(HARNESS)
  subprocess.run(['g++','-std=c++17','-DTARGET_ANDROID','-Wall','-Wextra','-Werror','-Wno-unused-parameter','-pthread','-I',str(temp),str(temp/'utils/JobManager.cpp'),str(temp/'test.cpp'),'-o',str(temp/'test')],check=True)
  for mode in ['memory','failure','callback','unknown','queue','receipt','receipt-failure','preclose-failure','callback-failure','receipt-canceled']:
   subprocess.run([str(temp/'test'),mode],check=True,timeout=10)
 print('PASS: complete production JobManager.cpp; idle-memory, required failure, callback lifetime, unknown completion, queued transfers')
if __name__=='__main__':main()
