/* SPDX-License-Identifier: GPL-2.0-or-later */
#pragma once
// Diagnostic-only: no Kodi locks, GIL calls, joins, cancellation, network or fsync.
// Linux CLOCK_BOOTTIME aligns with Android elapsedRealtimeNanos. Monotonic time
// is recorded separately for durations excluding device suspend. Scope return is
// NOT a success/clean-exit verdict. A final exit request is NOT proof of PID death.
#include <atomic>
#include <array>
#include <limits>
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
constexpr unsigned MAX_EVENTS = 8192;
constexpr const char* ENGINE_TAG = "infinity-checkpoint-cancelled-script-2103369-v1";
inline char path[1024]{};
inline std::atomic<bool> configured{false};
inline std::atomic<bool> begun{false};
inline std::atomic<int> descriptor{-1};
inline std::atomic<int> criticalDescriptor{-1};
inline std::atomic<unsigned> criticalCount{0};
constexpr unsigned MAX_CRITICAL_EVENTS = 1024;
inline bool Critical(const char* phase) noexcept
{
  // A separate budget: per-invoker/thread traffic cannot hide the final phase.
  return phase && (std::strncmp(phase,"application.",12)==0 ||
      std::strncmp(phase,"android.",8)==0 || std::strncmp(phase,"stop.",5)==0 ||
      std::strncmp(phase,"pre.",4)==0 || std::strncmp(phase,"cleanup.",8)==0 ||
      std::strncmp(phase,"scripts.",8)==0 || std::strncmp(phase,"services.",9)==0 ||
      std::strncmp(phase,"python.runtime",14)==0 || std::strcmp(phase,"python.exit_frame")==0 ||
      std::strcmp(phase,"python.bytecode_returned")==0 || std::strcmp(phase,"python.child_thread_wait")==0 || std::strncmp(phase,"process.",8)==0 ||
      std::strncmp(phase,"capture.",8)==0 || std::strncmp(phase,"checkpoint.",11)==0 || std::strncmp(phase,"jobs.",5)==0 || std::strncmp(phase,"directory.",10)==0);
}
struct OperationMetadata
{
  unsigned long long id,parent,generation;
  long long startedMonotonicNs,stageStartedMonotonicNs,endedMonotonicNs,workerTid;
  const char* backend;const char* stage;const char* scheme;const char* kind;
  const char* cancellationSupport;
  unsigned cancelObserved,cancelOutcomes,identityVerified;
  unsigned long long subjectExecutionId;
  long long subjectStartedMonotonicNs,subjectWorkerTid;
  const char* ownerKind;
  long long checkpointObservedMonotonicNs{0};
};
// The existing exporter copies the first 2 MiB of this file. Bound the
// complete critical stream below that cap, with independent byte allowances.
// Detailed events and fast SQLite traffic cannot consume terminal lanes.
inline long long originNs{0};
enum class EvidenceLane : unsigned { Checkpoint, Cancellation, Retirement, Initial, NativeReturn, Legacy, Detail };
constexpr unsigned LANE_BYTES[]={320*1024,256*1024,512*1024,128*1024,128*1024,448*1024};
inline std::array<std::atomic<unsigned>,6> retainedBytes{};
inline std::array<std::atomic<unsigned>,6> droppedRows{};
inline std::array<std::atomic<bool>,6> laneLimitReported{};
inline std::atomic<unsigned> vfsCount{0};
inline EvidenceLane Lane(const char* phase) noexcept
{
  if(!phase)return EvidenceLane::Detail;
  if(std::strncmp(phase,"vfs.checkpoint.",15)==0 ||
     std::strncmp(phase,"checkpoint.",11)==0 ||
     std::strcmp(phase,"vfs.diagnostic.fast_scope_summary")==0)
    return EvidenceLane::Checkpoint;
  if(std::strncmp(phase,"vfs.backend.cancel",18)==0 ||
     std::strncmp(phase,"vfs.backend.callback",20)==0)
    return EvidenceLane::Cancellation;
  if(std::strcmp(phase,"vfs.python.active_invoker")==0 ||
     std::strcmp(phase,"vfs.shutdown.request")==0 ||
     std::strcmp(phase,"vfs.native.scope_pending")==0)
    return EvidenceLane::Initial;
  if(std::strncmp(phase,"vfs.python.",11)==0 ||
     std::strcmp(phase,"vfs.shutdown_operation_return")==0)
    return EvidenceLane::Retirement;
  if(std::strcmp(phase,"vfs.blocking_operation_return")==0 ||
     std::strcmp(phase,"vfs.native.scope_return")==0)
    return EvidenceLane::NativeReturn;
  if(Critical(phase) || std::strncmp(phase,"vfs.snapshot",12)==0 ||
     std::strncmp(phase,"vfs.history",11)==0 || std::strncmp(phase,"vfs.capture",11)==0)
    return EvidenceLane::Legacy;
  return EvidenceLane::Detail;
}
inline bool ReserveCritical(EvidenceLane lane,unsigned bytes) noexcept
{
  const auto i=static_cast<unsigned>(lane);
  if(i>=6)return false;
  auto prior=retainedBytes[i].load();
  for(unsigned attempt=0;attempt<8;++attempt)
  {
    if(prior>LANE_BYTES[i] || bytes>LANE_BYTES[i]-prior)break;
    if(retainedBytes[i].compare_exchange_weak(prior,prior+bytes))return true;
  }
  droppedRows[i].fetch_add(1);
  // Exactly one fixed-size loss marker per lane; it cannot recurse through Event.
  if(!laneLimitReported[i].exchange(true))
  {
    char row[256]{};
    const int n=std::snprintf(row,sizeof(row),
      "{\"schema\":1,\"kind\":\"limit\",\"phase\":\"capture.lane_limit\",\"pid\":%ld,\"session_start_ns\":%lld,\"lane\":%u,\"outcome\":\"evidence_incomplete\"}\n",
      static_cast<long>(::getpid()),originNs,i);
    const int fd=criticalDescriptor.load();
    if(fd>=0 && n>0 && static_cast<unsigned>(n)<sizeof(row))
    {const auto ignored=::write(fd,row,n);(void)ignored;}
  }
  return false;
}
constexpr unsigned MAX_VFS_EVENTS=4096;
inline std::atomic<unsigned> count{0};
inline std::atomic<unsigned long long> ids{0};
inline thread_local unsigned long long parentId{0};

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
                  long long durationNs=0,const char* addon=nullptr,const char* outcome="observed",const char* target=nullptr,
                  const OperationMetadata* operation=nullptr) noexcept
{
  PreserveErrno keep;
  const int fd=descriptor.load(std::memory_order_acquire);
  if (fd<0) return;
  const unsigned serial=count.fetch_add(1,std::memory_order_relaxed);
  const bool critical=Critical(phase);
  const unsigned criticalSerial=critical ? criticalCount.fetch_add(1,std::memory_order_relaxed) : MAX_CRITICAL_EVENTS+1;
  const bool vfs=phase && std::strncmp(phase,"vfs.",4)==0;
  const unsigned vfsSerial=vfs?vfsCount.fetch_add(1):MAX_VFS_EVENTS+1;
  const auto lane=Lane(phase);
  const bool reserved=lane!=EvidenceLane::Detail;
  if (serial>MAX_EVENTS && criticalSerial>MAX_CRITICAL_EVENTS && vfsSerial>MAX_VFS_EVENTS && !reserved) return;
  const long long boot=Clock(CLOCK_BOOTTIME), mono=Clock(CLOCK_MONOTONIC);
  const long long epoch=Clock(CLOCK_REALTIME);
  char threadName[16]{},safeThread[16]{},safeAddon[97]{},safePhase[81]{},safeTarget[65]{};
  // PR_GET_NAME reads this thread without the API-26-only pthread getter.
  // Keep the locked Android API-21 native baseline; names remain best effort.
  const int named=::prctl(PR_GET_NAME,threadName,0UL,0UL,0UL); (void)named;
  Token(threadName,safeThread,sizeof(safeThread)); Token(addon,safeAddon,sizeof(safeAddon));
  Token(phase,safePhase,sizeof(safePhase)); Token(target,safeTarget,sizeof(safeTarget));

  char extension[1200]{};
  if(operation)
  {
    char backend[33]{},stage[41]{},scheme[17]{},op[33]{},support[49]{},ownerKind[33]{};
    Token(operation->backend,backend,sizeof(backend));Token(operation->stage,stage,sizeof(stage));
    Token(operation->scheme,scheme,sizeof(scheme));Token(operation->kind,op,sizeof(op));
    Token(operation->cancellationSupport,support,sizeof(support));
    Token(operation->ownerKind,ownerKind,sizeof(ownerKind));
    const auto ignored=std::snprintf(extension,sizeof(extension),
      ",\"operation_id\":%llu,\"operation_parent_id\":%llu,\"checkpoint_generation\":%llu,\"operation_start_monotonic_ns\":%lld,\"stage_start_monotonic_ns\":%lld,\"operation_end_monotonic_ns\":%lld,\"operation_worker_tid\":%lld,\"backend_category\":\"%s\",\"backend_identity_observed\":%u,\"operation_kind\":\"%s\",\"operation_stage\":\"%s\",\"resource_category\":\"%s\",\"cancellation_support\":\"%s\",\"backend_cancel_callback_observed\":%u,\"cancellation_outcome_bits\":%u,\"subject_execution_id\":%llu,\"subject_start_monotonic_ns\":%lld,\"subject_worker_tid\":%lld,\"owner_kind\":\"%s\",\"checkpoint_outcome_observed_monotonic_ns\":%lld",
      operation->id,operation->parent,operation->generation,operation->startedMonotonicNs,
      operation->stageStartedMonotonicNs,operation->endedMonotonicNs,operation->workerTid,
      backend,operation->identityVerified,op,stage,scheme,support,operation->cancelObserved,operation->cancelOutcomes,
      operation->subjectExecutionId,operation->subjectStartedMonotonicNs,operation->subjectWorkerTid,ownerKind,
      operation->checkpointObservedMonotonicNs);
    (void)ignored;
  }
  char row[2304]{};
  const int n=std::snprintf(row,sizeof(row),
    "{\"schema\":1,\"engine\":\"%s\",\"session_start_ns\":%lld,\"seq\":%u,\"pid\":%ld,\"tid\":%ld,\"thread\":\"%s\",\"boot_ns\":%lld,\"monotonic_ns\":%lld,\"epoch_ns\":%lld,\"kind\":\"%s\",\"phase\":\"%s\",\"invoker_id\":%lld,\"addon_id\":\"%s\",\"span_id\":%llu,\"parent_span_id\":%llu,\"duration_ns\":%lld,\"outcome\":\"%s\",\"target_thread\":\"%s\"%s}\n",
    ENGINE_TAG,originNs,serial,static_cast<long>(::getpid()),static_cast<long>(::syscall(SYS_gettid)),
    safeThread,boot,mono,epoch,kind,safePhase,invoker,safeAddon,span,parent,durationNs,outcome,safeTarget,extension);
  // One bounded append per event. Do not retry partial/EINTR writes and risk
  // making evidence collection an unbounded teardown wait. Parser flags gaps.
  if(n>0 && static_cast<size_t>(n)<sizeof(row))
  {
    const int criticalFd=criticalDescriptor.load(std::memory_order_acquire);
    if (reserved && criticalFd>=0 && ReserveCritical(lane,static_cast<unsigned>(n)))
    { const auto ignored=::write(criticalFd,row,static_cast<size_t>(n)); (void)ignored; }
    if (serial<MAX_EVENTS)
    { const auto ignored=::write(fd,row,static_cast<size_t>(n)); (void)ignored; }
  }
  if (serial==MAX_EVENTS || (critical && criticalSerial==MAX_CRITICAL_EVENTS) || (vfs && vfsSerial==MAX_VFS_EVENTS))
  {
    char limit[256]{};
    const int size=std::snprintf(limit,sizeof(limit),
      "{\"schema\":1,\"kind\":\"limit\",\"phase\":\"capture.event_limit\",\"pid\":%ld,\"session_start_ns\":%lld,\"boot_ns\":%lld,\"seq\":%u,\"outcome\":\"truncated\"}\n",
      static_cast<long>(::getpid()),originNs,boot,serial);
    const int output=serial==MAX_EVENTS ? fd : criticalDescriptor.load();
    if(size>0 && static_cast<size_t>(size)<sizeof(limit) && output>=0)
    { const auto ignored=::write(output,limit,static_cast<size_t>(size)); (void)ignored; }
  }
}
struct NativeScopeRecord
{
  std::atomic<unsigned long long> id{0},parent{0};
  std::atomic<long long> started{0},invoker{-1},tid{0};
  std::array<std::atomic<char>,81> phase{};
  std::atomic<bool> captured{false};
};
inline std::array<NativeScopeRecord,128> nativeScopes;
constexpr const char* FAST_SCOPE_PHASES[]={"sqlite.close","sqlite.commit","sqlite.rollback",
  "database.close","database.commit","database.rollback"};
