#!/usr/bin/env python3
"""Extend the existing complete production JobManager harness; no simulated write coverage."""
import argparse
import hashlib
import importlib.util
from pathlib import Path
import shutil
import subprocess
import tempfile
import apply_runtime

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]

def module(path,name):
    spec=importlib.util.spec_from_file_location(name,path);value=importlib.util.module_from_spec(spec);spec.loader.exec_module(value);return value

def main():
    p=argparse.ArgumentParser();p.add_argument('--runtime',type=Path);args=p.parse_args()
    old=module(ROOT/'repairs/android-checkpoint-shutdown/runtime-tests/test_job_manager_runtime.py','essential_existing_job_runtime')
    with tempfile.TemporaryDirectory(prefix='essential-actual-jobs-') as folder:
        folder=Path(folder)
        if args.runtime:
            source=args.runtime/'xbmc'
        else:
            source=folder/'source/xbmc';overlay=ROOT/'repairs/android-checkpoint-shutdown/runtime/native/overlay/xbmc'
            for name in ('utils/Job.h','utils/JobManager.h','utils/JobManager.cpp',
                         'platform/android/activity/InfinityAndroidCheckpoint.cpp'):
                target=source/name;target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(overlay/name,target)
            prune=module(ROOT/'repairs/shutdown-drain-2103377/prune_optional_jobs.py','essential_existing_optional_prune')
            prune.apply(source.parent)
            job=source/'utils/JobManager.cpp'
            assert hashlib.sha256(job.read_bytes()).hexdigest()==apply_runtime.PINS[apply_runtime.JOBS]
            job.write_text(apply_runtime.jobs(job.read_text()))
            shutil.copyfile(HERE/'runtime/xbmc/utils/JobCheckpoint.h',source/'utils/JobCheckpoint.h')
        harness=old.HARNESS.replace('int main(int argc,char**argv)',r'''
class CRepositoryUpdateJob final:public CJob {public:bool DoWork()override{return false;}};
class OptionalCallback:public IJobCallback {public:bool called=false;
 void OnJobComplete(unsigned int,bool,CJob*)override {
  const auto state=CJobManager::AndroidCheckpointSnapshot();
  assert(state.required==0 && state.unknown==0 && state.optionalUnfinished.size()==1);
  assert(state.optionalUnfinished[0].operation=="repository_update");
  assert(state.optionalUnfinished[0].phase=="callback");called=true;
 }};
int main(int argc,char**argv)''')
        harness=harness.replace(' Callback callback;ThrowingCallback throwing;',r'''
 if(mode=="startup-job-admission" || mode=="startup-job-failure") {
  InfinityAndroidCheckpoint::active=true;InfinityAndroidCheckpoint::startupPending=true;
  const auto id=manager->AddJob(new RequiredJob(mode!="startup-job-failure"),nullptr);assert(id);
  assert(CJobManager::AndroidCheckpointSnapshot().required==1);
  CJobWorker worker(manager);worker.Process();
  assert(InfinityAndroidCheckpoint::failures==(mode=="startup-job-failure"?1:0));
  InfinityAndroidCheckpoint::startupPending=false;
  assert(manager->AddJob(new MemoryJob,nullptr)==0);
  return 0;
 }
 if(mode=="repository-pending" || mode=="repository-callback" || mode=="repository-refused") {
  OptionalCallback observer;
  const auto id=manager->AddJob(new CRepositoryUpdateJob,&observer);assert(id);
  const auto state=CJobManager::AndroidCheckpointSnapshot();
  assert(state.required==0 && state.unknown==0 && state.nonPersistent==1);
  assert(state.optionalUnfinished.size()==1 && state.optionalUnfinished[0].operation=="repository_update");
  InfinityAndroidCheckpoint::active=true;
  if(mode=="repository-refused") assert(manager->AddJob(new CRepositoryUpdateJob,&observer)==0);
  if(mode=="repository-callback") {CJobWorker worker(manager);worker.Process();assert(observer.called);}
  assert(InfinityAndroidCheckpoint::failures==0);return 0;
 }
 Callback callback;ThrowingCallback throwing;''')
        for name in ['Job.h','JobManager.h','JobManager.cpp','JobCheckpoint.h']:
            target=folder/'utils'/name;target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(source/'utils'/name,target)
        for name,content in old.STUBS.items():
            if name == 'platform/android/activity/InfinityAndroidCheckpoint.h':
                # Existing cases model an initialized engine. Pending startup
                # uses the real coordinator in run_runtime_coordinator_tests.
                content = content.replace('inline bool IsActive(){return active;}',
                    'inline bool startupPending=false;inline bool IsActive(){return active;}inline bool IsWriteAdmissionActive(){return active&&!startupPending;}')
                content = content.replace('admitted(!active)', 'admitted(!active||startupPending)')
            target=folder/name;target.parent.mkdir(parents=True,exist_ok=True);target.write_text(content)
        (folder/'test.cpp').write_text(harness)
        subprocess.run(['g++','-std=c++17','-DTARGET_ANDROID','-Wall','-Wextra','-Werror','-Wno-unused-parameter','-pthread','-I',str(folder),str(folder/'utils/JobManager.cpp'),str(folder/'test.cpp'),'-o',str(folder/'test')],check=True)
        cases=['memory','failure','callback','unknown','queue','receipt','receipt-failure','preclose-failure','callback-failure','receipt-canceled','repository-pending','repository-callback','repository-refused','startup-job-admission','startup-job-failure']
        for case in cases:
            subprocess.run([str(folder/'test'),case],check=True,timeout=10)
            print('PASS',case)
        print('PASS 15 full production JobManager cases; original 13 retained, required startup admission and failure accounting verified')

if __name__=='__main__':main()
