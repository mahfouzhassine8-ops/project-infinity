#!/usr/bin/env python3
"""Compile *the real transformed C++ method* with guarded test peers.

The host harness extracts the exact production method; it does not reimplement
its selection loop. It must reject required/unknown/callback/save work and only
prune verified nonpersistent never-started jobs.
"""
from pathlib import Path
import json
import subprocess
import tempfile
import shutil
import sys
import hashlib

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
sys.path.insert(0,str(HERE))
import prune_optional_jobs

def run():
    source_overlay=ROOT/'repairs/android-checkpoint-shutdown/runtime/native/overlay'
    cases={}
    with tempfile.TemporaryDirectory(prefix='rc2-checkpoint-') as tmp:
        tmp=Path(tmp)
        original={}
        for name in (prune_optional_jobs.CPP,prune_optional_jobs.HEADER,prune_optional_jobs.CHECKPOINT):
            source=source_overlay/name
            if not source.is_file(): raise RuntimeError('Missing pinned Kodi source: '+name)
            target=tmp/name
            target.parent.mkdir(parents=True,exist_ok=True)
            shutil.copy2(source,target)
            original[name]=hashlib.sha256(target.read_bytes()).hexdigest()
        receipt=prune_optional_jobs.apply(tmp)
        assert len(receipt['changed'])==3
        assert all(receipt['after'][key]!=original[key] for key in receipt['changed'])
        cases['three_only_approved_source_files_changed']=True
        try: prune_optional_jobs.apply(tmp)
        except ValueError: cases['reject_duplicate_or_unpinned_apply']=True
        else: raise AssertionError('Transform applied twice without a source guard')
        coordinator=(tmp/prune_optional_jobs.CHECKPOINT).read_text()
        assert coordinator.index('PruneCheckpointOptionalQueuedJobs();')<coordinator.index('UnPauseJobs();')
        cases['cancel_before_unpause_order']=True
        header=(tmp/prune_optional_jobs.HEADER).read_text()
        assert header.count('void PruneCheckpointOptionalQueuedJobs();')==1
        cases['native_method_declared_once']=True
        cpp=(tmp/prune_optional_jobs.CPP).read_text()
        start=cpp.index('#if defined(TARGET_ANDROID)\nvoid CJobManager::PruneCheckpointOptionalQueuedJobs()')
        end=cpp.index('\n#endif',start)+len('\n#endif')
        production=cpp[start:end]
        assert 'record->required' in production and 'record->unknown' in production
        assert 'it->m_callback == nullptr' in production and 'item.FreeJob();' in production
        assert production.index('it = queue.erase(it);')<production.index('item.FreeJob();')
        cases['prunes_without_fabricating_save_receipts']=True
        harness=r'''#include <cassert>
#include <deque>
#include <iostream>
#include <memory>
#include <mutex>
#include <string>
#include <vector>
using CCriticalSection=std::mutex;
struct CJobCheckpointRecord {
  bool required=true;
  bool unknown=true;
};
struct CJob {
  std::shared_ptr<CJobCheckpointRecord> m_checkpointRecord;
  bool callbackNeeded=false, receiptNeeded=false;
  static int destructionCount;
  ~CJob() { ++destructionCount; }
  bool RequiresCheckpointCallback() const {return callbackNeeded;}
  bool RequiresCheckpointCompletionReceipt() const {return receiptNeeded;}
};
int CJob::destructionCount=0;
namespace InfinityAndroidCheckpoint {
bool active=true;
bool IsActive() { return active; }
}
namespace InfinityShutdownTrace {
int count=0;
void Event(const char*,const char*,long long) { ++count; }
}
namespace JobCheckpoint {
int phaseCount=0;
void Phase(const std::shared_ptr<CJobCheckpointRecord>&,const char*,unsigned int) {++phaseCount;}
}
class CJobManager {
public:
struct CWorkItem {
  CJob* m_job;
  unsigned int m_id;
  void* m_callback;
  void FreeJob() { delete m_job; m_job=nullptr; }
};
std::deque<CWorkItem> m_jobQueue[3];
CCriticalSection m_section;
void PruneCheckpointOptionalQueuedJobs();
};
''' +production+r'''
static CJob* job(bool required,bool unknown,bool callbackNeeded=false,bool receiptNeeded=false) {
 auto p=new CJob;
 p->m_checkpointRecord=std::make_shared<CJobCheckpointRecord>();
 p->m_checkpointRecord->required=required;p->m_checkpointRecord->unknown=unknown;
 p->callbackNeeded=callbackNeeded;p->receiptNeeded=receiptNeeded;
 return p;
}
int main() {
 CJobManager m;
 // No active Close: even proven optional jobs must remain live.
 InfinityAndroidCheckpoint::active=false;
 m.m_jobQueue[0].push_back({job(false,false),1,nullptr});
 m.PruneCheckpointOptionalQueuedJobs();
 assert(m.m_jobQueue[0].size()==1 && CJob::destructionCount==0);
 // During Close, preserve required/unknown, callback and receipt-owned items.
 InfinityAndroidCheckpoint::active=true;
 m.m_jobQueue[0].push_back({job(true,false),2,nullptr});
 m.m_jobQueue[1].push_back({job(false,true),3,nullptr});
 m.m_jobQueue[1].push_back({job(false,false),4,reinterpret_cast<void*>(1)});
 m.m_jobQueue[2].push_back({job(false,false,true,false),5,nullptr});
 m.m_jobQueue[2].push_back({job(false,false,false,true),6,nullptr});
 m.m_jobQueue[2].push_back({job(false,false),7,nullptr});
 m.PruneCheckpointOptionalQueuedJobs();
 assert(CJob::destructionCount==2);
 assert(JobCheckpoint::phaseCount==2 && InfinityShutdownTrace::count==1);
 assert(m.m_jobQueue[0].size()==1 && m.m_jobQueue[0][0].m_id==2);
 assert(m.m_jobQueue[1].size()==2);
 assert(m.m_jobQueue[2].size()==2);
 // Repeat is a no-op, not an accidental mandatory job cancel.
 m.PruneCheckpointOptionalQueuedJobs();
 assert(CJob::destructionCount==2 && JobCheckpoint::phaseCount==2);
 std::cout<<"PASS: inactive, optional, required, unknown, callback, receipt, idempotent"<<std::endl;
}
'''
        test=tmp/'test_native_optional_queue.cpp'
        test.write_text(harness)
        binary=tmp/'test_native_optional_queue'
        compiled=subprocess.run(['g++','-std=c++17','-O2','-pthread','-Wall','-Wextra','-Werror',
                                '-DTARGET_ANDROID',str(test),'-o',str(binary)],capture_output=True,text=True,timeout=45)
        if compiled.returncode: raise AssertionError(compiled.stderr)
        tested=subprocess.run([str(binary)],capture_output=True,text=True,timeout=15)
        if tested.returncode:raise AssertionError(tested.stderr+tested.stdout)
        cases['compiled_real_method_with_mocked_native_peers']=True
        cases['required_unknown_callback_and_receipt_protected']=True
        cases['repeated_checkpoint_pruning_is_idempotent']=True
        cases['ordinary_running_never_prunes']=True
    report={'tests':len(cases),'passed':len(cases),'checks':cases,
       'scope':'C++ native method compiled and executed with controlled mock peers; entire Kodi library not compiled here',
       'production_source_changes':False}
    print(json.dumps(report,indent=2,sort_keys=True))
    return report

if __name__=='__main__':
    report=run()
    if len(sys.argv)>1:
        Path(sys.argv[1]).write_text(json.dumps(report,indent=2,sort_keys=True)+'\n')
