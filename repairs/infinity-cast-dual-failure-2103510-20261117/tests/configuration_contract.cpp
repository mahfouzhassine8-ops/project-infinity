#define main reader_main
#include "../../infinity-cast-source-reader-2103508-20261117/tests/reader.cpp"
#undef main
struct Stop:std::exception{};
struct Bridge:CastVideoBridge {
 std::vector<uint8_t> csd;bool began=false,aborted=false;
 void begin(const std::string&,const std::vector<uint8_t>& a,const std::vector<uint8_t>& b,int64_t,int64_t)override{if(!b.empty())throw Failure("test_second_csd");csd=a;began=true;throw Stop();}
 void offer(const std::vector<uint8_t>&,int64_t)override{throw Failure("test_unexpected_offer");}
 std::vector<uint8_t> finish()override{throw Failure("test_unexpected_finish");}
 void abort()override{aborted=true;}
 void qualifyDelivery(int64_t,int64_t)override{}
};
int main(int argc,char** argv){if(argc!=3)return 2;auto* a=new Source(argv[1]);State full{std::unique_ptr<Input>(a)};full.inspect();auto* p=full.format->streams[full.video]->codecpar;auto expected=CastVideoSource::configuration(p);if(expected.first.empty())return 3;
 int checks=1;std::vector<uint8_t> original(p->extradata,p->extradata+p->extradata_size);auto reject=[&](std::vector<uint8_t> b){AVCodecParameters copy=*p;copy.extradata=b.data();copy.extradata_size=int(b.size());try{CastVideoSource::configuration(&copy);throw Failure("test_bad_configuration_accepted");}catch(const Failure& e){if(std::string(e.what()).find("test_")==0)throw;checks++;}};
 for(size_t n=0;n<original.size();n++)reject(std::vector<uint8_t>(original.begin(),original.begin()+n));auto trailing=original;trailing.push_back(0);reject(trailing);auto wrong=original;wrong[0]=0;reject(wrong);wrong=original;wrong[23]|=64;reject(wrong);
 auto* b=new Source(argv[2]);State inband{std::unique_ptr<Input>(b)};inband.inspect();auto* ip=inband.format->streams[inband.video]->codecpar;if(ip->extradata_size!=23||ip->extradata[22])return 4;
 auto owned=std::make_unique<Bridge>();auto* bridge=owned.get();b->budget=inband.readBudget(0);b->used=0;try{inband.configureVideo(std::move(owned));return 5;}catch(const Stop&){}if(!bridge->began||!bridge->aborted||bridge->csd!=expected.first||!inband.videoInputHeader.empty()||!inband.videoInputCsd.empty())return 6;checks++;
 std::cout<<"PASS_REAL_HVCC_AND_INBAND_CSD checks="<<checks<<" exact_csd_bytes="<<expected.first.size()<<" no_extra_source_scan=true partial_begin_aborted=true\n";
}
