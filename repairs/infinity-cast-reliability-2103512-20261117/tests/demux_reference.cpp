// Compile against the unmodified signed512 native source (see generator receipt).
#define INFINITY_REMUX_HOST
#include "BASELINE_NATIVE_SOURCE"
#include <cstdio>
#include <iostream>
#include <iomanip>
#include <libavutil/sha.h>
using namespace InfinityMkv;
struct File:Input {FILE* f;int64_t length;File(const char* path){f=fopen(path,"rb");if(!f)throw Failure("fixture_missing");fseeko(f,0,SEEK_END);length=ftello(f);fseeko(f,0,SEEK_SET);}~File(){fclose(f);}int read(uint8_t* p,int n)override{return fread(p,1,n,f);}int64_t seek(int64_t at,int mode)override{if(mode&AVSEEK_SIZE)return length;mode&=~AVSEEK_FORCE;if(fseeko(f,at,mode))return AVERROR(EIO);return ftello(f);}};
std::string sha(const AVPacket* p){auto alloc=reinterpret_cast<decltype(&av_sha_alloc)>(dlsym(api().image,"av_sha_alloc"));auto init=reinterpret_cast<decltype(&av_sha_init)>(dlsym(api().image,"av_sha_init"));auto update=reinterpret_cast<decltype(&av_sha_update)>(dlsym(api().image,"av_sha_update"));auto finish=reinterpret_cast<decltype(&av_sha_final)>(dlsym(api().image,"av_sha_final"));auto state=alloc();if(!state||init(state,256)<0)throw Failure("test_SHA");update(state,p->data,p->size);std::array<uint8_t,32> bytes;finish(state,bytes.data());api().av_free(state);std::ostringstream out;for(auto b:bytes)out<<std::hex<<std::setw(2)<<std::setfill('0')<<unsigned(b);return out.str();}
int main(int argc,char**argv){if(argc!=2)return 2;State s{std::make_unique<File>(argv[1])};s.inspect();if(api().av_seek_frame(s.format,s.video,s.keys[0],AVSEEK_FLAG_BACKWARD)<0)return 3;Packet p;std::cout<<"{\"FFmpeg_version\":\""<<api().av_version_info()<<"\",\"origin_us\":"<<s.origin<<",\"packets\":[";bool comma=false;for(int n=0;n<250000;n++){int code=api().av_read_frame(s.format,p.value);if(code==AVERROR_EOF)break;if(code<0)return 4;if(p.value->stream_index==s.video){if(comma)std::cout<<',';comma=true;std::cout<<"{\"pts_us\":"<<s.micros(p.value->pts,s.format->streams[s.video]->time_base)<<",\"sha256\":\""<<sha(p.value)<<"\"}";}api().av_packet_unref(p.value);}std::cout<<"]}\n";}
