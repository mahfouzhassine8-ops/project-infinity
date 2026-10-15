"""Bound diagnostic traffic while reserving independent terminal evidence."""

def once(s,old,new):
    if s.count(old)!=1:raise ValueError('Retention anchor mismatch '+repr(old[:100]))
    return s.replace(old,new,1)

def apply(s):
    s=once(s,'inline long long originNs{0};','')
    s=once(s,'inline std::atomic<unsigned> vfsCount{0};',"""// The existing exporter copies the first 2 MiB of this file. Bound the
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
      "{\\\"schema\\\":1,\\\"kind\\\":\\\"limit\\\",\\\"phase\\\":\\\"capture.lane_limit\\\",\\\"pid\\\":%ld,\\\"session_start_ns\\\":%lld,\\\"lane\\\":%u,\\\"outcome\\\":\\\"evidence_incomplete\\\"}\\n",
      static_cast<long>(::getpid()),originNs,i);
    const int fd=criticalDescriptor.load();
    if(fd>=0 && n>0 && static_cast<unsigned>(n)<sizeof(row))
    {const auto ignored=::write(fd,row,n);(void)ignored;}
  }
  return false;
}""")
    s=once(s,'  if (serial>MAX_EVENTS && criticalSerial>MAX_CRITICAL_EVENTS && vfsSerial>MAX_VFS_EVENTS) return;',
      '''  const auto lane=Lane(phase);
  const bool reserved=lane!=EvidenceLane::Detail;
  if (serial>MAX_EVENTS && criticalSerial>MAX_CRITICAL_EVENTS && vfsSerial>MAX_VFS_EVENTS && !reserved) return;''')
    s=once(s,'if (((critical && criticalSerial<MAX_CRITICAL_EVENTS) || (vfs && vfsSerial<MAX_VFS_EVENTS)) && criticalFd>=0)',
      'if (reserved && criticalFd>=0 && ReserveCritical(lane,static_cast<unsigned>(n)))')
    # Preserve the original first main-stream limit marker, but do not repeat
    # old critical limits now that byte reservations, rather than noisy row
    # counts, govern terminal capture. The legacy host fixture still sees limits.
    s=once(s,'    const int output=serial==MAX_EVENTS ? fd : criticalDescriptor.load();',
      '    const int output=serial==MAX_EVENTS ? fd : criticalDescriptor.load();')
    s=once(s,'  std::array<std::atomic<char>,81> phase{};',
      '  std::array<std::atomic<char>,81> phase{};\n  std::atomic<bool> captured{false};')
    s=once(s,'inline std::array<NativeScopeRecord,128> nativeScopes;',"""inline std::array<NativeScopeRecord,128> nativeScopes;
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
}""")
    s=once(s,'    if(id==r.id.load(std::memory_order_acquire))\n      NativeScopeEvent(id,parent,start,0,invoker,tid,phase,"active_at_capture_begin");',
      '''    if(id==r.id.load(std::memory_order_acquire))
    {
      r.captured.store(true);
      if(id==r.id.load(std::memory_order_acquire))
        NativeScopeEvent(id,parent,start,0,invoker,tid,phase,"active_at_capture_begin");
    }''')
    s=once(s,'      r.parent.store(m_parent);r.started.store(m_start);r.invoker.store(m_invoker);r.tid.store(m_tid);',
      '      r.parent.store(m_parent);r.started.store(m_start);r.invoker.store(m_invoker);r.tid.store(m_tid);r.captured.store(false);')
    s=once(s,'    Event("begin",m_phase,m_invoker,m_id,m_parent,0,m_addon,"observed",m_target);',
      '''    m_fast=FastScopeIndex(m_phase);
    if(m_fast<0)Event("begin",m_phase,m_invoker,m_id,m_parent,0,m_addon,"observed",m_target);''')
    s=once(s,'''    Event("end",m_phase,m_invoker,m_id,m_parent,Clock(CLOCK_MONOTONIC)-m_start,m_addon,
          std::uncaught_exceptions()>m_exceptions?"scope_unwound":"scope_returned",m_target);
    NativeScopeEvent(m_id,m_parent,m_start,Clock(CLOCK_MONOTONIC),m_invoker,m_tid,m_phase,
      std::uncaught_exceptions()>m_exceptions?"scope_unwound_not_success":"scope_returned_not_success");''',
      '''    const auto end=Clock(CLOCK_MONOTONIC),duration=end-m_start;
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
    }''')
    s=once(s,'  NativeScopeRecord* m_record{nullptr};','  int m_fast{-1};\n  NativeScopeRecord* m_record{nullptr};')
    return s
