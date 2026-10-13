#include "InfinityVfsOpenTrace.h"
#include <condition_variable>
#include <filesystem>
#include <iostream>
#include <mutex>
#include <thread>
#include <vector>
#include <memory>
#include <stdexcept>
namespace V=InfinityVfsOpenTrace;
namespace T=InfinityShutdownTrace;
int main(int argc,char**argv)
{
  if(argc!=3)return 2;
  std::filesystem::create_directories(argv[2]);T::Configure(argv[2]);
  const std::string which=argv[1];
  int file=0;
  if(which=="preclose" || which=="cancel")
  {
    std::mutex mutex;std::condition_variable condition;bool entered=false,finish=false;
    std::thread worker([&]{
      V::Invoker invoker(5,true);V::Open operation(V::Scheme::Https);
      V::Select(V::Backend::Curl);operation.Bind(&file,V::Backend::Curl,true);V::Mark(V::Stage::CurlPoll);
      {std::unique_lock<std::mutex> lock(mutex);entered=true;condition.notify_all();condition.wait(lock,[&]{return finish;});}
      operation.Returned(false);
    });
    {std::unique_lock<std::mutex> lock(mutex);condition.wait(lock,[&]{return entered;});}
    T::Begin();errno=EDOM;V::Request(5,"monitor_notification_sent");
    if(errno!=EDOM)return 3;
    if(which=="cancel")
    {
      V::BackendCancellation(&file,"callback_entered",true);
      V::BackendCancellation(&file,"existing_flag_set",false);
      V::BackendCancellation(&file,"callback_returned",false);
    }
    {std::unique_lock<std::mutex> lock(mutex);if(finish)return 4;finish=true;condition.notify_all();}
    worker.join();V::Milestone(5,"vfs.python.bytecode_return","observed");
    V::Milestone(5,"vfs.python.interpreter_retired","durability_receipt_taken",true);
  }
  else if(which=="nested")
  {
    T::Begin();V::Invoker invoker(5,true);
    {V::Open parent(V::Scheme::Special);V::Select(V::Backend::Special);
      {V::Open child(V::Scheme::Local);V::Select(V::Backend::Posix);child.Returned(true);}
      V::Request(5,"cooperative_stop_called");parent.Returned(true);}
    V::Milestone(5,"vfs.python.interpreter_retired","no_durability_receipt",true);
  }
  else if(which=="inactive")
  {
    T::Begin();V::Invoker unrelated(17,false);V::Open operation(V::Scheme::Https);
    V::Select(V::Backend::Curl);V::Request(17,"cooperative_stop_called");operation.Returned(true);
  }
  else if(which=="exception")
  {
    T::Begin();V::Invoker invoker(5,true);
    try {V::Open operation(V::Scheme::Local);V::Select(V::Backend::Posix);throw std::runtime_error("PRIVATE_URL_PASSWORD");}
    catch(const std::runtime_error&){}
    V::Milestone(5,"vfs.python.interpreter_retired","no_durability_receipt",true);
  }
  else if(which=="capacity")
  {
    T::Begin();V::Invoker invoker(5,true);
    std::vector<std::unique_ptr<V::Open>> operations;
    for(unsigned i=0;i<=V::CAPACITY;++i)operations.push_back(std::make_unique<V::Open>(V::Scheme::Local));
    if(V::current!=nullptr)return 5;
    while(!operations.empty())operations.pop_back();
    if(V::current!=nullptr)return 6;
  }
  else if(which=="reuse")
  {
    T::Begin();V::Invoker invoker(5,true);
    {V::Open first(V::Scheme::Local);first.Bind(&file);V::BackendCancellation(&file,"callback_entered",true);first.Returned(true);}
    {V::Open next(V::Scheme::Https);next.Bind(&file);V::Request(5,"cooperative_stop_called");next.Returned(false);}
  }
  else if(which=="curl_result")
  {
    T::Begin();V::Invoker invoker(5,true);V::Open operation(V::Scheme::Https);
    V::Select(V::Backend::Curl);V::Mark(V::Stage::CurlPerform);V::TransferResult(28);operation.Returned(false);
  }
  else if(which=="stale_cancel")
  {
    T::Begin();V::Record record;
    record.id.store(100);V::ObserveCancellation(record,100);
    V::ObserveCancellation(record,99);if(V::Read(record).cancelCalls!=1)return 8;
    record.id.store(101);record.cancelForId.store(0);
    V::ObserveCancellation(record,100);if(V::Read(record).cancelCalls!=0)return 9;
    V::ObserveCancellation(record,101);V::ObserveCancellation(record,100);
    if(V::Read(record).cancelCalls!=1 || record.cancelForId.load()!=101)return 10;
  }
  else if(which=="stress")
  {
    T::Begin();std::atomic<bool> done{false};
    std::thread reader([&]{for(unsigned i=0;i<200 && !done.load();++i){V::Request(5,"cooperative_stop_called");std::this_thread::yield();}});
    {V::Invoker invoker(5,true);for(unsigned i=0;i<100;++i){V::Open operation(V::Scheme::Https);V::Select(V::Backend::Curl);operation.Bind(&file,V::Backend::Curl,true);operation.Returned(i%2==0);}}
    done.store(true);reader.join();V::Milestone(5,"vfs.python.interpreter_retired","durability_receipt_taken",true);
  }
  else if(which=="multiple_children")
  {
    std::mutex mutex;std::condition_variable cv;unsigned ready=0;bool finish=false;
    int hooks[3]{},files[3]{};
    std::vector<std::thread> workers;
    const char* addons[]={"plugin.video.seren","script.artistslideshow","plugin.video.themoviedb.helper"};
    // Register native interpreter ownership before a child uses its hook.
    std::vector<std::unique_ptr<V::Invoker>> subjects;
    for(unsigned i=0;i<3;++i)
    {subjects.push_back(std::make_unique<V::Invoker>(20+i,true,addons[i]));V::AttachLanguageHook(20+i,&hooks[i]);}
    for(unsigned i=0;i<3;++i)workers.emplace_back([&,i]{
      V::ThreadContext child(&hooks[i]);V::Open operation(V::Scheme::Local,V::Kind::Read);
      operation.Bind(&files[i],i==1?V::Backend::Addon:V::Backend::Posix,true);
      V::Mark(V::Stage::BackendCall);
      {std::unique_lock<std::mutex> lock(mutex);++ready;cv.notify_all();cv.wait(lock,[&]{return finish;});}
      operation.Returned(static_cast<long long>(-1));
    });
    {std::unique_lock<std::mutex> lock(mutex);cv.wait(lock,[&]{return ready==3;});}
    T::Begin();V::CheckpointBegin(7);
    for(unsigned i=0;i<3;++i)V::Request(20+i,"cooperative_stop_called");
    V::CheckpointOutcome(7,false);V::FlushCheckpoint();
    {std::lock_guard<std::mutex> lock(mutex);finish=true;cv.notify_all();}
    for(auto& worker:workers)worker.join();
    for(unsigned i=0;i<3;++i){
      V::Milestone(20+i,"vfs.python.children_retired","no_other_interpreter_thread_states_observed");
      V::Milestone(20+i,"vfs.python.interpreter_end_return","Py_EndInterpreter_returned_not_durability_proof");
      V::Milestone(20+i,"vfs.python.interpreter_retired",i==1?"no_durability_receipt":"durability_receipt_taken");
    }
  }
  else if(which=="callback_after_return")
  {
    std::mutex mutex;std::condition_variable cv;bool entered=false,finish=false;
    std::thread worker([&]{
      V::Invoker invoker(5,true);V::Open operation(V::Scheme::Https);
      operation.Bind(&file,V::Backend::Curl,true);
      {std::unique_lock<std::mutex> lock(mutex);entered=true;cv.notify_all();cv.wait(lock,[&]{return finish;});}
      V::CancelFlagSeen();operation.Returned(false);
    });
    {std::unique_lock<std::mutex> lock(mutex);cv.wait(lock,[&]{return entered;});}
    T::Begin();V::CheckpointBegin(8);
    {
      V::Callback callback(&file);callback.FlagSet();
      {std::lock_guard<std::mutex> lock(mutex);finish=true;cv.notify_all();}
      worker.join();
    }
    V::Milestone(5,"vfs.python.interpreter_retired","durability_receipt_taken");
  }
  else if(which=="native_preclose")
  {
    std::mutex mutex;std::condition_variable cv;bool entered=false,finish=false;
    std::thread worker([&]{
      V::Open operation(V::Scheme::Nfs,V::Kind::Stat);
      operation.Bind(&file,V::Backend::Nfs,true);V::Mark(V::Stage::BackendCall);
      {std::unique_lock<std::mutex> lock(mutex);entered=true;cv.notify_all();cv.wait(lock,[&]{return finish;});}
      operation.Returned(static_cast<long long>(0));
    });
    {std::unique_lock<std::mutex> lock(mutex);cv.wait(lock,[&]{return entered;});}
    T::Begin();V::CheckpointBegin(9);V::CheckpointOutcome(9,false);
    V::OwnerStatus(9,"python_services",3,3,false,true,false,0);
    V::OwnerStatus(9,"native_databases",4,3,true,false,true,1);V::FlushCheckpoint();
    {std::lock_guard<std::mutex> lock(mutex);finish=true;cv.notify_all();}
    worker.join();
  }
  else if(which=="cache_worker")
  {
    T::Begin();V::Invoker invoker(5,true);V::Open parent(V::Scheme::Https);
    V::RegisterFile(&file);const auto id=V::Read(*V::current).id;
    std::thread worker([&]{
      V::FileContext owner(&file);V::Open operation(V::Scheme::Other,V::Kind::CacheProcess);
      V::VoidCompletion completion(operation);operation.Bind(&file,V::Backend::FileCache,true);
      if(V::Read(*V::current).parent!=id)std::terminate();
      V::Callback callback(&file);callback.FlagSet();
    });
    worker.join();V::ForgetFile(&file);parent.Returned(true);
  }
  else if(which=="support_unknown")
  {
    T::Begin();V::Invoker invoker(5,true);
    {V::Open operation(V::Scheme::Other);operation.Bind(&file,V::Backend::Unknown,true);operation.Returned(false);}
    {V::Open operation(V::Scheme::Other);V::Select(V::Backend::Curl);operation.Returned(false);}
  }
  else if(which=="history_gap")
  {
    T::Begin();V::Invoker invoker(5,true);
    auto* subject=V::FindSubject(5);subject->last.id.store(V::INITIALIZING);
    {V::Open operation(V::Scheme::Local);operation.Returned(true);}
    subject->last.id.store(0);
  }
  else if(which=="limits")
  {
    T::Begin();
    for(unsigned i=0;i<=T::MAX_VFS_EVENTS;++i)V::SubjectEvent(-1,"vfs.test.limit","observed");
    T::Event("milestone","checkpoint.result",-1,0,0,0,nullptr,"CHECKPOINT_FAILED");
  }
  else if(which=="native_scope_preclose")
  {
    std::mutex mutex;std::condition_variable cv;bool entered=false,finish=false;
    std::thread worker([&]{
      T::Scope scope("sqlite.commit");
      {std::unique_lock<std::mutex> lock(mutex);entered=true;cv.notify_all();cv.wait(lock,[&]{return finish;});}
    });
    {std::unique_lock<std::mutex> lock(mutex);cv.wait(lock,[&]{return entered;});}
    T::Begin();V::CheckpointBegin(10);V::CheckpointOutcome(10,false);V::FlushCheckpoint();
    {std::lock_guard<std::mutex> lock(mutex);finish=true;cv.notify_all();}
    worker.join();
  }
  else return 7;
  std::cout<<"PASS "<<which<<"\n";return 0;
}
