#define INFINITY_REMUX_HOST
#include "/workspace/infinity-cast96-root-cause/repairs/infinity-six-repairs-2103502-20261116/cast/native/InfinityCastRemux.cpp"
#include <fstream>
#include <iostream>
using namespace InfinityMkv;
std::vector<uint8_t> read(const char* p){std::ifstream f(p,std::ios::binary);return {std::istreambuf_iterator<char>(f),std::istreambuf_iterator<char>()};}
int main(int argc,char**argv){if(argc!=4)return 2;auto b=read(argv[1]);auto before=b;AVCodecParameters p{};p.codec_id=AV_CODEC_ID_HEVC;p.extradata=b.data();p.extradata_size=b.size();try{repairReservedHevcLevel(&p);if(std::string(argv[3])!="success")return 3;if(b!=read(argv[2]))return 4;std::cout<<"SUCCESS_EXACT_EXPECTED_BYTES\n";}catch(const Failure&e){if(std::string(argv[3])=="success")return 5;if(b!=before)return 6;if(std::string(e.what())!=argv[3])return 7;std::cout<<e.what()<<" NO_PARTIAL_MUTATION\n";}return 0;}
