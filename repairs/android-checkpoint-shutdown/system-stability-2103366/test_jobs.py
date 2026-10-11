"""Execute complete production manager with the inherited deterministic peers."""
import runpy
from pathlib import Path

path = Path(__file__).parents[1] / 'runtime-tests/test_job_manager_runtime.py'
fixture = runpy.run_path(str(path), run_name='manager_peers')
harness = fixture['HARNESS'].replace('class ThrowingCallback:', '''
class CancellableReceipt final:public RequiredJob {
 bool started{false}; bool interrupt;
public:
 explicit CancellableReceipt(bool value=false):interrupt(value){}
 bool RequiresCheckpointCompletionReceipt()const override{return true;}
 bool CheckpointCancelledWithoutWork()const override{return !started;}
 bool RequiresCheckpointCallback()const override{return true;}
 bool DoWork()override {started=true;if(interrupt)manager->CancelJob(id);return true;}
 unsigned int id{0};
};
class ThrowingCallback:''')
harness = harness.replace(' Callback callback;ThrowingCallback throwing;', '''
 Callback callback;ThrowingCallback throwing;
 if(mode=="reviewed-queued-cancel" || mode=="reviewed-shutdown-cancel") {
  auto id=manager->AddJob(new CancellableReceipt,&callback);assert(id);
  if(mode=="reviewed-queued-cancel")manager->CancelJob(id);else manager->BeginShutdown();
  assert(callback.called==0);assert(CJobManager::AndroidCheckpointSnapshot().required==0);return 0;
 }
 if(mode=="reviewed-active-cancel") {
  auto*job=new CancellableReceipt(true);job->id=manager->AddJob(job,&callback);
  CJobWorker worker(manager);worker.Process();
  auto snapshot=CJobManager::AndroidCheckpointSnapshot();
  assert(callback.called==0);assert(snapshot.required==1);
  assert(snapshot.blockers[0].phase=="completed_write_failed");return 0;
 }
''')
globals_ = fixture['main'].__globals__
globals_['HARNESS'] = harness
# Reuse the complete compiler, stubs and all inherited cases; add three cases
# without changing historical baseline tests or installing a different manager.
subprocess = globals_['subprocess']
original = subprocess.run
def run(command, **kwargs):
    result = original(command, **kwargs)
    if len(command) == 2 and command[-1] == 'receipt-canceled':
        for mode in ('reviewed-queued-cancel', 'reviewed-shutdown-cancel', 'reviewed-active-cancel'):
            original([command[0], mode], **kwargs)
    return result
subprocess.run = run
fixture['main']()
