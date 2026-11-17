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

static std::vector<std::vector<uint8_t>> units(const AVCodecParameters* p,const std::vector<uint8_t>& packet){unsigned width=(p->extradata[21]&3)+1;size_t at=0;std::vector<std::vector<uint8_t>> result;while(at<packet.size()){uint32_t n=0;for(unsigned k=0;k<width;k++)n=(n<<8)|packet.at(at++);if(n>packet.size()-at)throw Failure("test_fixture_length");result.emplace_back(packet.begin()+at,packet.begin()+at+n);at+=n;}return result;}
static std::vector<uint8_t> pack(const AVCodecParameters* p,const std::vector<std::vector<uint8_t>>& u){std::vector<uint8_t> b;unsigned width=(p->extradata[21]&3)+1;for(auto& n:u){for(int k=int(width)-1;k>=0;k--)b.push_back(uint8_t(n.size()>>(k*8)));b.insert(b.end(),n.begin(),n.end());}return b;}
static std::vector<uint8_t> key(State& s,int index){auto* input=static_cast<Source*>(s.input.get());input->budget=s.readBudget(index);input->used=0;if(api().av_seek_frame(s.format,s.video,s.keys[index],AVSEEK_FLAG_BACKWARD)<0)throw Failure("test_seek");Packet packet;for(int n=0;n<512;n++){if(api().av_read_frame(s.format,packet.value)<0)break;auto* q=packet.value;if(q->stream_index==s.video&&q->pts==s.keys[index])return {q->data,q->data+q->size};api().av_packet_unref(q);}throw Failure("test_key_missing");}
int main(int argc,char**argv){if(argc!=3)return 2;State s{std::make_unique<Source>(argv[1])};s.inspect();auto* p=s.format->streams[s.video]->codecpar;auto bytes=key(s,0);AVPacket packet{};packet.data=bytes.data();packet.size=int(bytes.size());auto good=CastVideoSource::configuration(p,&packet).first;int checks=1;auto u=units(p,bytes);
 auto reject=[&](std::vector<std::vector<uint8_t>> data,const char* reason,const std::vector<uint8_t>* verified=nullptr){auto b=pack(p,data);AVPacket q{};q.data=b.data();q.size=int(b.size());try{CastVideoSource::configuration(p,&q,verified);throw Failure("test_bad_AU_accepted");}catch(const Failure& e){if(std::string(e.what())!=reason)throw;checks++;}};
 auto missing=u;missing.erase(std::remove_if(missing.begin(),missing.end(),[](const auto& n){return ((n[0]>>1)&63)==32;}),missing.end());reject(missing,"cast_hw_source_configuration_inband_missing",&good);
 auto bare=u;bare.erase(std::remove_if(bare.begin(),bare.end(),[](const auto& n){unsigned t=(n[0]>>1)&63;return t>=32&&t<=34;}),bare.end());reject(bare,"cast_hw_source_configuration_inband_missing");auto b=pack(p,bare);AVPacket q{};q.data=b.data();q.size=int(b.size());if(CastVideoSource::configuration(p,&q,&good).first!=good)return 3;checks++;
 auto late=bare;for(auto& n:u){unsigned t=(n[0]>>1)&63;if(t>=32&&t<=34)late.push_back(n);}reject(late,"cast_hw_source_configuration_late_sets",&good);
 for(int kind=0;kind<3;kind++){auto bad=u;if(kind==0)bad[0][0]|=128;if(kind==1)bad[0][1]=0;if(kind==2)bad[0][0]|=1;reject(bad,kind==2?"cast_hw_source_multilayer_unsupported":"cast_hw_source_configuration_nal_header",&good);}
 auto many=std::vector<std::vector<uint8_t>>(1025,std::vector<uint8_t>{70,1,128});reject(many,"cast_hw_source_configuration_count_limit");auto huge=u;huge[0].resize(65531,128);reject(huge,"cast_hw_source_configuration_output_limit");
 auto malformed=bytes;malformed.push_back(0);q.data=malformed.data();q.size=int(malformed.size());try{CastVideoSource::configuration(p,&q,&good);return 4;}catch(const Failure&e){if(std::string(e.what())!="cast_hw_source_configuration_nal_length")throw;checks++;}
 // Explicit successful-bootstrap precondition: cache contains only genuine CSD
 // validated above. Android gate must separately exercise successful conversion.
 State cached{std::make_unique<Source>(argv[2])};cached.inspect();auto* cp=cached.format->streams[cached.video]->codecpar;cached.videoInputHeader.assign(cp->extradata,cp->extradata+cp->extradata_size);cached.videoInputCsd=good;cached.videoConfigured=true;auto c=std::make_unique<Bridge>();auto* capture=c.get();cached.videoBridge=std::move(c);auto* source=static_cast<Source*>(cached.input.get());source->budget=cached.readBudget(1);source->used=0;try{cached.videoSegment(1);return 5;}catch(const Stop&){}if(!capture->began||!capture->aborted||capture->csd!=good)return 6;checks++;
 cached.videoInputHeader[1]^=1;c=std::make_unique<Bridge>();capture=c.get();cached.videoBridge=std::move(c);source->budget=cached.readBudget(1);source->used=0;try{cached.videoSegment(1);return 7;}catch(const Failure&e){if(std::string(e.what())!="cast_hw_source_configuration_changed")throw;}if(capture->began)return 8;checks++;
 State fresh{std::make_unique<Source>(argv[2])};fresh.inspect();c=std::make_unique<Bridge>();capture=c.get();fresh.videoBridge=std::move(c);source=static_cast<Source*>(fresh.input.get());source->budget=fresh.readBudget(1);source->used=0;try{fresh.videoSegment(1);return 9;}catch(const Failure&e){if(std::string(e.what())!="cast_hw_source_configuration_inband_missing")throw;}if(capture->began||!fresh.videoInputCsd.empty())return 10;checks++;
 std::cout<<"PASS_INBAND_MALFORMED_BOUNDS_AND_NONZERO_CUE checks="<<checks<<" cache_precondition=explicit_genuine_CSD_fixture no_hardware_claim\n";
}
