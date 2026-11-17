#define INFINITY_REMUX_HOST
#include "../../infinity-six-repairs-2103502-20261116/cast/native/InfinityCastRemux.cpp"
#include <cstdio>
#include <fstream>
#include <iostream>
#include <filesystem>

#include "../native/CastAudioAdapter.h"
using namespace InfinityMkv;
struct File:Input {
 FILE* f=nullptr;int64_t size=0;
 explicit File(const char* path){f=std::fopen(path,"rb");if(!f)throw Failure("test_input_missing");fseeko(f,0,SEEK_END);size=ftello(f);fseeko(f,0,SEEK_SET);}
 ~File(){if(f)std::fclose(f);}
 int read(uint8_t* dst,int n)override{size_t r=std::fread(dst,1,n,f);return r?int(r):std::ferror(f)?AVERROR(EIO):0;}
 int64_t seek(int64_t at,int mode)override{if(mode&AVSEEK_SIZE)return size;mode&=~AVSEEK_FORCE;if(fseeko(f,at,mode))return AVERROR(EIO);return ftello(f);}
};
void save(const std::filesystem::path& p,const std::vector<uint8_t>& data){std::ofstream out(p,std::ios::binary);out.write(reinterpret_cast<const char*>(data.data()),data.size());if(!out)throw Failure("test_output_failed");}

int main(int argc,char** argv){if(argc!=3 && argc!=4)return 2;State s(std::unique_ptr<Input>(new File(argv[1])));try {
 s.inspect();CastAudioAdapter audio(s.format,s.audio,s.origin,s.duration,[&]{s.check();});
 s.deadline=Clock::now()+std::chrono::seconds(15);
 if(argc==4){int calls=0;audio.check=[&]{if(++calls==50)s.cancelled=true;s.check();};try{audio.interval(0,s.duration);throw Failure("test_cancel_not_observed");}catch(const Failure&e){if(std::string(e.what())!="mkv_cancelled")throw;std::cout<<"PASS_CANCELLED_DURING_CONVERSION\n";return 0;}}
 auto all=audio.interval(0,s.duration);std::cout<<"packets "<<all.size()<<" rate "<<audio.Rate<<" last_duration "<<all.back().duration<<" known_end "<<audio.knownEnd<<" duration "<<s.duration<<"\n";
 for(size_t i=1;i<all.size();i++)if(all[i].sample!=all[i-1].sample+1024)throw Failure("test_audio_grid");
 for(size_t i=s.starts.size()-1;i>0;i--){auto part=audio.interval(s.starts[i-1],s.starts[i]);for(auto& p:part){auto& expected=all.at(size_t(p.sample/1024));if(p.data!=expected.data || p.duration!=expected.duration)throw Failure("test_random_access_mismatch");}}
 std::ofstream output(argv[2],std::ios::binary);int freq=audio.Rate==48000?3:audio.Rate==44100?4:5;
 for(auto& p:all){size_t size=p.data.size()+7;uint8_t h[]={0xff,0xf1,uint8_t((1<<6)|(freq<<2)),uint8_t((2<<6)|((size>>11)&3)),uint8_t(size>>3),uint8_t(((size&7)<<5)|31),0xfc};output.write((char*)h,7);output.write((char*)p.data.data(),p.data.size());}
 std::cout<<"PASS_CANONICAL_AUDIO_GRID_RANDOM_REQUESTS\n";return 0;
 }catch(const std::exception&e){std::cerr<<e.what()<<"\n";return 1;}}
