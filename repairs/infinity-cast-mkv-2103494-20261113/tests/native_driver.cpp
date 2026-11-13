#define INFINITY_REMUX_HOST
#include "../native/InfinityCastRemux.cpp"
#include <cstdio>
#include <fstream>
#include <iostream>
#include <filesystem>
using namespace InfinityMkv;
struct File:Input {
 FILE* f=nullptr;int64_t size=0;
 explicit File(const char* path){f=std::fopen(path,"rb");if(!f)throw Failure("test_input_missing");fseeko(f,0,SEEK_END);size=ftello(f);fseeko(f,0,SEEK_SET);}
 ~File(){if(f)std::fclose(f);}
 int read(uint8_t* dst,int n)override{size_t r=std::fread(dst,1,n,f);return r?int(r):std::ferror(f)?AVERROR(EIO):0;}
 int64_t seek(int64_t at,int mode)override{if(mode&AVSEEK_SIZE)return size;mode&=~AVSEEK_FORCE;if(fseeko(f,at,mode))return AVERROR(EIO);return ftello(f);}
};
void save(const std::filesystem::path& p,const std::vector<uint8_t>& data){std::ofstream out(p,std::ios::binary);out.write(reinterpret_cast<const char*>(data.data()),data.size());if(!out)throw Failure("test_output_failed");}
int main(int argc,char** argv){if(argc!=3)return 2;State s(std::unique_ptr<Input>(new File(argv[1])));try {
 s.inspect();std::filesystem::path out=argv[2];std::filesystem::create_directories(out);save(out/"init.mp4",s.init);std::ofstream meta(out/"inspection.json");meta<<s.describe();meta.close();
 // Deliberately out of order: the converter must seek using real MKV cues.
 for(size_t n=0;n<s.keys.size();n++){size_t index=n%2==0?s.keys.size()-1-n/2:n/2;save(out/("seg"+std::to_string(index)+".m4s"),s.segment(int(index)));}
 std::cout<<s.describe()<<"\nPASS_NATIVE_STREAM_COPY_RANDOM_SEGMENTS\n";return 0;
 }catch(const std::exception& e){std::cerr<<s.describe()<<'\n'<<e.what()<<'\n';return 1;}}
