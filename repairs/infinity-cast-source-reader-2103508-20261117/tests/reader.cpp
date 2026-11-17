#define INFINITY_REMUX_HOST
#include "../../infinity-six-repairs-2103502-20261116/cast/native/InfinityCastRemux.cpp"
#include <cstdio>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <iomanip>
#include <libavutil/sha.h>
using namespace InfinityMkv;
std::string hash(const std::vector<uint8_t>& bytes){auto alloc=reinterpret_cast<decltype(&av_sha_alloc)>(dlsym(api().image,"av_sha_alloc"));auto init=reinterpret_cast<decltype(&av_sha_init)>(dlsym(api().image,"av_sha_init"));auto update=reinterpret_cast<decltype(&av_sha_update)>(dlsym(api().image,"av_sha_update"));auto final=reinterpret_cast<decltype(&av_sha_final)>(dlsym(api().image,"av_sha_final"));if(!alloc||!init||!update||!final)throw Failure("test_sha_missing");auto c=alloc();if(!c||init(c,256)<0)throw Failure("test_sha");update(c,bytes.data(),bytes.size());std::array<uint8_t,32> digest{};final(c,digest.data());api().av_free(c);std::ostringstream out;for(auto b:digest)out<<std::hex<<std::setw(2)<<std::setfill('0')<<unsigned(b);return out.str();}

struct Source:Input {
 FILE* f;int64_t length;uint64_t budget=16*1024*1024,used=0;bool exhausted=false;
 explicit Source(const char* p){f=fopen(p,"rb");if(!f)throw Failure("test_source_missing");fseeko(f,0,SEEK_END);length=ftello(f);fseeko(f,0,SEEK_SET);}
 ~Source(){fclose(f);}
 int read(uint8_t* b,int n)override{if(used>=budget){exhausted=true;return AVERROR(ENOSPC);}int got=fread(b,1,std::min<uint64_t>(n,budget-used),f);used+=got;return got;}
 int64_t seek(int64_t at,int whence)override{if(whence&AVSEEK_SIZE)return length;whence&=~AVSEEK_FORCE;if(fseeko(f,at,whence))return AVERROR(EIO);return ftello(f);}
};
int main(int argc,char**argv){if(argc<5)return 2;auto* in=new Source(argv[1]);State s{std::unique_ptr<Input>(in)};try{s.inspect();}catch(const std::exception&e){std::cerr<<"inspect:"<<e.what()<<"\n";return 1;}
 std::filesystem::create_directories(argv[2]);std::ofstream init(std::string(argv[2])+"/init.mp4",std::ios::binary);init.write((char*)s.init.data(),s.init.size());init.close();
 for(int k=4;k<argc;k++){int index=std::stoi(argv[k]);in->budget=std::stoull(argv[3]);in->used=0;in->exhausted=false;std::string error="none",fingerprint;size_t size=0;
  try{if(in->budget==0)in->budget=s.readBudget(index);auto out=s.segment(index);size=out.size();fingerprint=hash(out);std::ofstream f(std::string(argv[2])+"/"+std::to_string(index)+".m4s",std::ios::binary);f.write((char*)out.data(),out.size());}catch(const std::exception&e){error=e.what();}
  std::cout<<"{\"index\":"<<index<<",\"bytes\":"<<in->used<<",\"budget\":"<<in->budget<<",\"exhausted\":"<<(in->exhausted?"true":"false")<<",\"phase_bytes\":[";for(int n=0;n<4;n++){if(n)std::cout<<',';std::cout<<in->consumed[n];}std::cout<<"],\"seeks\":"<<in->seeks<<",\"output\":"<<size<<",\"reason\":\""<<error<<"\",\"sha256\":\""<<fingerprint<<"\"}\n";
 }
}
