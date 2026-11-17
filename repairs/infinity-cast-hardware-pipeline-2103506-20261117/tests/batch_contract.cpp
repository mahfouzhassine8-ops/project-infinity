#define INFINITY_REMUX_HOST
#include "../../infinity-six-repairs-2103502-20261116/cast/native/InfinityCastRemux.cpp"
#include <iostream>
using namespace InfinityMkv;
static void word(std::vector<uint8_t>& b,uint32_t n){for(int k=3;k>=0;k--)b.push_back(uint8_t(n>>(k*8)));}
static void wide(std::vector<uint8_t>& b,int64_t n){word(b,uint64_t(n)>>32);word(b,uint32_t(n));}
static std::vector<uint8_t> fixture(){std::vector<uint8_t> b;for(int n:{0x43564831,1280,720,66,31,1})word(b,n);std::vector<uint8_t> c={1,66,192,31,255,225,0,5,103,66,192,31,128,1,0,2,104,128};word(b,c.size());b.insert(b.end(),c.begin(),c.end());word(b,2);for(int n=0;n<2;n++){wide(b,n*40000);wide(b,40000);word(b,n==0?1:0);word(b,6);b.insert(b.end(),{0,0,0,2,101,136});}return b;}
int main(){int checks=0;auto good=fixture();auto parsed=CastVideoResult::parse(good,0,80000);if(parsed.packets.size()!=2||parsed.width!=1280)return 1;checks++;
 auto bad=[&](std::vector<uint8_t> b){try{CastVideoResult::parse(b,0,80000);throw std::runtime_error("malformed batch accepted");}catch(const Failure&){checks++;}};
 for(size_t n=0;n<good.size();n++)bad(std::vector<uint8_t>(good.begin(),good.begin()+n));
 for(size_t at:{size_t(0),size_t(4),size_t(8),size_t(12),size_t(16),size_t(20),size_t(24),size_t(28),size_t(32)}){auto b=good;b[at]^=0x80;bad(b);}
 auto trailing=good;trailing.push_back(0);bad(trailing);auto overflow=good;std::fill(overflow.begin()+50,overflow.begin()+58,255);bad(overflow);
 std::vector<uint8_t> hvcc(23,0);hvcc[0]=1;hvcc[1]=1;hvcc[22]=1;hvcc.insert(hvcc.end(),{33,0,1,0,4,66,1,1,96});AVCodecParameters h{};h.codec_id=AV_CODEC_ID_HEVC;h.extradata=hvcc.data();h.extradata_size=int(hvcc.size());auto config=CastVideoSource::configuration(&h);if(config.first.empty())return 1;checks++;hvcc[1]|=32;try{CastVideoSource::configuration(&h);return 1;}catch(const Failure& e){if(std::string(e.what())!="cast_hw_source_high_tier_unsupported")return 1;checks++;}
 std::cout<<"PASS_NATIVE_VIDEO_BATCH_CONTRACT "<<checks<<"\n";
}
