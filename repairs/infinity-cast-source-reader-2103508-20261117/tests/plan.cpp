#define INFINITY_REMUX_HOST
#include "../../infinity-six-repairs-2103502-20261116/cast/native/InfinityCastRemux.cpp"
#include <cstdio>
#include <iostream>
using namespace InfinityMkv;
struct Source:Input{FILE*f;int64_t length;size_t used=0;Source(const char*p){f=fopen(p,"rb");if(!f)throw Failure("fixture");fseeko(f,0,SEEK_END);length=ftello(f);fseeko(f,0,SEEK_SET);}~Source(){fclose(f);}int read(uint8_t*b,int n)override{int got=fread(b,1,n,f);used+=got;return got;}int64_t seek(int64_t at,int w)override{if(w&AVSEEK_SIZE)return length;w&=~AVSEEK_FORCE;return fseeko(f,at,w)?AVERROR(EIO):ftello(f);}};
int main(int argc,char**argv){if(argc!=2)return 2;int checks=0;auto need=[&](bool b){if(!b)throw Failure("test_assertion");checks++;};auto* in=new Source(argv[1]);State s{std::unique_ptr<Input>(in)};s.inspect();size_t before=in->used;need(s.audioAdapter!=nullptr);need(s.readBudget(5)>33554432 && s.readBudget(5)<=134217728);need(in->used==before);
 uint8_t privateData[23]={1};privateData[21]=3;uint8_t data[]={0,0,0,3,38,1,128};AVCodecParameters codec{};codec.codec_id=AV_CODEC_ID_HEVC;codec.extradata=privateData;codec.extradata_size=23;AVPacket p{};p.data=data;p.size=7;need(closedPicture(&p,&codec)&&!closedPicture(&p,&codec,true));data[4]=40;need(closedPicture(&p,&codec,true));data[4]=42;need(!closedPicture(&p,&codec));codec.codec_id=AV_CODEC_ID_H264;privateData[4]=3;data[4]=0x65;need(closedPicture(&p,&codec,true));data[4]=0x41;need(!closedPicture(&p,&codec,true));
 s.positionPlanValid=false;need(s.readBudget(5)==33554432);s.positionPlanValid=true;
 s.duration=s.audioAdapter->duration=1000000;s.starts={0,1000000};s.keys={0};s.positions={2};s.sourceLength=44673708;s.audioAdapter->cache.clear();s.audioAdapter->clockAnchor=AV_NOPTS_VALUE;
 need(s.readBudget(0)==134217728);need(in->used==before);s.sourceLength++;s.positions[0]++;bool rejected=false;try{s.readBudget(0);}catch(const Failure&e){rejected=std::string(e.what())=="mkv_source_working_set_limit";}need(rejected);
 s.sourceLength=1048576;s.positions={0};need(s.readBudget(0)==33554432);s.cancelled=true;bool cancelled=false;try{s.segment(0);}catch(const Failure&e){cancelled=std::string(e.what())=="mkv_cancelled";}need(cancelled&&in->used==before);
 s.cancelled=false;s.positionPlanValid=false;s.audioAdapter.reset();need(s.readBudget(0)==33554432);std::cout<<"PASS_PLAN_BOUNDARY_AND_PRESERVATION_NEGATIVES checks="<<checks<<"\n";
}
