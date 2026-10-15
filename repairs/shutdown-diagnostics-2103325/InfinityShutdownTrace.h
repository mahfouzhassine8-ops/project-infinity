/* SPDX-License-Identifier: GPL-2.0-or-later */
#pragma once
// Diagnostic-only: no Kodi locks, GIL calls, joins, cancellation, network or fsync.
// Linux CLOCK_BOOTTIME aligns with Android elapsedRealtimeNanos. Monotonic time
// is recorded separately for durations excluding device suspend. Scope return is
// NOT a success/clean-exit verdict. A final exit request is NOT proof of PID death.
#include <atomic>
#include <cerrno>
#include <cstdint>
#include <cstdio>
#include <cstring>
#include <exception>
#include <fcntl.h>
#include <sys/prctl.h>
#include <sys/syscall.h>
#include <time.h>
#include <unistd.h>

namespace InfinityShutdownTrace
{
constexpr unsigned MAX_EVENTS = 2048;
constexpr const char* ENGINE_TAG = "infinity-shutdown-2103325-v1";
inline char path[1024]{};
inline std::atomic<bool> configured{false};
inline std::atomic<bool> begun{false};
inline std::atomic<int> descriptor{-1};
inline std::atomic<unsigned> count{0};
inline std::atomic<unsigned long long> ids{0};
inline thread_local unsigned long long parentId{0};
inline long long originNs{0};
struct PreserveErrno { int value{errno}; ~PreserveErrno() noexcept { errno=value; } };
inline long long Clock(clockid_t clock) noexcept
{
  timespec ts{};
  if (::clock_gettime(clock,&ts)!=0) return 0;
  return static_cast<long long>(ts.tv_sec)*1000000000LL+static_cast<long long>(ts.tv_nsec);
}
inline void Token(const char* source,char* target,size_t capacity) noexcept
{
  if (!capacity) return;
  size_t i=0;
  if (source) for (;i+1<capacity && source[i];++i)
  {
    const char c=source[i];
    target[i]=((c>='a'&&c<='z')||(c>='A'&&c<='Z')||(c>='0'&&c<='9')||c=='.'||c=='_'||c=='-')?c:'_';
  }
  target[i]='\0';
}
inline void Configure(const char* root) noexcept
{
  PreserveErrno keep;
  if (configured.load() || !root || !*root) return;
  const int n=std::snprintf(path,sizeof(path),"%s/infinity-shutdown-native.jsonl",root);
  if (n<=0 || static_cast<size_t>(n)>=sizeof(path)) { path[0]='\0'; return; }
  configured.store(true,std::memory_order_release);
}
inline void Event(const char* kind,const char* phase,long long invoker=-1,
                  unsigned long long span=0,unsigned long long parent=0,
                  long long durationNs=0,const char* addon=nullptr,const char* outcome="observed",const char* target=nullptr) noexcept
{
  PreserveErrno keep;
  const int fd=descriptor.load(std::memory_order_acquire);
  if (fd<0) return;
  const unsigned serial=count.fetch_add(1,std::memory_order_relaxed);
  if (serial>MAX_EVENTS) return;
  const long long boot=Clock(CLOCK_BOOTTIME), mono=Clock(CLOCK_MONOTONIC);
  const long long epoch=Clock(CLOCK_REALTIME);
  char threadName[16]{},safeThread[16]{},safeAddon[97]{},safePhase[81]{},safeTarget[65]{};
  // PR_GET_NAME reads this thread without the API-26-only pthread getter.
  // Keep the locked Android API-21 native baseline; names remain best effort.
  const int named=::prctl(PR_GET_NAME,threadName,0UL,0UL,0UL); (void)named;
  Token(threadName,safeThread,sizeof(safeThread)); Token(addon,safeAddon,sizeof(safeAddon));
  Token(phase,safePhase,sizeof(safePhase)); Token(target,safeTarget,sizeof(safeTarget));
  if (serial==MAX_EVENTS) {kind="limit"; std::strcpy(safePhase,"capture.event_limit");outcome="truncated";}
  char row[1024]{};
  const int n=std::snprintf(row,sizeof(row),
    "{\"schema\":1,\"engine\":\"%s\",\"session_start_ns\":%lld,\"seq\":%u,\"pid\":%ld,\"tid\":%ld,\"thread\":\"%s\",\"boot_ns\":%lld,\"monotonic_ns\":%lld,\"epoch_ns\":%lld,\"kind\":\"%s\",\"phase\":\"%s\",\"invoker_id\":%lld,\"addon_id\":\"%s\",\"span_id\":%llu,\"parent_span_id\":%llu,\"duration_ns\":%lld,\"outcome\":\"%s\",\"target_thread\":\"%s\"}\n",
    ENGINE_TAG,originNs,serial,static_cast<long>(::getpid()),static_cast<long>(::syscall(SYS_gettid)),
    safeThread,boot,mono,epoch,kind,safePhase,invoker,safeAddon,span,parent,durationNs,outcome,safeTarget);
  // One bounded append per event. Do not retry partial/EINTR writes and risk
  // making evidence collection an unbounded teardown wait. Parser flags gaps.
  if(n>0 && static_cast<size_t>(n)<sizeof(row)) { const auto ignored=::write(fd,row,static_cast<size_t>(n)); (void)ignored; }
}
inline void Begin() noexcept
{
  PreserveErrno keep;
  if (!configured.load(std::memory_order_acquire)) return;
  bool expected=false;
  if (!begun.compare_exchange_strong(expected,true)) return;
  char previous[1056]{};
  const int n=std::snprintf(previous,sizeof(previous),"%s.previous",path);
  if (n>0 && static_cast<size_t>(n)<sizeof(previous)) { const auto ignored=::rename(path,previous); (void)ignored; }
  originNs=Clock(CLOCK_BOOTTIME);
  const int fd=::open(path,O_WRONLY|O_CREAT|O_TRUNC|O_APPEND|O_CLOEXEC,0600);
  descriptor.store(fd,std::memory_order_release);
  Event("milestone","capture.begin");
}
class Scope
{
public:
  explicit Scope(const char* phase,long long invoker=-1,const char* addon=nullptr,const char* target=nullptr) noexcept
    : m_phase(phase),m_invoker(invoker),m_addon(addon),m_target(target)
  {
    PreserveErrno keep;
    if (descriptor.load(std::memory_order_acquire)<0) return;
    m_active=true; m_id=ids.fetch_add(1)+1; m_parent=parentId; parentId=m_id;
    m_start=Clock(CLOCK_MONOTONIC);m_exceptions=std::uncaught_exceptions();
    Event("begin",m_phase,m_invoker,m_id,m_parent,0,m_addon,"observed",m_target);
  }
  Scope(const Scope&)=delete;
  Scope& operator=(const Scope&)=delete;
  ~Scope() noexcept { End(); }
  void End() noexcept
  {
    PreserveErrno keep;
    if (!m_active) return;
    m_active=false;
    Event("end",m_phase,m_invoker,m_id,m_parent,Clock(CLOCK_MONOTONIC)-m_start,m_addon,
          std::uncaught_exceptions()>m_exceptions?"scope_unwound":"scope_returned",m_target);
    if(parentId==m_id) parentId=m_parent;
  }
private:
  const char* m_phase;
  long long m_invoker;
  const char* m_addon;
  const char* m_target;
  bool m_active{false};
  unsigned long long m_id{0},m_parent{0};
  long long m_start{0};
  int m_exceptions{0};
};
}
