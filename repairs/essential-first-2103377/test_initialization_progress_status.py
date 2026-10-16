#!/usr/bin/env python3
"""Compile real coordinator status serialization; progress is auxiliary only."""
import sys
import run_runtime_coordinator_tests as runtime


MAIN = r'''
static std::string originalStatusWithDetail(std::size_t detailSize) {
  // The existing explicit JSON peer records every actual production encoding.
  // Select the complete original safety status encoded before new diagnostics,
  // not a reconstructed/mirrored expected status.
  for(const auto& entry:Test::parsed) {
    const auto& row=entry.second;
    if(row["script_persistence"].isObject() &&
       row["script_persistence"]["initialization_progress_contract"].isNull() &&
       row["blockers"].size()==1 && row["blockers"][0]["detail"].asString().size()==detailSize)
      return entry.first;
  }
  assert(false);return {};
}
int main(int argc,char** argv) {
  (void)ready; // Retain the original harness's peer helper without executing saves.
  assert(argc==3);const std::string mode=std::string(argv[1]).substr(8);Test::root=argv[2];
  const int writers=mode=="progress-41"?41:mode=="progress-64"?64:mode=="progress-512"?512:65;
  std::filesystem::create_directories(Test::root);
  assert(RegisterStartupOwner(OWNER,getpid(),Test::root));assert(PublishStartupOwner());
  for(int id=1;id<=writers;++id) {
    InfinityScriptPersistence::Admit(id,"service.observerprobe.writer"+std::to_string(id)+":service.py");
    for(int step=0;step<20;++step)
      assert(InfinityScriptPersistence::InitializationProgress(id,"native.interpreter.create",1000+id));
  }
  assert(Request(SESSION,OWNER,getpid()));
  if(mode=="progress-little-space") {
    std::lock_guard<std::mutex> lock(Get().mutex);
    Get().blockers.push_back({"native_admission",std::string(48000,'x'),1,false});
  }
  std::size_t nearLimitDetailSize=0;
  if(mode=="progress-no-margin") {
    {
      std::lock_guard<std::mutex> lock(Get().mutex);
      Get().blockers.push_back({"native_admission",{},1,false});
      // Keep elapsed-field digit widths stable while measuring the payload.
      // The original expires/deadline and all admission state stay intact.
      Get().started=std::chrono::steady_clock::now()-std::chrono::seconds(4);
    }
    Status(SESSION,OWNER,getpid());
    const auto original=originalStatusWithDetail(0);assert(original.size()<64512);
    nearLimitDetailSize=65500-original.size();
    std::lock_guard<std::mutex> lock(Get().mutex);
    Get().blockers[0].detail=std::string(nearLimitDetailSize,'x');
  }
  const auto encoded=Status(SESSION,OWNER,getpid());assert(encoded.size()<=65536);
  auto report=Test::parsed.at(encoded);const auto& diagnostic=report["script_persistence"];
  assert(diagnostic["active_writers"].asUnsignedInteger()==static_cast<unsigned>(writers));
  assert(diagnostic["observed_writers"].asUnsignedInteger()==0);
  if(mode=="progress-no-margin") {
    assert(encoded.size()>=65490 && encoded.size()<=65510);
    assert(encoded==originalStatusWithDetail(nearLimitDetailSize));
    assert(diagnostic["initialization_progress_contract"].isNull());
    assert(!AuthorizeTermination(SESSION,OWNER,getpid()));
    assert(!InfinityScriptPersistence::EssentialWritesAuthorized(Get().generation));
    assert(InfinityScriptPersistence::Snapshot().active==65);
    std::cout<<"writers=65 native_status_bytes="<<encoded.size()<<"; exact original bytes retained; no authorization\n";
    return 0;
  }
  assert(diagnostic["initialization_progress_total_writers"].asUnsignedInteger()==static_cast<unsigned>(writers));
  const auto reported=diagnostic["initialization_progress_reported_writers"].asUnsignedInteger();
  if(mode=="progress-41" || mode=="progress-64") {
    assert(reported==static_cast<unsigned>(writers));assert(!diagnostic["initialization_progress_truncated"].asBoolean());
  } else {
    assert(reported<static_cast<unsigned>(writers) && reported<=64);
    assert(diagnostic["initialization_progress_truncated"].asBoolean());
  }
  const auto& progressRows=diagnostic["initialization_progress"];
  for(auto current=progressRows.begin_array();current!=progressRows.end_array();++current) {
    const auto& row=*current;
    assert(row["stage"].asString()=="native.interpreter.create");
    assert(row["steps"].size()<=4 && row["steps_total"].asUnsignedInteger()==20);
  }
  assert(!AuthorizeTermination(SESSION,OWNER,getpid()));
  assert(!InfinityScriptPersistence::EssentialWritesAuthorized(Get().generation));
  assert(InfinityScriptPersistence::Snapshot().active==static_cast<unsigned>(writers));
  std::cout<<"writers="<<writers<<" reported="<<reported<<" native_status_bytes="<<encoded.size()<<"; no authorization\n";
}
'''


if __name__=='__main__':
    runtime.CASES=['startup-progress-41','startup-progress-64','startup-progress-65','startup-progress-512','startup-progress-little-space','startup-progress-no-margin']
    runtime.MAIN=MAIN
    runtime.main()
