#include "threads/InfinityProbeExport.h"
#include <cassert>
#include <fstream>
#include <iostream>
#include <sys/stat.h>
int main(int argc,char** argv)
{
  assert(argc==2);const std::string root=argv[1];::mkdir(root.c_str(),0700);
  InfinityStabilityProbe::Configure(root+"/probe.jsonl");InfinityProbeExport::Install();
  InfinityStabilityProbe::Snapshot("before_admission_sealed");
  InfinityShutdownTrace::Configure(root.c_str());InfinityShutdownTrace::Begin();
  unsigned used[6]{};
  for(unsigned i=0;i<6;++i)used[i]=InfinityShutdownTrace::retainedBytes[i].load();
  InfinityStabilityProbe::Snapshot("after_admission_sealed");
  InfinityStabilityProbe::Snapshot("later");
  const auto path=root+"/infinity-shutdown-native.jsonl.critical";
  std::ifstream input(path);std::string bytes((std::istreambuf_iterator<char>(input)),{});
  for(const char* text:{"before_admission_sealed","after_admission_sealed","later"}) {
    auto first=bytes.find(text);assert(first!=std::string::npos);assert(bytes.find(text,first+1)==std::string::npos);
  }
  assert(bytes.find("\"checkpoint_authority\":false")!=std::string::npos);
  for(unsigned i=0;i<6;++i) {
    assert(InfinityShutdownTrace::retainedBytes[i].load()==used[i]);
    assert(InfinityShutdownTrace::ReserveCritical(static_cast<InfinityShutdownTrace::EvidenceLane>(i),
        InfinityShutdownTrace::LANE_BYTES[i]-used[i]));
  }
  InfinityProbeExport::Mirror("{\"kind\":\"stability_probe\",\"padding\":\""+std::string(130*1024,'x')+"\"}\n");
  assert(InfinityProbeExport::retained<=InfinityProbeExport::MIRROR_BYTES);
  std::cout<<"Real native export retains pre/post admission-seal snapshots; six original evidence lanes remain intact; independent mirror cap enforced\n";
}