struct FastScopeAggregate {std::atomic<unsigned long long> calls{0},nanoseconds{0};};
inline std::array<FastScopeAggregate,6> fastScopes;
inline int FastScopeIndex(const char* phase) noexcept
{
  if(!phase)return -1;
  for(unsigned i=0;i<6;++i)if(std::strcmp(phase,FAST_SCOPE_PHASES[i])==0)return i;
  return -1;
}
inline void RecordFastScope(int index,long long duration) noexcept
{
  if(index<0)return;
  fastScopes[index].calls.fetch_add(1);
  fastScopes[index].nanoseconds.fetch_add(duration>0?duration:0);
}
inline void FastScopeSummary() noexcept
{
  for(unsigned i=0;i<6;++i)
  {
    const auto calls=fastScopes[i].calls.load();
    if(!calls)continue;
    char outcome[128]{};
    const auto ignored=std::snprintf(outcome,sizeof(outcome),"completed_calls_%llu_total_ns_%llu",
      calls,fastScopes[i].nanoseconds.load());(void)ignored;
    Event("milestone","vfs.diagnostic.fast_scope_summary",-1,0,0,0,nullptr,outcome,FAST_SCOPE_PHASES[i]);
  }
}
inline void NativeScopeEvent(unsigned long long id,unsigned long long parent,
  long long start,long long end,long long invoker,long long tid,const char* phase,
  const char* outcome) noexcept
{
  OperationMetadata m{id,parent,0,start,start,end,tid,
    std::strncmp(phase,"sqlite.",7)==0?"sqlite":
    std::strncmp(phase,"python.",7)==0?"python_runtime":"native_backend_unobserved",
    "native_scope","other","native_scope","unobservable",0,0,0,0,0,0,"native_scope"};
  Event("milestone",end?"vfs.native.scope_return":"vfs.native.scope_pending",
    invoker,id,parent,Clock(CLOCK_MONOTONIC)-start,nullptr,outcome,phase,&m);
}
inline void NativeScopeSnapshots() noexcept
{
  for(auto& r:nativeScopes)
  {
    const auto id=r.id.load(std::memory_order_acquire);
    if(!id || id==std::numeric_limits<unsigned long long>::max())continue;
    char phase[81]{};
    for(unsigned i=0;i<80;++i)phase[i]=r.phase[i].load();
    const auto parent=r.parent.load();const auto start=r.started.load();
    const auto invoker=r.invoker.load(),tid=r.tid.load();
    if(id==r.id.load(std::memory_order_acquire))
    {
      r.captured.store(true);
      if(id==r.id.load(std::memory_order_acquire))
        NativeScopeEvent(id,parent,start,0,invoker,tid,phase,"active_at_capture_begin");
    }
    else Event("milestone","vfs.snapshot_gap",-1,0,0,0,nullptr,"native_scope_snapshot_changed");
  }
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
  // Preserve an independently bounded high-level timeline and its prior run.
  char criticalPath[1056]{},criticalPrevious[1080]{};
  const int cn=std::snprintf(criticalPath,sizeof(criticalPath),"%s.critical",path);
  const int pn=std::snprintf(criticalPrevious,sizeof(criticalPrevious),"%s.previous",criticalPath);
  if(cn>0 && pn>0 && static_cast<size_t>(cn)<sizeof(criticalPath) && static_cast<size_t>(pn)<sizeof(criticalPrevious))
  {
    const auto ignored=::rename(criticalPath,criticalPrevious); (void)ignored;
    criticalDescriptor.store(::open(criticalPath,O_WRONLY|O_CREAT|O_TRUNC|O_APPEND|O_CLOEXEC,0600),std::memory_order_release);
  }
  descriptor.store(fd,std::memory_order_release);
  Event("milestone","capture.begin");
  NativeScopeSnapshots();
}
class Scope
{
public:
  explicit Scope(const char* phase,long long invoker=-1,const char* addon=nullptr,const char* target=nullptr) noexcept
    : m_phase(phase),m_invoker(invoker),m_addon(addon),m_target(target)
  {
    PreserveErrno keep;
    // Retain active native scopes before Close; append no evidence until Begin.

    m_active=true; m_id=ids.fetch_add(1)+1; m_parent=parentId; parentId=m_id;
    m_start=Clock(CLOCK_MONOTONIC);m_exceptions=std::uncaught_exceptions();
    m_tid=static_cast<long long>(::syscall(SYS_gettid));
    for(auto& r:nativeScopes)
    {
      unsigned long long empty=0;
      if(!r.id.compare_exchange_strong(empty,std::numeric_limits<unsigned long long>::max()))continue;
      m_record=&r;char phase[81]{};Token(m_phase,phase,sizeof(phase));
      for(unsigned i=0;i<81;++i)r.phase[i].store(phase[i]);
      r.parent.store(m_parent);r.started.store(m_start);r.invoker.store(m_invoker);r.tid.store(m_tid);r.captured.store(false);
      r.id.store(m_id,std::memory_order_release);break;
    }
    if(!m_record)Event("milestone","vfs.capture_limit",m_invoker,0,0,0,nullptr,"native_scope_capacity_exhausted");

    m_fast=FastScopeIndex(m_phase);
    if(m_fast<0)Event("begin",m_phase,m_invoker,m_id,m_parent,0,m_addon,"observed",m_target);
  }
  Scope(const Scope&)=delete;
  Scope& operator=(const Scope&)=delete;
  ~Scope() noexcept { End(); }
  void End() noexcept
  {
    PreserveErrno keep;
    if (!m_active) return;
    m_active=false;
    const auto end=Clock(CLOCK_MONOTONIC),duration=end-m_start;
    const bool unwound=std::uncaught_exceptions()>m_exceptions;
    const bool captured=m_record && m_record->captured.load();
    if(m_fast>=0 && duration<1000000 && !unwound && !captured)
      RecordFastScope(m_fast,duration);
    else
    {
      Event("end",m_phase,m_invoker,m_id,m_parent,duration,m_addon,
            unwound?"scope_unwound":"scope_returned",m_target);
      NativeScopeEvent(m_id,m_parent,m_start,end,m_invoker,m_tid,m_phase,
        unwound?"scope_unwound_not_success":"scope_returned_not_success");
    }
    if(m_record)m_record->id.store(0,std::memory_order_release);
    if(parentId==m_id) parentId=m_parent;
  }
private:
  const char* m_phase;
  long long m_invoker;
  const char* m_addon;
  const char* m_target;
  bool m_active{false};
  unsigned long long m_id{0},m_parent{0};
  int m_fast{-1};
  NativeScopeRecord* m_record{nullptr};
  long long m_tid{0};
  long long m_start{0};
  int m_exceptions{0};
};
}
