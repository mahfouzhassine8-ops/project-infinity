// Tests the actual transformed LanguageInvokerThread.cpp with explicitly mocked
// Kodi/runtime boundaries. Does not reproduce CPython or Android native unload.
#include "LanguageInvokerThread.h"
#include "ScriptInvocationManager.h"
#include "InfinityInvokerTarget.h"
#include "platform/android/activity/InfinityShutdownTrace.h"
#include <chrono>
#include <cstdio>
#include <functional>
#include <iostream>
#include <stdexcept>
#include <sys/syscall.h>
#include <unistd.h>
using namespace std::chrono_literals;
static void require(bool ok,const char* text) { if(!ok) throw std::runtime_error(text); }
static void until(const std::function<bool()>& f) {
  const auto end=std::chrono::steady_clock::now()+3s;
  while(!f()) { if(std::chrono::steady_clock::now()>end) throw std::runtime_error("test wait expired"); std::this_thread::sleep_for(1ms); }
}
struct Gate {
  std::mutex mutex;std::condition_variable cv;bool released=false;std::atomic<bool> entered{false};
  void wait() { entered=true;std::unique_lock<std::mutex> l(mutex);cv.wait(l,[this]{return released;}); }
  void open() { std::lock_guard<std::mutex> l(mutex);released=true;cv.notify_all(); }
};
struct Invoker : ILanguageInvoker {
  Gate execution,finalizer,exception;std::atomic<unsigned> tid{0};std::atomic<int> stopCount{0},doneCount{0};
  bool blockExecute=false,blockFinalizer=false,throwExecute=false,reusable=false;
  Invoker():ILanguageInvoker(nullptr){}
  bool execute(const std::string&,const std::vector<std::string>&) override {
    tid=static_cast<unsigned>(::syscall(SYS_gettid));m_state=InvokerStateRunning;
    if(throwExecute)throw std::runtime_error("test exception");
    if(blockExecute)execution.wait();
    m_state=reusable?InvokerStateScriptDone:InvokerStateExecutionDone;return true;
  }
  bool stop(bool) override { ++stopCount;execution.open();return true; }
  void onExecutionDone() override { if(blockFinalizer)finalizer.wait();++doneCount; }
  void onExecutionFailed() override { exception.wait();++doneCount; }
};
static void clearRows(){std::lock_guard<std::mutex> l(InfinityShutdownTrace::rowMutex);InfinityShutdownTrace::rows.clear();}
static std::vector<InfinityShutdownTrace::Row> rows(){std::lock_guard<std::mutex> l(InfinityShutdownTrace::rowMutex);return InfinityShutdownTrace::rows;}
static bool has(const char* phase){for(const auto& row:rows())if(row.phase==phase)return true;return false;}
static InfinityShutdownTrace::Row last(const char* phase){auto r=rows();for(auto it=r.rbegin();it!=r.rend();++it)if(it->phase==phase)return *it;throw std::runtime_error("missing row");}
static void checkRow(const char* phase,unsigned tid,const char* stage,bool addon=true){
  const auto row=last(phase);require(row.invoker==42,"wrong invoker id");
  require(row.addon==(addon?"service.test.fixture":""),"wrong addon id");
  require(row.target=="os_tid."+std::to_string(tid)+".stage."+stage,"wrong target tid/stage");
  require(row.outcome=="snapshot_not_liveness","incorrect liveness claim");
}
static ADDON::AddonPtr addon(){return std::make_shared<ADDON::TestAddon>(ADDON::TestAddon{"service.test.fixture"});}
static void stalled(const std::string& name,bool managerBlock,bool failure,bool nonblocking,bool withAddon){
  clearRows();auto inv=std::make_shared<Invoker>();inv->blockFinalizer=!managerBlock&&!failure;inv->throwExecute=failure;
  CScriptInvocationManager manager;Gate managerGate;std::atomic<int> callbacks{0};
  manager.callback=[&](int id){require(id==42,"wrong callback id");++callbacks;if(managerBlock)managerGate.wait();};
  CLanguageInvokerThread wrapper(inv,&manager,false);wrapper.SetId(42);if(withAddon)wrapper.SetAddon(addon());
  require(wrapper.Execute("fixture.py"),"execute rejected");
  until([&]{return managerBlock?managerGate.entered.load():failure?inv->exception.entered.load():inv->finalizer.entered.load();});
  const char* expected=managerBlock?"manager_callback":failure?"exception_finalizer":"finalizer";
  if(nonblocking){
    require(wrapper.Stop(false),"nonblocking stop rejected");
    checkRow("scripts.target_before_nonblocking_stop",inv->tid,expected,withAddon);
    require(!has("scripts.target_before_join"),"nonblocking stop mislabeled as join");
  }
  std::atomic<bool> finished{false};std::thread stopper([&]{wrapper.Stop(true);finished=true;});
  until([&]{return has("scripts.target_before_join");});
  const auto row=last("scripts.target_before_join");
  std::this_thread::sleep_for(15ms);const bool bypassed=finished.load();
  if(managerBlock)managerGate.open();else if(failure)inv->exception.open();else inv->finalizer.open();
  stopper.join();
  require(!bypassed,"diagnostic bypassed real join");checkRow("scripts.target_before_join",inv->tid,expected,withAddon);
  require(finished && inv->doneCount==1 && callbacks==1,"completion behavior changed");
  std::cout<<"PASS "<<name<<" target="<<row.target<<"\n";
}
static void activeExecution(){
  clearRows();auto inv=std::make_shared<Invoker>();inv->blockExecute=true;CScriptInvocationManager manager;
  CLanguageInvokerThread wrapper(inv,&manager,false);wrapper.SetId(42);wrapper.SetAddon(addon());
  wrapper.Execute("fixture.py");until([&]{return inv->execution.entered.load();});wrapper.Stop(true);
  checkRow("scripts.target_before_stop",inv->tid,"execute");
  require(inv->stopCount==1&&inv->doneCount==1,"active cancellation changed");
  std::cout<<"PASS active_execution_stop_unchanged\n";
}
static void atomicCoherence(){
  InfinityInvokerTarget target;using S=InfinityInvokerTarget::Stage;
  require(target.Read().tid==0&&target.Read().stage==S::NotStarted,"default state wrong");
  target.Mark(S::Execute);require(target.Read().tid==0,"invented target before start");
  std::atomic<bool> done{false};std::atomic<bool> bad{false};
  std::thread writer([&]{for(unsigned i=0;i<100000;++i){target.Start(101);target.Mark(S::Finalizer);target.Start(202);target.Mark(S::Execute);}done=true;});
  while(!done){const auto v=target.Read();if(v.tid==0)continue;
    if(v.tid==101&&v.stage!=S::Startup&&v.stage!=S::Finalizer)bad=true;
    if(v.tid==202&&v.stage!=S::Startup&&v.stage!=S::Execute)bad=true;
    if(v.tid!=101&&v.tid!=202)bad=true;
  }
  writer.join();require(!bad,"mixed tid/stage observation");
  require(std::string(InfinityInvokerTarget::Name(static_cast<S>(255)))=="unknown","unknown enum mislabeled");
  char buffer[65]{};const int n=std::snprintf(buffer,sizeof(buffer),"os_tid.%u.stage.%s",0xffffffffU,InfinityInvokerTarget::Name(S::ExceptionManagerCallback));
  require(n>0&&n<65,"diagnostic target would truncate");std::cout<<"PASS atomic_snapshot_and_format_bounds\n";
}
static void noThread(){
  clearRows();CScriptInvocationManager manager;CLanguageInvokerThread wrapper(nullptr,&manager,false);wrapper.SetId(42);
  require(!wrapper.Stop(true),"null invoker behavior changed");require(rows().empty(),"invented join target");
  std::cout<<"PASS null_invoker_no_fake_join\n";
}
int main(){try{
  atomicCoherence();noThread();activeExecution();
  stalled("finalizer_join_preserved",false,false,false,true);
  stalled("manager_callback_join_preserved",true,false,false,true);
  stalled("exception_finalizer_join_preserved",false,true,false,true);
  stalled("nonblocking_stop_distinguished",false,false,true,true);
  stalled("missing_addon_not_invented",false,false,false,false);
  std::cout<<"HOST TESTS ONLY: mocked Kodi/CPython boundaries, real host threads and joins.\n";return 0;
}catch(const std::exception& e){std::cerr<<"FAIL "<<e.what()<<"\n";return 1;}}
