/* SPDX-License-Identifier: GPL-2.0-or-later */
#pragma once
// Internal QA observations only. No admission, retry, save or lifecycle authority.
#include <cstdint>
namespace InfinityStartupTrace
{
enum class Stage : unsigned {
  RequestBegin, RequestEnd, BuiltinResolve, BuiltinResolved, BuiltinResult,
  LookupWait, LookupLocked, DispatchWait, DispatchLocked,
  EmptyScript, MissingScript, NullInvoker, ShutdownClosed, StartupClosed,
  MissingHandler, Quarantined, FreshDispatch, ReusedDispatch,
  StartupGateClosed, ShutdownGateClosed, ExecuteEnter, ExecuteMissing,
  HandlerBegin, HandlerRejected, HandlerReady, RuntimeWait, RuntimeLocked,
  RuntimeInitialize, RuntimeInitialized, RuntimeReused, MainStateMissing,
  ThreadStateFailed, GilWait, GilAcquired, InterpreterCreate, InterpreterCreated,
  InterpreterFailed, RestoreGilWait, RestoreGilAcquired, KodiInitialize,
  KodiInitialized, ObserverBegin, ObserverReturned, BytecodeEnter, BytecodeReturned,
  BytecodeException, StoppingBeforeBytecode, ExecutionFinished, CheckpointGateClosed, Overflow
};
struct Event {
  uint64_t request{0}, monotonicUs{0};
  long tid{0}; int invoker{-1}, value{0}; unsigned flags{0}, tracked{0};
  Stage stage{Stage::RequestBegin};
};
inline const char* Name(Stage s) noexcept {
  static constexpr const char* names[]={
    "request.begin","request.end","builtin.resolve","builtin.resolved","builtin.result",
    "lookup.wait","lookup.locked","dispatch.wait","dispatch.locked",
    "refused.empty_script","refused.missing_script","refused.null_invoker","refused.shutdown",
    "refused.startup_gate","refused.missing_handler","refused.quarantine","dispatch.fresh","dispatch.reused",
    "gate.startup_closed","gate.shutdown_closed","execute.enter","execute.missing_script",
    "handler.begin","handler.rejected","handler.ready","runtime.wait","runtime.locked",
    "runtime.initialize","runtime.initialized","runtime.reused","interpreter.main_state_missing",
    "interpreter.thread_state_failed","gil.wait","gil.acquired","interpreter.create","interpreter.created",
    "interpreter.failed","gil.restore_wait","gil.restore_acquired","kodi.initialize","kodi.initialized",
    "observer.begin","observer.returned","bytecode.enter","bytecode.returned","bytecode.exception",
    "bytecode.cancelled_before_entry","execution.finished","gate.checkpoint_closed","trace.overflow"};
  const unsigned index=static_cast<unsigned>(s);
  return index<sizeof(names)/sizeof(names[0])?names[index]:"invalid";
}
}

#if defined(INFINITY_STARTUP_TRACE_QA)
#include <array>
#include <atomic>
#include <cerrno>
#include <chrono>
#include <cstring>
#include <fcntl.h>
#include <sys/syscall.h>
#include <unistd.h>
namespace InfinityStartupTrace
{
constexpr unsigned CAPACITY=8192;
constexpr unsigned DRAIN_BATCH=32;
struct Slot { Event event; std::atomic<bool> ready{false}; };
inline std::array<Slot,CAPACITY> slots;
inline std::atomic<unsigned> next{0}, dropped{0};
inline std::atomic<uint64_t> serial{0};
inline std::atomic_flag draining=ATOMIC_FLAG_INIT;
inline unsigned drained=0, reportedDropped=0;
inline thread_local uint64_t request=0;
#if defined(INFINITY_STARTUP_TRACE_HOST)
inline bool hostInfinity=false; // Host fixture only; not present in Android.
#endif
inline uint64_t Now() noexcept {
  return std::chrono::duration_cast<std::chrono::microseconds>(
      std::chrono::steady_clock::now().time_since_epoch()).count();
}
inline bool InfinityProcess() noexcept {
#if defined(INFINITY_STARTUP_TRACE_HOST)
  return hostInfinity;
#elif defined(TARGET_ANDROID)
  // Process identity, not skin/foreground/checkpoint state. No profile reads.
  static const bool owned=[] {
    const int saved=errno;
    char name[80]{};
    const int fd=::open("/proc/self/cmdline",O_RDONLY|O_CLOEXEC);
    const auto size=fd<0 ? -1 : ::read(fd,name,sizeof(name)-1);
    if(fd>=0)::close(fd);
    const bool result=size>0 && std::strcmp(name,"com.projectinfinity.kodi:kodi")==0;
    errno=saved;return result;
  }();
  return owned;
#else
  return false;
#endif
}
inline bool Enabled() noexcept {
  if(!InfinityProcess())return false;
  static const uint64_t started=Now();
  return Now()-started<1200000000ULL; // finite twenty-minute QA capture
}
inline void Record(Stage stage,int invoker=-1,int value=0,unsigned flags=0,unsigned tracked=0) noexcept {
  if(!Enabled())return;
  const unsigned index=next.fetch_add(1,std::memory_order_relaxed);
  if(index>=CAPACITY){dropped.fetch_add(1,std::memory_order_relaxed);return;}
  const int saved=errno;
  auto& slot=slots[index];
  slot.event={request,Now(),static_cast<long>(::syscall(SYS_gettid)),invoker,value,flags,tracked,stage};
  slot.ready.store(true,std::memory_order_release);
  errno=saved;
}
class Request {
  uint64_t previous{0}; bool owns{false};
public:
  Request() noexcept {
    if(!Enabled())return;
    previous=request;owns=previous==0;
    if(owns){request=serial.fetch_add(1,std::memory_order_relaxed)+1;Record(Stage::RequestBegin);}
  }
  ~Request(){if(owns){Record(Stage::RequestEnd);request=previous;}}
};
// Drain only outside application/Python/manager locks, through the normal native
// log sink. No producer mutex, Python GIL or filesystem write is acquired here.
template<class Sink> inline void Drain(Sink sink) noexcept {
  if(!InfinityProcess() || draining.test_and_set(std::memory_order_acquire))return;
  const int saved=errno;
  try {
    const auto end=drained+DRAIN_BATCH;
    for(unsigned i=drained;i<CAPACITY && i<end && i<next.load(std::memory_order_relaxed);++i) {
      if(!slots[i].ready.load(std::memory_order_acquire))break;
      sink(slots[i].event);drained=i+1;
    }
    const auto overflow=dropped.load(std::memory_order_relaxed);
    if(overflow!=reportedDropped){Event e;e.stage=Stage::Overflow;e.value=static_cast<int>(overflow);sink(e);reportedDropped=overflow;}
  }catch(...){/* A diagnostic sink never alters execution. */}
  errno=saved;draining.clear(std::memory_order_release);
}
}
#else
namespace InfinityStartupTrace
{
inline bool Enabled() noexcept{return false;}
inline void Record(Stage,int=-1,int=0,unsigned=0,unsigned=0) noexcept{}
class Request {public: Request() noexcept{} ~Request() noexcept{}};
template<class Sink> inline void Drain(Sink) noexcept{}
}
#endif
