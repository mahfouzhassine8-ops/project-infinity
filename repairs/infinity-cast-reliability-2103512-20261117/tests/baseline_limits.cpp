#define main retained_reader_main
#include "../../infinity-cast-source-reader-2103508-20261117/tests/reader.cpp"
#undef main
// Real retained high-bitrate MKV packets; a sparse, valid cue fixture retains
// every nth actual cue. No codec packet, timestamp or decoded frame is changed.
int main(int argc,char**argv){if(argc!=3)return 2;int stride=std::stoi(argv[2]);auto* in=new Source(argv[1]);State s{std::unique_ptr<Input>(in)};s.inspect();auto keys=s.keys,starts=s.starts,positions=s.positions;s.keys.clear();s.starts.clear();s.positions.clear();for(size_t i=0;i<keys.size();i+=stride){s.keys.push_back(keys[i]);s.starts.push_back(starts[i]);s.positions.push_back(positions[i]);}s.starts.push_back(starts.back());
 for(size_t i=0;i<s.keys.size();i++){
  in->used=0;in->exhausted=false;std::string planning="none",generation="NOT_EXECUTED";uint64_t budget=0;size_t bytes=0;
  try{budget=s.readBudget(int(i));}catch(const std::exception& e){planning=e.what();}
  if(budget){in->budget=budget;try{auto out=s.segment(int(i));bytes=out.size();generation="none";}catch(const std::exception&e){generation=e.what();}}
  std::cout<<"{\"index\":"<<i<<",\"cue_stride\":"<<stride<<",\"span_us\":"<<s.starts[i+1]-s.starts[i]<<",\"planning\":\""<<planning<<"\",\"generation\":\""<<generation<<"\",\"budget\":"<<budget<<",\"read_bytes\":"<<in->used<<",\"exhausted\":"<<(in->exhausted?"true":"false")<<",\"output_bytes\":"<<bytes<<"}\n";
 }
}
