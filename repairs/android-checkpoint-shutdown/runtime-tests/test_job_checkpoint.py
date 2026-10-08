#!/usr/bin/env python3
"""Production job admission metadata and lifetime registry with controlled peers.

Compiles real Job/JobManager headers and real tracking functions. Does not claim
Android ABI or validation of unaudited DoWork implementations.
"""
from pathlib import Path
import argparse
import shutil
import subprocess
import tempfile


def function(source, marker):
    start=source.index(marker);end=source.index('{',start)+1;depth=1
    while depth:
        depth+=(source[end]=='{')-(source[end]=='}');end+=1
    return source[start:end]

PEERS=r'''
#include "utils/JobManager.h"
#include <cassert>
#include <typeinfo>
#include <thread>
namespace InfinityAndroidCheckpoint {bool IsRequiredOwner(const std::string&s){return s=="native_databases"||s=="playback";}}
bool CJob::ShouldCancel(unsigned int,unsigned int)const{return false;}
class Callback:public IJobCallback{void OnJobComplete(unsigned int,bool,CJob*)override{}};
class UnknownJob:public CJob{public:bool DoWork()override{return true;}const char*GetType()const override{return "system-info-read";}};
class MemoryJob final:public CJob{public:bool DoWork()override{return false;}
 CheckpointResponsibility GetCheckpointResponsibility(const IJobCallback*c)const override{return c?CheckpointResponsibility::Unknown:CheckpointResponsibility::NonPersistent;}};
class RequiredJob:public CJob{public:bool DoWork()override{return true;}
 CheckpointResponsibility GetCheckpointResponsibility(const IJobCallback*)const override{return CheckpointResponsibility::Required;}
 const char*GetCheckpointPersistenceOwner()const override{return "native_databases";}
 const char*GetCheckpointOperation()const override{return "checked-database-write";}
 ~RequiredJob(){assert(CJobManager::AndroidCheckpointSnapshot().required>0);}};
'''
TEST=r'''
int main(int argc,char**argv){assert(argc==2);std::string mode=argv[1];
 if(mode=="unknown"){
  auto*j=new UnknownJob;CJobManager::TrackCheckpointJob(j,nullptr,"pending");
  assert(CJobManager::IsRequiredCheckpointJob(j));assert(j->DoWork());delete j;
  auto s=CJobManager::AndroidCheckpointSnapshot();assert(s.unknown==1&&s.required==1);
  assert(s.blockers[0].phase=="completed_without_owner_receipt");
  for(int n=0;n<10000;++n){auto*x=new UnknownJob;CJobManager::TrackCheckpointJob(x,nullptr,"pending");delete x;}
  assert(CJobManager::AndroidCheckpointSnapshot().unknown==1);assert(JobCheckpoint::Get().unresolved.size()==1);return 0;
 }
 if(mode=="callback"){
  Callback cb;auto*j=new MemoryJob;CJobManager::TrackCheckpointJob(j,&cb,"pending");assert(CJobManager::IsRequiredCheckpointJob(j));delete j;
  assert(CJobManager::AndroidCheckpointSnapshot().unknown==1);return 0;
 }
 if(mode=="memory"){
  auto*j=new MemoryJob;CJobManager::TrackCheckpointJob(j,nullptr,"running");auto s=CJobManager::AndroidCheckpointSnapshot();
  assert(s.required==0&&s.nonPersistent==1);assert(!j->DoWork());assert(!CJobManager::IsRequiredCheckpointJob(j));delete j;
  assert(CJobManager::AndroidCheckpointSnapshot().nonPersistent==0);return 0;
 }
 if(mode=="required"){
  auto*j=new RequiredJob;CJobManager::TrackCheckpointJob(j,nullptr,"queue_pending");auto first=CJobManager::AndroidCheckpointSnapshot();
  assert(first.required==1&&first.unknown==0);assert(first.blockers[0].operation=="checked-database-write");
  Callback wrapper;CJobManager::TrackCheckpointJob(j,&wrapper,"manager_pending");
  assert(CJobManager::AndroidCheckpointSnapshot().blockers[0].token==first.blockers[0].token);
  CJobManager::TrackCheckpointPhase(j,"callback",17);auto callback=CJobManager::AndroidCheckpointSnapshot();
  assert(callback.required==1&&callback.blockers[0].phase=="callback"&&callback.blockers[0].jobId==17);
  CJobManager::TrackCheckpointPhase(j,"destructor",17);delete j;
  assert(CJobManager::AndroidCheckpointSnapshot().required==0);return 0;
 }
 if(mode=="queue-owner"){
  auto f=[]{};auto*j=new CLambdaJob<decltype(f)>(std::move(f));Callback queue;
  CJobManager::TrackCheckpointJob(j,&queue,"queue_pending","playback");assert(CJobManager::AndroidCheckpointSnapshot().unknown==0);delete j;
  assert(CJobManager::AndroidCheckpointSnapshot().required==0);return 0;
 }
 if(mode=="bad-owner"){
  auto f=[]{};auto*j=new CLambdaJob<decltype(f)>("made-up-owner","bad-mapping",std::move(f));
  CJobManager::TrackCheckpointJob(j,nullptr,"pending");delete j;assert(CJobManager::AndroidCheckpointSnapshot().unknown==1);return 0;
 }
 if(mode=="race"){
  for(int n=0;n<200;++n){auto*j=new RequiredJob;CJobManager::TrackCheckpointJob(j,nullptr,"running");std::thread t([&]{CJobManager::TrackCheckpointPhase(j,"callback",42);});
   auto s=CJobManager::AndroidCheckpointSnapshot();assert(s.required==1);t.join();delete j;assert(CJobManager::AndroidCheckpointSnapshot().required==0);}return 0;
 }
 assert(false);
}
'''
def main():
    p=argparse.ArgumentParser();p.add_argument('--runtime',type=Path,required=True);a=p.parse_args();root=a.runtime/'xbmc'
    source=(root/'utils/JobManager.cpp').read_text()
    methods=[function(source,marker) for marker in ['void CJobManager::TrackCheckpointJob(', 'void CJobManager::TrackCheckpointPhase(', 'bool CJobManager::IsRequiredCheckpointJob(', 'JobCheckpoint::Snapshot CJobManager::AndroidCheckpointSnapshot()']]
    # Preserve hooks around the exact production admission/callback/destructor sites.
    assert 'CheckpointWriteGuard>("jobs")' in function(source,'unsigned int CJobManager::AddJob(')
    assert 'TrackCheckpointJob(job, this, "queue_pending", m_checkpointOwner)' in function(source,'bool CJobQueue::AddJob(')
    assert 'TrackCheckpointPhase(job, "callback"' in function(source,'void CJobManager::OnJobComplete(')
    assert 'TrackCheckpointPhase(item.m_job, "destructor"' in function(source,'void CJobManager::OnJobComplete(')
    with tempfile.TemporaryDirectory(prefix='job-checkpoint-') as temp:
        temp=Path(temp)
        for relative in ['utils/Job.h','utils/JobManager.h','utils/JobCheckpoint.h']:
            target=temp/relative;target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(root/relative,target)
        (temp/'threads').mkdir();(temp/'threads/CriticalSection.h').write_text('#pragma once\n#include <mutex>\nusing CCriticalSection=std::recursive_mutex;\n')
        (temp/'threads/Thread.h').write_text('#pragma once\nclass CEvent {}; class CThread {public: virtual ~CThread()=default;virtual void Process(){};};\n')
        (temp/'test.cpp').write_text(PEERS+'\n'.join(methods)+TEST)
        subprocess.run(['g++','-std=c++17','-DTARGET_ANDROID','-Wall','-Wextra','-Werror','-Wno-unused-parameter','-pthread','-I',str(temp),str(temp/'test.cpp'),'-o',str(temp/'test')],check=True)
        for mode in ['unknown','callback','memory','required','queue-owner','bad-owner','race']:
            subprocess.run([str(temp/'test'),mode],check=True,timeout=10)
    print('PASS: actual job metadata + registry; 7 cases, 200 phase races, lifetime unknown retention, callbacks/destructors and 10000-invocation bound')
if __name__=='__main__':main()
