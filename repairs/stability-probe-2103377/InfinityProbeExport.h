#pragma once
#include "threads/InfinityStabilityProbe.h"
#include "platform/android/activity/InfinityShutdownTrace.h"

// A separate allowance within the existing exporter's spare 256 KiB margin.
// Never debit or resize any of the six approved shutdown evidence lanes.
namespace InfinityProbeExport
{
constexpr unsigned MIRROR_BYTES=120*1024;
static_assert(InfinityShutdownTrace::LANE_BYTES[0]+InfinityShutdownTrace::LANE_BYTES[1]+
    InfinityShutdownTrace::LANE_BYTES[2]+InfinityShutdownTrace::LANE_BYTES[3]+
    InfinityShutdownTrace::LANE_BYTES[4]+InfinityShutdownTrace::LANE_BYTES[5]+128*1024 < 2*1024*1024,
    "Probe must fit below the existing 2 MiB export cap without changing approved lanes");
inline std::atomic_flag busy=ATOMIC_FLAG_INIT;
inline bool replayed=false,limitReported=false;
inline unsigned retained=0;
inline void Incomplete(int fd,const char* reason) noexcept
{
  if(limitReported)return;limitReported=true;
  char row[300]{};
  const int n=std::snprintf(row,sizeof(row),
      "{\"schema\":1,\"kind\":\"limit\",\"phase\":\"stability.export_incomplete\",\"pid\":%ld,\"observational_only\":true,\"reason\":\"%s\"}\n",
      static_cast<long>(::getpid()),reason);
  if(n>0 && static_cast<unsigned>(n)<sizeof(row)){const auto ignored=::write(fd,row,n);(void)ignored;}
}
inline void Append(int fd,const std::string& raw)
{
  if(raw.empty() || raw[0]!='{')return;
  std::string row=raw;
  if(!row.empty() && row.back()=='\n')row.pop_back();
  if(row.empty() || row.back()!='}'){Incomplete(fd,"partial_primary_row");return;}
  row.insert(1,"\"engine\":"+InfinityStabilityProbe::Quote(InfinityShutdownTrace::ENGINE_TAG)+
      ",\"session_start_ns\":"+std::to_string(InfinityShutdownTrace::originNs)+
      ",\"phase\":\"stability.observation\",\"observational_only\":true,\"checkpoint_authority\":false,");
  row+='\n';
  if(retained>MIRROR_BYTES || row.size()>MIRROR_BYTES-retained){Incomplete(fd,"probe_mirror_budget");return;}
  retained+=row.size();const auto n=::write(fd,row.data(),row.size());
  if(n!=static_cast<ssize_t>(row.size()))Incomplete(fd,"partial_mirror_write");
}
inline void Mirror(const std::string& latest) noexcept
{
  InfinityShutdownTrace::PreserveErrno keep;
  const int destination=InfinityShutdownTrace::criticalDescriptor.load(std::memory_order_acquire);
  if(destination<0 || busy.test_and_set())return;
  struct Release {~Release(){busy.clear();}} release;
  try {
    if(!replayed) {
      // Replay pre-close stalls when the existing shutdown recorder opens.
      // This avoids requiring a new Python invocation after admission is sealed.
      std::string bytes(512*1024,'\0');
      const int source=::open(InfinityStabilityProbe::output.data(),O_RDONLY|O_CLOEXEC);
      if(source>=0) {
        const auto n=::read(source,bytes.data(),bytes.size());::close(source);
        if(n>0) {
          bytes.resize(n);size_t start=0;
          while(start<bytes.size()) {
            const auto end=bytes.find('\n',start);
            if(end==std::string::npos){Incomplete(destination,"partial_primary_log");break;}
            Append(destination,bytes.substr(start,end-start));start=end+1;
          }
          replayed=true;return;
        }
      }
      Incomplete(destination,"primary_log_unavailable");
      replayed=true;
    }
    Append(destination,latest);
  }catch(...){Incomplete(destination,"mirror_unavailable");}
}
inline void Install() {InfinityStabilityProbe::exportSink.store(Mirror);}
}
