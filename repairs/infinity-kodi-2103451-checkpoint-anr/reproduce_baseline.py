"""Bounded baseline reproductions; no database, Android or repaired-runtime claim."""
from pathlib import Path
import argparse
import hashlib
import importlib.util
import json
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
OVERLAY = ROOT / 'repairs/android-checkpoint-shutdown/runtime/native/overlay/xbmc'
ESSENTIAL = ROOT / 'repairs/essential-first-2103377'


def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--inputs', type=Path, default=Path('/tmp/kodi451-p0-inputs'))
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)
    if (args.out / 'RESULTS.json').exists():
        raise ValueError('Preserve completed results; do not repeat a passing run')
    old = load(ROOT / 'repairs/android-checkpoint-shutdown/runtime-tests/test_job_checkpoint.py',
               'p0_tracking_function_reader')
    sys.path.insert(0, str(ESSENTIAL))
    apply_runtime = load(ESSENTIAL / 'apply_runtime.py', 'p0_retained_essential_producer')
    prune = load(ROOT / 'repairs/shutdown-drain-2103377/prune_optional_jobs.py',
                 'p0_retained_optional_prune')
    source = args.out / 'source/xbmc'
    bindings = {}
    for relative in ('utils/Job.h', 'utils/JobManager.h', 'utils/JobManager.cpp',
                     'platform/android/activity/InfinityAndroidCheckpoint.cpp'):
        original = OVERLAY / relative
        target = source / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(original, target)
        bindings[str(original.relative_to(ROOT))] = digest(original)
    prune.apply(source.parent)
    manager = source / 'utils/JobManager.cpp'
    assert digest(manager) == apply_runtime.PINS[apply_runtime.JOBS]
    manager.write_text(apply_runtime.jobs(manager.read_text()))
    ledger = ESSENTIAL / 'runtime/xbmc/utils/JobCheckpoint.h'
    shutil.copyfile(ledger, source / 'utils/JobCheckpoint.h')
    bindings[str(ledger.relative_to(ROOT))] = digest(ledger)
    bindings['reconstructed_JobManager.cpp'] = digest(manager)

    manifest = json.loads((ROOT / 'repairs/android-checkpoint-shutdown/runtime/native/manifest.json').read_text())
    for relative in ('video/jobs/VideoLibraryJob.h', 'video/jobs/VideoLibraryMarkWatchedJob.h'):
        original = args.inputs / 'xbmc' / relative
        expected = manifest['before']['xbmc/' + relative]
        assert digest(original) == expected == manifest['after']['xbmc/' + relative]
        target = source / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(original, target)
        bindings['pinned_upstream/xbmc/' + relative] = expected

    threads = source / 'threads'
    threads.mkdir()
    (threads / 'CriticalSection.h').write_text('#pragma once\n#include <mutex>\nusing CCriticalSection=std::recursive_mutex;\n')
    (threads / 'Thread.h').write_text('#pragma once\nclass CEvent {}; class CThread {public: virtual ~CThread()=default;virtual void Process(){};};\n')
    tracking = '\n'.join(old.function(manager.read_text(), marker) for marker in (
        'void CJobManager::TrackCheckpointJob(', 'void CJobManager::TrackCheckpointPhase(',
        'bool CJobManager::IsRequiredCheckpointJob(', 'JobCheckpoint::Snapshot CJobManager::AndroidCheckpointSnapshot()'))
    job_cpp = r'''
#include "utils/JobManager.h"
#include "video/jobs/VideoLibraryMarkWatchedJob.h"
#include <cassert>
#include <typeinfo>
namespace InfinityAndroidCheckpoint {
bool IsRequiredOwner(const std::string& owner) {return owner=="native_databases" || owner=="playback";}
}
bool CJob::ShouldCancel(unsigned int,unsigned int)const{return false;}
// Work/DB boundaries only: deliberately no real database or persistence proof.
class CVideoDatabase {};
CVideoLibraryJob::CVideoLibraryJob()=default;
CVideoLibraryJob::~CVideoLibraryJob()=default;
bool CVideoLibraryJob::DoWork(){CVideoDatabase db;return Work(db);}
CVideoLibraryMarkWatchedJob::CVideoLibraryMarkWatchedJob(const std::shared_ptr<CFileItem>& item,bool mark):m_item(item),m_mark(mark){}
CVideoLibraryMarkWatchedJob::~CVideoLibraryMarkWatchedJob()=default;
bool CVideoLibraryMarkWatchedJob::operator==(const CJob* other)const{return this==other;}
bool CVideoLibraryMarkWatchedJob::Work(CVideoDatabase&){return true;}
class QueueCallback final:public IJobCallback {
 void OnJobComplete(unsigned int,bool,CJob*)override{}
};
''' + tracking + r'''
int main(){
 QueueCallback callback;
 auto* job=new CVideoLibraryMarkWatchedJob(nullptr,true);
 assert(std::string(typeid(*job).name())=="27CVideoLibraryMarkWatchedJob");
 assert(job->GetCheckpointResponsibility(&callback)==CJob::CheckpointResponsibility::Unknown);
 assert(!job->RequiresCheckpointCompletionReceipt());
 CJobManager::TrackCheckpointJob(job,&callback,"queue_pending");
 assert(CJobManager::IsRequiredCheckpointJob(job));
 assert(job->DoWork()); // ordinary success, deliberately no persistence receipt
 CJobManager::TrackCheckpointPhase(job,"destructor",973);
 delete job;
 auto snapshot=CJobManager::AndroidCheckpointSnapshot();
 assert(snapshot.required==1 && snapshot.unknown==1 && snapshot.blockers.size()==1);
 const auto& blocker=snapshot.blockers.front();
 assert(blocker.type=="27CVideoLibraryMarkWatchedJob" && blocker.owner.empty() && blocker.resource.empty());
 assert(blocker.jobId==973 && blocker.phase=="completed_without_owner_receipt");
}
'''
    (args.out / 'watched.cpp').write_text(job_cpp)

    application_path = OVERLAY / 'application/Application.cpp'
    checkpoint_path = OVERLAY / 'platform/android/activity/InfinityAndroidCheckpoint.cpp'
    application = application_path.read_text()
    coordinator = checkpoint_path.read_text()
    bindings[str(application_path.relative_to(ROOT))] = digest(application_path)
    bindings[str(checkpoint_path.relative_to(ROOT))] = digest(checkpoint_path)
    fail = old.function(coordinator, 'void FinalizeInventoryFailureLocked(')
    active = old.function(coordinator, 'bool IsActive()')
    pump = old.function(coordinator, 'void Pump(CApplication& application)')
    pump = pump[:pump.index('  CoordinatorWriteScope permission;')] + '  ++afterGuard;\n}\n'
    process = old.function(application, 'void CApplication::Process()')
    process = process[:process.index('  // dispatch the messages generated')] + '  ++dispatchReached;\n}\n'
    message = old.function(application, 'void CApplication::OnApplicationMessage(')
    message = message[:message.index('  uint32_t msg = pMsg->dwMessage;')] + '  ++messageReached;\n}\n'
    assert 's.active' not in fail
    assert 's.phase == "CHECKPOINT_FAILED"' in pump
    assert 'InfinityAndroidCheckpoint::IsActive()' in process
    assert 'InfinityAndroidCheckpoint::IsActive()' in message
    lifecycle_cpp = r'''
#include <atomic>
#include <cassert>
#include <cstdint>
#include <mutex>
#include <string>
struct ThreadMessage {uint32_t dwMessage;};
class CApplication {public:void Process();void OnApplicationMessage(ThreadMessage*);};
int dispatchReached=0,messageReached=0;
namespace InfinityAndroidCheckpoint {
// Controlled boundaries for the exact production early branches below.
struct State {std::mutex mutex;std::atomic<bool> active{true};bool requestReady=true;
 bool sealed=false,inventoryComplete=false;std::string phase="QUIESCE",safeStatus="";};
State& Get(){static State state;return state;}
void CheckDeadlineLocked(State&){}
int afterGuard=0;
''' + fail + active + pump + '\n}\n' + process + message + r'''
int main(int argc,char** argv){
 assert(argc==2);const std::string mode=argv[1];CApplication app;
 auto& state=InfinityAndroidCheckpoint::Get();
 InfinityAndroidCheckpoint::FinalizeInventoryFailureLocked(state);
 assert(state.phase=="CHECKPOINT_FAILED" && state.active && state.sealed);
 if(mode=="failed-dispatch"){
   for(int i=0;i<10;++i)app.Process();
   assert(InfinityAndroidCheckpoint::afterGuard==0 && dispatchReached==0);
   // Negative control: ordinary (non-checkpoint) processing reaches dispatch.
   state.active=false;app.Process();assert(dispatchReached==1);return 0;
 }
 if(mode=="message-rejection"){
   // The guard precedes inspection of the ID; it rejects every application
   // message, including the display-destroy class, independently of its ID.
   ThreadMessage message{0};app.OnApplicationMessage(&message);assert(messageReached==0);
   state.active=false;app.OnApplicationMessage(&message);assert(messageReached==1);return 0;
 }
 assert(false);
}
'''
    (args.out / 'lifecycle.cpp').write_text(lifecycle_cpp)
    cases = []
    for filename, modes in (('watched', [None]), ('lifecycle', ['failed-dispatch', 'message-rejection'])):
        binary = args.out / filename
        command = ['g++', '-std=c++17', '-DTARGET_ANDROID', '-Wall', '-Wextra', '-Werror',
                   '-Wno-unused-parameter', '-pthread', '-I', str(source),
                   str(args.out / (filename + '.cpp')), '-o', str(binary)]
        compiled = subprocess.run(command, capture_output=True, text=True)
        (args.out / (filename + '-compile.txt')).write_text(compiled.stdout + compiled.stderr)
        if compiled.returncode:
            raise RuntimeError('Compile failed; inspect ' + str(args.out / (filename + '-compile.txt')))
        for mode in modes:
            run = [str(binary)] + ([mode] if mode else [])
            result = subprocess.run(run, capture_output=True, text=True, timeout=10)
            case = {'case': mode or 'watched-unknown-completion', 'command': run,
                    'compiler': command, 'status': 'BASELINE_DEFECT_REPRODUCED' if result.returncode == 0 else 'REPRODUCTION_FAILED',
                    'exit_code': result.returncode, 'output': result.stdout + result.stderr}
            cases.append(case)
            if result.returncode:
                (args.out / 'FAILED-CASE.json').write_text(json.dumps(case, indent=2) + '\n')
                raise RuntimeError('Baseline reproduction failed: ' + case['case'])
            print(case['case'] + ': ' + case['status'])
    report = {'purpose': 'source-bound baseline failure reproduction', 'cases': cases,
              'source_sha256': bindings, 'production_files_modified': False,
              'real_database_operations': False, 'android_execution': False,
              'physical_fold_acceptance': False, 'repairs_implemented': False,
              'exact_final_native_source_map_recovered': False,
              'limitations': ['Work and DB boundaries are stubbed; no durability success is asserted.',
                              'Lifecycle probes compile exact early branches with controlled peers, not the whole application.',
                              'Final native source-map provenance, full diagnostics access and Android runtime verification remain open.']}
    (args.out / 'RESULTS.json').write_text(json.dumps(report, indent=2) + '\n')


if __name__ == '__main__':
    main()
