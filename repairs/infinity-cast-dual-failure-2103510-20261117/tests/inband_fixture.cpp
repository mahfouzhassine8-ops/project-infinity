// Historical short-fixture prototype. Current CI uses make_inband_fixture.py
// to preserve all source packet timing, seek indexes and valid CRC treatment.
#define main reader_main
#include "../../infinity-cast-source-reader-2103508-20261117/tests/reader.cpp"
#undef main
using Bytes=std::vector<uint8_t>;
static void add(Bytes& a,const Bytes& b){a.insert(a.end(),b.begin(),b.end());}
static Bytes element(uint32_t id,const Bytes& data){Bytes out;int w=id>0xffffff?4:id>0xffff?3:id>0xff?2:1;for(int k=w-1;k>=0;k--)out.push_back(uint8_t(id>>(k*8)));unsigned len=1;while(data.size()>((1ULL<<(7*len))-2))++len;uint64_t n=data.size()|(1ULL<<(7*len));for(int k=int(len)-1;k>=0;k--)out.push_back(uint8_t(n>>(k*8)));add(out,data);return out;}
static Bytes number(uint32_t id,uint64_t n){Bytes b;unsigned w=1;while(w<8&&(n>>(w*8)))w++;for(int k=int(w)-1;k>=0;k--)b.push_back(uint8_t(n>>(k*8)));return element(id,b);}
static Bytes text(uint32_t id,const char* value){return element(id,Bytes(value,value+std::strlen(value)));}
static Bytes real(uint32_t id,double d){uint64_t n;std::memcpy(&n,&d,8);Bytes b;for(int k=7;k>=0;k--)b.push_back(uint8_t(n>>(k*8)));return element(id,b);}
int main(int argc,char**argv){if(argc<3)return 2;bool firstOnly=argc>3,keySeen=false;auto* in=new Source(argv[1]);State s{std::unique_ptr<Input>(in)};s.inspect();auto& a=api();auto* source=s.format->streams[s.video]->codecpar;auto* h=source->extradata;size_t at=23;Bytes ps;
 for(unsigned k=0;k<h[22];k++){int t=h[at++]&63;unsigned count=(h[at]<<8)|h[at+1];at+=2;for(unsigned n=0;n<count;n++){unsigned len=(h[at]<<8)|h[at+1];at+=2;if(t==32||t==33||t==34){int width=(h[21]&3)+1;for(int j=width-1;j>=0;j--)ps.push_back(uint8_t(len>>(j*8)));ps.insert(ps.end(),h+at,h+at+len);}at+=len;}}
 if(ps.empty()||at!=size_t(source->extradata_size))return 3;
 Bytes header;for(auto v:{number(0x4286,1),number(0x42f7,1),number(0x42f2,4),number(0x42f3,8),text(0x4282,"matroska"),number(0x4287,4),number(0x4285,2)})add(header,v);
 Bytes info;for(auto v:{number(0x2ad7b1,1000000),text(0x4d80,"Infinity source-derived test"),text(0x5741,"Infinity source-derived test"),real(0x4489,s.duration/1000.0)})add(info,v);
 Bytes tracks,video;for(auto v:{number(0xd7,1),number(0x73c5,1),number(0x83,1),text(0x86,"V_MPEGH/ISO/HEVC"),number(0x23e383,a.av_rescale_q(1,av_inv_q(s.format->streams[s.video]->avg_frame_rate),{1,1000000000}))})add(video,v);Bytes privateData(h,h+23);privateData[22]=0;add(video,element(0x63a2,privateData));Bytes geometry;add(geometry,number(0xb0,source->width));add(geometry,number(0xba,source->height));add(video,element(0xe0,geometry));add(tracks,element(0xae,video));
 auto* ap=s.format->streams[s.audio]->codecpar;Bytes audio;for(auto v:{number(0xd7,2),number(0x73c5,2),number(0x83,2),text(0x86,ap->codec_id==AV_CODEC_ID_AAC?"A_AAC":"A_EAC3")})add(audio,v);Bytes sound;add(sound,real(0xb5,ap->sample_rate));add(sound,number(0x9f,ap->ch_layout.nb_channels));if(ap->extradata_size>0)add(audio,element(0x63a2,Bytes(ap->extradata,ap->extradata+ap->extradata_size)));add(audio,element(0xe1,sound));add(tracks,element(0xae,audio));Bytes segment;add(segment,element(0x1549a966,info));add(segment,element(0x1654ae6b,tracks));
 in->budget=128*1024*1024;in->used=0;Packet q;Bytes cluster;int64_t base=-1;bool clusterKey=false;std::vector<std::pair<int64_t,size_t>> cues;
 auto flush=[&](){if(base<0)return;if(clusterKey)cues.push_back({base,segment.size()});add(segment,element(0x1f43b675,cluster));cluster.clear();};
 while(a.av_read_frame(s.format,q.value)>=0){auto* p=q.value;if(p->stream_index!=s.video&&p->stream_index!=s.audio){a.av_packet_unref(p);continue;}int64_t ms=s.micros(p->pts,s.format->streams[p->stream_index]->time_base)/1000;if(ms<0){a.av_packet_unref(p);continue;}
  bool key=p->stream_index==s.video&&(p->flags&AV_PKT_FLAG_KEY);if(base<0||key){flush();base=ms;clusterKey=key;add(cluster,number(0xe7,base));}int64_t relative=ms-base;if(relative<INT16_MIN||relative>INT16_MAX)return 9;Bytes block={uint8_t(p->stream_index==s.video?0x81:0x82),uint8_t(uint16_t(relative)>>8),uint8_t(relative),uint8_t((p->flags&AV_PKT_FLAG_KEY)?0x80:0)};if(key){if(!firstOnly||!keySeen)add(block,ps);keySeen=true;}block.insert(block.end(),p->data,p->data+p->size);add(cluster,element(0xa3,block));a.av_packet_unref(p);
 }flush();
 auto seekHead=[&](uint64_t position){Bytes seek;add(seek,element(0x53ab,{0x1c,0x53,0xbb,0x6b}));Bytes where;for(int k=7;k>=0;k--)where.push_back(uint8_t(position>>(k*8)));add(seek,element(0x53ac,where));return element(0x114d9b74,element(0x4dbb,seek));};
 size_t prefix=seekHead(0).size();Bytes cueData;for(auto [time,pos]:cues){Bytes point;add(point,number(0xb3,time));Bytes location;add(location,number(0xf7,1));add(location,number(0xf1,pos+prefix));add(point,element(0xb7,location));add(cueData,element(0xbb,point));}Bytes body=seekHead(prefix+segment.size());add(body,segment);add(body,element(0x1c53bb6b,cueData));Bytes whole=element(0x1a45dfa3,header);add(whole,element(0x18538067,body));std::ofstream f(argv[2],std::ios::binary);f.write((char*)whole.data(),whole.size());std::cout<<"CREATED_GENUINE_INBAND_PARAMETER_SET_MKV bytes="<<whole.size()<<" cues="<<cues.size()<<"\n";
}
