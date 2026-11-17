#define main reader_main
#include "../../infinity-cast-source-reader-2103508-20261117/tests/reader.cpp"
#undef main
struct Done:std::exception{};
struct Capture:CastVideoBridge{
 std::vector<uint8_t> raw;std::vector<int64_t> pts;int64_t startUs=0,endUs=0;bool aborted=false;
 void begin(const std::string&,const std::vector<uint8_t>& a,const std::vector<uint8_t>& b,int64_t x,int64_t y)override{raw=a;startUs=x;endUs=y;if(!b.empty())throw Failure("test_secondCsd");}
 void offer(const std::vector<uint8_t>& bytes,int64_t t)override{raw.insert(raw.end(),bytes.begin(),bytes.end());pts.push_back(t);}
 std::vector<uint8_t> finish()override{throw Done();}void abort()override{aborted=true;}void qualifyDelivery(int64_t,int64_t)override{}
};
int main(int argc,char**argv){if(argc!=3)return 2;std::filesystem::create_directories(argv[2]);
 for(int index=0;index<6;index++){
  auto* input=new Source(argv[1]);State state{std::unique_ptr<Input>(input)};state.inspect();input->used=0;input->budget=state.readBudget(index);auto b=std::make_unique<Capture>();auto* capture=b.get();state.videoBridge=std::move(b);
  try{state.segment(index);throw Failure("test_missing_stop");}catch(const Done&){}
  if(!capture->aborted||input->exhausted||capture->pts.empty())throw Failure("test_capture_ownership");std::ofstream f(std::string(argv[2])+"/"+std::to_string(index)+".hevc",std::ios::binary);f.write((char*)capture->raw.data(),capture->raw.size());
  std::cout<<"{\"index\":"<<index<<",\"begin\":"<<capture->startUs<<",\"end\":"<<capture->endUs<<",\"read_bytes\":"<<input->used<<",\"budget\":"<<input->budget<<",\"partial_finish_aborted\":true,\"offered_pts\":[";for(size_t n=0;n<capture->pts.size();n++){if(n)std::cout<<',';std::cout<<capture->pts[n];}std::cout<<"]}\n";
 }
}
