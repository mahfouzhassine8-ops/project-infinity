#define main reader_main
#include "../../infinity-cast-source-reader-2103508-20261117/tests/reader.cpp"
#undef main
static void observe(State& s,const char* stage){
 auto* p=s.format->streams[s.video]->codecpar;std::cout<<stage<<" size="<<p->extradata_size<<" version="<<(p->extradata_size?int(p->extradata[0]):-1)<<" arrays="<<(p->extradata_size>22?int(p->extradata[22]):-1);
 try{auto c=CastVideoSource::configuration(p);std::cout<<" csd="<<c.first.size()<<","<<c.second.size();}catch(const std::exception& e){std::cout<<" error="<<e.what();}std::cout<<"\n";
}
int main(int argc,char** argv){if(argc<2)return 2;auto* in=new Source(argv[1]);State s{std::unique_ptr<Input>(in)};s.inspect();observe(s,"after_inspect");
 if(s.audioAdapter){in->budget=s.readBudget(0);in->used=0;auto a=s.audioAdapter->interval(s.starts[0],s.starts[1]);std::cout<<"aac_packets="<<a.size()<<"\n";observe(s,"after_audio");}
 for(size_t n=0;n<s.keys.size();n++){in->budget=s.readBudget(int(n));in->used=0;s.segment(int(n));observe(s,"after_segment");}
}
