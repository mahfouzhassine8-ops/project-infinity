// Cast-owned, read-only demux / RAM-only stream-copy mux. Never changes Kodi.
#include <algorithm>
#include <array>
#include <atomic>
#include <cerrno>
#include <chrono>
#include <cstdint>
#include <cstring>
#include <dlfcn.h>
#include <limits>
#include <memory>
#include <mutex>
#include <sstream>
#include <stdexcept>
#include <string>
#include <unordered_map>
#include <vector>
extern "C" {
#include <libavformat/avformat.h>
#include <libavcodec/avcodec.h>
#include <libavcodec/ac3_parser.h>
#include <libavutil/avutil.h>
#include <libavutil/mem.h>
}
#ifndef INFINITY_REMUX_HOST
#include <jni.h>
#endif
namespace InfinityMkv {
using Clock=std::chrono::steady_clock;
constexpr size_t FragmentLimit=8*1024*1024,InitLimit=1024*1024;
constexpr int IndexLimit=8192;
// One fixed MPEG presentation epoch for the ENTIRE HLS rendition. This is a
// timestamp origin, never a wait/delay. HLS maps its first presentation to zero.
// Positive DTS avoids negative-CTS/edit-list ambiguities with B-frame video.
constexpr int64_t TransportEpoch=10LL*AV_TIME_BASE;
int denyOpen(AVFormatContext*,AVIOContext**,const char*,int,AVDictionary**){return AVERROR(EPERM);}
struct Failure:std::runtime_error{using std::runtime_error::runtime_error;};
#define FUNCTIONS(F) F(av_version_info) F(avutil_version) F(av_malloc) F(av_free) F(av_freep) F(av_dict_set) F(av_dict_get) F(av_dict_free) F(av_rescale_q) F(av_find_input_format) F(avformat_alloc_context) F(avformat_open_input) F(avformat_find_stream_info) F(avformat_close_input) F(avio_alloc_context) F(avio_context_free) F(avio_flush) F(avformat_index_get_entries_count) F(avformat_index_get_entry) F(av_seek_frame) F(avformat_alloc_output_context2) F(av_stream_new_side_data) F(avformat_new_stream) F(avformat_free_context) F(avcodec_parameters_copy) F(avcodec_get_name) F(av_ac3_parse_header) F(avformat_query_codec) F(avformat_write_header) F(av_interleaved_write_frame) F(av_write_frame) F(av_write_trailer) F(av_packet_alloc) F(av_packet_free) F(av_packet_unref) F(av_packet_rescale_ts) F(av_read_frame)
struct Api {
 void* image=nullptr;
#define DECLARE(f) decltype(&::f) f=nullptr;
 FUNCTIONS(DECLARE)
#undef DECLARE
 Api(){
#ifdef INFINITY_REMUX_HOST
  image=dlopen("libavformat.so.60",RTLD_NOW|RTLD_LOCAL);
#else
  // NOLOAD is mandatory: never start or replace a Kodi engine from Cast.
  image=dlopen("libkodi.so",RTLD_NOW|RTLD_LOCAL|RTLD_NOLOAD);
#endif
  if(!image)throw Failure("mkv_existing_ffmpeg_unavailable");
  try {
#define BIND(f) f=reinterpret_cast<decltype(f)>(dlsym(image,#f));if(!f)throw Failure("mkv_existing_ffmpeg_api_missing");
  FUNCTIONS(BIND)
#undef BIND
  if(std::strncmp(av_version_info(),"6.0.1",5)!=0 || (avutil_version()>>16)!=58)throw Failure("mkv_ffmpeg_abi_mismatch");
  }catch(...){dlclose(image);image=nullptr;throw;}
 }
 ~Api(){if(image)dlclose(image);}
};
Api& api(){static Api value;return value;}
void validateDolby(const AVPacket* packet,AVCodecID codec){
 if(!packet || !packet->data || packet->size<=0)throw Failure("mkv_invalid_dolby_frame");
 size_t at=0,total=size_t(packet->size);
 while(at<total){uint8_t bsid=0;uint16_t frame=0;
  if(total-at<8 || api().av_ac3_parse_header(packet->data+at,total-at,&bsid,&frame)<0 || frame<8 || frame>total-at || (codec==AV_CODEC_ID_EAC3?bsid<=10:bsid>8))throw Failure("mkv_invalid_dolby_frame");
  at+=frame;
 }
}

struct Input {virtual ~Input()=default;virtual int read(uint8_t*,int)=0;virtual int64_t seek(int64_t,int)=0;};
struct Packet {AVPacket* value=api().av_packet_alloc();~Packet(){if(value)api().av_packet_free(&value);}Packet(){if(!value)throw Failure("mkv_memory_limit");}};
} // namespace InfinityMkv
#include "../../../infinity-cast-end-to-end-2103504-20261116/native/CastAudioAdapter.h"
#include "../../../infinity-cast-hardware-pipeline-2103506-20261117/native/CastVideoAdapter.h"
namespace InfinityMkv {
struct State {
 std::unique_ptr<Input> input;AVFormatContext* format=nullptr;AVIOContext* io=nullptr;
 std::atomic<bool> cancelled{false};Clock::time_point deadline;
 int video=-1,audio=-1;int64_t origin=0,duration=0;std::vector<int64_t> keys,starts;
 std::vector<uint8_t> init;std::string videoName,audioName,codecs;std::unique_ptr<CastAudioAdapter> audioAdapter;
 std::unique_ptr<CastVideoBridge> videoBridge;CastVideoResult videoFormat;std::vector<uint8_t> bootstrapVideo;bool videoConfigured=false;
 explicit State(std::unique_ptr<Input> value):input(std::move(value)){api();}
 ~State(){if(format)api().avformat_close_input(&format);if(io){api().av_freep(&io->buffer);api().avio_context_free(&io);}}
 bool stopped()const{return cancelled.load() || Clock::now()>deadline;}
 void check()const{if(cancelled.load())throw Failure("mkv_cancelled");if(Clock::now()>deadline)throw Failure("mkv_deadline");}
 static int interrupt(void* p){return static_cast<State*>(p)->stopped();}
 static int read(void* p,uint8_t* data,int n){auto& s=*static_cast<State*>(p);if(s.stopped())return AVERROR_EXIT;int r=s.input->read(data,n);return r==0?AVERROR_EOF:r;}
 static int64_t seek(void* p,int64_t at,int whence){auto& s=*static_cast<State*>(p);if(s.stopped())return AVERROR_EXIT;return s.input->seek(at,whence);}
 int64_t micros(int64_t t,AVRational base)const{return api().av_rescale_q(t,base,AV_TIME_BASE_Q);}
 void inspect();std::vector<uint8_t> segment(int index);std::vector<uint8_t> videoSegment(int index);void configureVideo(std::unique_ptr<CastVideoBridge>);std::string describe()const;
};
struct Output {
 AVFormatContext* format=nullptr;AVIOContext* io=nullptr;std::vector<uint8_t> bytes;const char* failure=nullptr;bool packetHeader=false;
 ~Output(){if(format)api().avformat_free_context(format);if(io){api().av_freep(&io->buffer);api().avio_context_free(&io);}}
 static int write(void* p,uint8_t* data,int n){auto& o=*static_cast<Output*>(p);if(n<0 || o.bytes.size()+size_t(n)>FragmentLimit){o.failure="mkv_fragment_limit";return AVERROR(ENOSPC);}try{o.bytes.insert(o.bytes.end(),data,data+n);return n;}catch(...){o.failure="mkv_memory_limit";return AVERROR(ENOMEM);}}
 void begin(State& s){
  if(api().avformat_alloc_output_context2(&format,nullptr,"mp4",nullptr)<0 || !format)throw Failure("mkv_mp4_muxer_unavailable");
  for(int in:{s.video,s.audio})if(in>=0){
   auto* source=s.format->streams[in];if(api().avformat_query_codec(format->oformat,source->codecpar->codec_id,FF_COMPLIANCE_NORMAL)<=0)throw Failure("mkv_codec_not_mp4_compatible");
   auto* out=api().avformat_new_stream(format,nullptr);if(!out || api().avcodec_parameters_copy(out->codecpar,source->codecpar)<0)throw Failure("mkv_stream_copy_failed");
   if(in==s.audio && s.audioAdapter)s.audioAdapter->parameters(out->codecpar);
   if(in==s.video && s.videoBridge){
    auto* p=out->codecpar;api().av_freep(&p->extradata);p->extradata_size=int(s.videoFormat.config.size());p->extradata=static_cast<uint8_t*>(api().av_malloc(size_t(p->extradata_size)+AV_INPUT_BUFFER_PADDING_SIZE));if(!p->extradata)throw Failure("mkv_memory_limit");std::memset(p->extradata,0,size_t(p->extradata_size)+AV_INPUT_BUFFER_PADDING_SIZE);std::copy(s.videoFormat.config.begin(),s.videoFormat.config.end(),p->extradata);
    p->codec_id=AV_CODEC_ID_H264;p->width=1280;p->height=720;p->profile=s.videoFormat.profile;p->level=s.videoFormat.level;p->format=AV_PIX_FMT_YUV420P;p->video_delay=0;p->bit_rate=2000000;p->sample_aspect_ratio={1,1};p->color_primaries=AVCOL_PRI_BT709;p->color_trc=AVCOL_TRC_BT709;p->color_space=AVCOL_SPC_BT709;p->color_range=AVCOL_RANGE_MPEG;p->field_order=AV_FIELD_PROGRESSIVE;p->bits_per_raw_sample=8;p->bits_per_coded_sample=8;
   }
   for(int k=0;k<source->nb_side_data;k++) {
    if(in==s.video && s.videoBridge)continue; // Encoded SDR must not inherit HEVC/HDR/Dolby metadata.
    const auto& side=source->side_data[k];
    if(side.type==AV_PKT_DATA_MASTERING_DISPLAY_METADATA || side.type==AV_PKT_DATA_CONTENT_LIGHT_LEVEL || side.type==AV_PKT_DATA_DISPLAYMATRIX || side.type==AV_PKT_DATA_STEREO3D || side.type==AV_PKT_DATA_DOVI_CONF){
     if(side.size>65536)throw Failure("mkv_display_metadata_limit");auto* copy=api().av_stream_new_side_data(out,side.type,side.size);if(!copy)throw Failure("mkv_memory_limit");std::memcpy(copy,side.data,side.size);
    }
   }
   out->codecpar->codec_tag=0;out->time_base=(in==s.audio && s.audioAdapter)?AVRational{1,s.audioAdapter->Rate}:source->time_base;out->avg_frame_rate=source->avg_frame_rate;out->sample_aspect_ratio=source->sample_aspect_ratio;out->id=int(format->nb_streams);out->disposition=source->disposition;
   if(in==s.video && s.videoBridge){out->time_base=AV_TIME_BASE_Q;out->avg_frame_rate={30,1};out->sample_aspect_ratio={1,1};}
  }
  auto* buffer=static_cast<unsigned char*>(api().av_malloc(32768));if(!buffer)throw Failure("mkv_memory_limit");
  io=api().avio_alloc_context(buffer,32768,1,this,nullptr,write,nullptr);if(!io){api().av_free(buffer);throw Failure("mkv_memory_limit");}
  io->seekable=0;format->pb=io;format->flags|=AVFMT_FLAG_CUSTOM_IO;format->avoid_negative_ts=AVFMT_AVOID_NEG_TS_DISABLED;format->io_open=denyOpen;
  AVDictionary* options=nullptr;
  packetHeader=!s.audioAdapter && s.audio>=0 && (s.format->streams[s.audio]->codecpar->codec_id==AV_CODEC_ID_AC3 || s.format->streams[s.audio]->codecpar->codec_id==AV_CODEC_ID_EAC3);
  // Dolby MP4 dac3/dec3 configuration is derived by FFmpeg from REAL packets.
  // The unchanged AAC/MP3 path still emits its original immediate header.
  std::string flags="empty_moov+frag_custom+frag_discont+default_base_moof+omit_tfhd_offset+skip_trailer";
  if(packetHeader)flags+="+delay_moov";
  api().av_dict_set(&options,"movflags",flags.c_str(),0);
  api().av_dict_set(&options,"use_editlist","0",0);
  int code=api().avformat_write_header(format,&options);api().av_dict_free(&options);api().avio_flush(io);
  if(code<0 || failure)throw Failure(failure?failure:"mkv_mux_header_failed");if(!packetHeader && (bytes.empty() || bytes.size()>InitLimit))throw Failure("mkv_init_limit");
 }
 size_t headerSize()const {
  // Split FFmpeg's real ftyp/moov from media; never synthesize codec boxes.
  bool ftyp=false;size_t at=0;
  auto word=[&](size_t n){return (uint32_t(bytes[n])<<24)|(uint32_t(bytes[n+1])<<16)|(uint32_t(bytes[n+2])<<8)|bytes[n+3];};
  while(at+8<=bytes.size() && at<InitLimit){uint64_t size=word(at);size_t minimum=8;
   if(size==1){if(at+16>bytes.size())break;size=(uint64_t(word(at+8))<<32)|word(at+12);minimum=16;}
   if(size<minimum || size>bytes.size()-at || size>InitLimit-at)break;
   if(std::memcmp(bytes.data()+at+4,"ftyp",4)==0)ftyp=true;
   if(std::memcmp(bytes.data()+at+4,"moov",4)==0){if(!ftyp)break;return at+size;}
   if(std::memcmp(bytes.data()+at+4,"moof",4)==0 || std::memcmp(bytes.data()+at+4,"mdat",4)==0)break;
   at+=size;
  }
  throw Failure("mkv_delayed_init_invalid");
 }
};

// HEVC level 1 is encoded as 30, not 1 (FFmpeg6 H265 level table).
// Only repair a reserved below-minimum declaration. Existing valid headers,
// all NAL arrays and media packets remain untouched. The demuxer is Cast-owned.
static void repairReservedHevcLevel(AVCodecParameters* p){
 if(p->codec_id!=AV_CODEC_ID_HEVC)return;
 if(!p->extradata || p->extradata_size<23 || p->extradata[0]!=1)throw Failure("mkv_invalid_hevc_configuration");
 if(p->extradata[12]>=30)return;
 if(p->extradata_size>65536)throw Failure("mkv_codec_private_limit");
 const uint8_t* bytes=p->extradata;const size_t size=size_t(p->extradata_size);
 std::array<uint8_t,12> agreed{};bool have=false;unsigned vps=0,spsRefs=0,nals=0;
 auto refuse=[](){throw Failure("mkv_hevc_ptl_unverified");};
 auto knownLevel=[](uint8_t level){switch(level){case 30:case 60:case 63:case 90:case 93:case 120:case 123:case 150:case 153:case 156:case 180:case 183:case 186:return true;default:return false;}};
 size_t at=23;
 auto word=[&](){if(size-at<2)refuse();unsigned value=(unsigned(bytes[at])<<8)|bytes[at+1];at+=2;return value;};
 for(unsigned array=0;array<bytes[22];++array){
  if(at>=size)refuse();uint8_t header=bytes[at++];if(header&64)refuse();unsigned type=header&63,count=word();
  for(unsigned index=0;index<count;++index){
   unsigned length=word();if(++nals>1024 || length<2 || length>size-at)refuse();const uint8_t* nal=bytes+at;at+=length;
   if((nal[0]&128) || ((nal[0]>>1)&63)!=type || !(nal[1]&7))refuse();
   if(type!=32 && type!=33)continue;
   // No multilayer/extension interpretation or first-parameter-set guessing.
   if((nal[0]&1) || (nal[1]>>3) || (nal[1]&7)!=1)refuse();
   std::vector<uint8_t> rbsp;rbsp.reserve(length-2);unsigned zeros=0;
   for(unsigned k=2;k<length;++k){uint8_t b=nal[k];
    if(zeros==2 && b==3){if(k+1>=length || nal[k+1]>3)refuse();zeros=0;continue;}
    if(zeros==2 && b<3)refuse();
    rbsp.push_back(b);zeros=b==0?std::min(zeros+1,2u):0;
   }
   size_t start=type==32?4:1;if(rbsp.size()<start+12)refuse();
   if(type==32){
    if((rbsp[0]&15)!=12 || (rbsp[1]>>4) || ((rbsp[1]>>1)&7)>6 || rbsp[2]!=255 || rbsp[3]!=255)refuse();
    vps|=1u<<(rbsp[0]>>4);
   }else{if(((rbsp[0]>>1)&7)>6)refuse();spsRefs|=1u<<(rbsp[0]>>4);}
   std::array<uint8_t,12> current;std::copy_n(rbsp.data()+start,12,current.begin());
   if(!knownLevel(current[11]) || ((current[0]&32) && current[11]<120))refuse();
   if(have && current!=agreed)throw Failure("mkv_hevc_ptl_conflict");agreed=current;have=true;
  }
 }
 if(at!=size || !have || !vps || !spsRefs || (spsRefs&~vps))refuse();
 // Commit only after complete validation. No partial change on any refusal.
 std::copy(agreed.begin(),agreed.end(),p->extradata+1);
}
std::string codecDescription(const AVCodecParameters* p){
 // RFC6381, using the same verified configuration copied into the MP4 muxer.
 // Keep FFmpeg's existing avc1/hev1 sample entries and every media packet.
 std::ostringstream out;out<<std::uppercase<<std::hex;
 if(p->codec_id==AV_CODEC_ID_HEVC){
  if(p->extradata_size<23 || p->extradata[0]!=1)throw Failure("mkv_invalid_hevc_configuration");const auto* b=p->extradata;
  out<<"hev1.";int space=(b[1]>>6)&3;if(space)out<<char('A'+space-1);out<<std::dec<<int(b[1]&31)<<'.';uint32_t reversed=0;
  for(int n=0;n<32;n++)reversed|=uint32_t((b[2+n/8]>>(7-n%8))&1)<<n;
  out<<std::hex<<reversed<<'.'<<((b[1]&32)?'H':'L')<<std::dec<<int(b[12]);int last=11;while(last>=6 && b[last]==0)last--;
  for(int n=6;n<=last;n++){out<<'.'<<std::hex;if(b[n]<16)out<<'0';out<<int(b[n]);}return out.str();
 }
 if(p->codec_id==AV_CODEC_ID_H264){if(p->extradata_size<4 || p->extradata[0]!=1)throw Failure("mkv_invalid_avc_configuration");out<<"avc1.";for(int n=1;n<4;n++){if(p->extradata[n]<16)out<<'0';out<<int(p->extradata[n]);}return out.str();}
 if(p->codec_id==AV_CODEC_ID_EAC3)return "ec-3";if(p->codec_id==AV_CODEC_ID_AC3)return "ac-3";
 if(p->codec_id==AV_CODEC_ID_MP3)return p->sample_rate>24000?"mp4a.6B":"mp4a.69";
 if(p->codec_id==AV_CODEC_ID_AAC){if(p->extradata_size<2)throw Failure("mkv_invalid_aac_configuration");int type=p->extradata[0]>>3;if(type==31)type=32+((p->extradata[0]&7)<<3)+(p->extradata[1]>>5);if(!type)throw Failure("mkv_invalid_aac_configuration");return "mp4a.40."+std::to_string(type);}
 throw Failure("mkv_unsupported_codec_description");
}
int select(AVFormatContext* f,AVMediaType kind){
 int first=-1,defaultIndex=-1,count=0,defaults=0;
 for(unsigned n=0;n<f->nb_streams;n++){auto* s=f->streams[n];if(s->codecpar->codec_type!=kind || (s->disposition&AV_DISPOSITION_ATTACHED_PIC))continue;first=int(n);count++;if(s->disposition&AV_DISPOSITION_DEFAULT){defaultIndex=int(n);defaults++;}}
 if(count<=1)return first;if(defaults==1)return defaultIndex;throw Failure(kind==AVMEDIA_TYPE_AUDIO?"mkv_ambiguous_audio_tracks":"mkv_ambiguous_video_tracks");
}
// A true closed random-access picture is required for independent JIT chunks.
bool closedPicture(const AVPacket* packet,const AVCodecParameters* codec){
 if(!codec->extradata || codec->extradata_size<6 || codec->extradata[0]!=1)return false;
 int bytes=codec->codec_id==AV_CODEC_ID_H264?(codec->extradata[4]&3)+1:codec->extradata_size>21?(codec->extradata[21]&3)+1:0;
 if(bytes<1 || bytes>4)return false;
 for(int at=0;at+bytes<packet->size;){uint32_t n=0;for(int j=0;j<bytes;j++)n=(n<<8)|packet->data[at++];if(!n || n>uint32_t(packet->size-at))return false;
  int type=codec->codec_id==AV_CODEC_ID_H264?packet->data[at]&31:(packet->data[at]>>1)&63;
  if(codec->codec_id==AV_CODEC_ID_H264 && type>=1 && type<=5)return type==5;
  if(codec->codec_id==AV_CODEC_ID_HEVC && type<=31)return type==19 || type==20;
  at+=int(n);
 }return false;
}
void State::inspect(){
 deadline=Clock::now()+std::chrono::seconds(15);format=api().avformat_alloc_context();if(!format)throw Failure("mkv_memory_limit");
 auto* buffer=static_cast<unsigned char*>(api().av_malloc(32768));if(!buffer)throw Failure("mkv_memory_limit");
 io=api().avio_alloc_context(buffer,32768,0,this,read,nullptr,seek);if(!io){api().av_free(buffer);throw Failure("mkv_memory_limit");}
 io->seekable=AVIO_SEEKABLE_NORMAL;format->pb=io;format->flags|=AVFMT_FLAG_CUSTOM_IO;format->interrupt_callback={interrupt,this};format->probesize=4*1024*1024;format->max_analyze_duration=2*AV_TIME_BASE;format->max_streams=32;format->max_index_size=IndexLimit*sizeof(AVIndexEntry);format->io_open=denyOpen;
 const AVInputFormat* matroska=api().av_find_input_format("matroska");if(!matroska)throw Failure("mkv_existing_demuxer_unavailable");
 if(api().avformat_open_input(&format,"cast-private-input.mkv",matroska,nullptr)<0)throw Failure("mkv_input_probe_failed");check();
 if(!format->iformat || std::string(format->iformat->name).find("matroska")==std::string::npos)throw Failure("mkv_wrong_container");
 if(api().avformat_find_stream_info(format,nullptr)<0)throw Failure("mkv_stream_info_failed");check();
 video=select(format,AVMEDIA_TYPE_VIDEO);audio=select(format,AVMEDIA_TYPE_AUDIO);if(video<0)throw Failure("mkv_video_missing");
 videoName=api().avcodec_get_name(format->streams[video]->codecpar->codec_id);audioName=audio<0?"none":api().avcodec_get_name(format->streams[audio]->codecpar->codec_id);
 auto v=format->streams[video]->codecpar->codec_id;if(v!=AV_CODEC_ID_H264 && v!=AV_CODEC_ID_HEVC)throw Failure("mkv_unsupported_video_codec");
 if(audio>=0){auto a=format->streams[audio]->codecpar->codec_id;if(a!=AV_CODEC_ID_AAC && a!=AV_CODEC_ID_MP3 && a!=AV_CODEC_ID_AC3 && a!=AV_CODEC_ID_EAC3)throw Failure("mkv_unsupported_audio_codec");}
 for(int n:{video,audio})if(n>=0){auto* s=format->streams[n];if(s->codecpar->extradata_size<0 || s->codecpar->extradata_size>65536)throw Failure("mkv_codec_private_limit");if(api().av_dict_get(s->metadata,"enc_key_id",nullptr,0))throw Failure("drm_or_unsupported_encryption");for(int k=0;k<s->nb_side_data;k++)if(s->side_data[k].type==AV_PKT_DATA_ENCRYPTION_INIT_INFO || s->side_data[k].type==AV_PKT_DATA_ENCRYPTION_INFO)throw Failure("drm_or_unsupported_encryption");}
 origin=format->start_time;if(origin==AV_NOPTS_VALUE || origin< -30LL*24*3600*AV_TIME_BASE || origin>30LL*24*3600*AV_TIME_BASE)throw Failure("mkv_unverified_timeline");duration=format->duration;if(duration<=0 || duration>30LL*24*3600*AV_TIME_BASE)throw Failure("mkv_unverified_duration");
 auto* stream=format->streams[video];int64_t middle=api().av_rescale_q(origin+duration/2,AV_TIME_BASE_Q,stream->time_base);
 if(api().av_seek_frame(format,video,middle,AVSEEK_FLAG_BACKWARD)<0)throw Failure("mkv_seek_index_unavailable");check();
 int count=api().avformat_index_get_entries_count(stream);if(count<=0 || count>IndexLimit)throw Failure("mkv_seek_index_limit");
 for(int n=0;n<count;n++){const auto* key=api().avformat_index_get_entry(stream,n);if(!key || !(key->flags&AVINDEX_KEYFRAME))continue;int64_t us=micros(key->timestamp,stream->time_base)-origin;
  if(us<0 || us>=duration)continue;if(!keys.empty() && key->timestamp<=keys.back())throw Failure("mkv_invalid_seek_index");keys.push_back(key->timestamp);starts.push_back(us);
 }
 if(keys.empty() || starts.front()>AV_TIME_BASE)throw Failure("mkv_first_cue_missing");starts.front()=0;starts.push_back(duration);
 for(size_t n=1;n<starts.size();n++)if(starts[n]<=starts[n-1] || starts[n]-starts[n-1]>30LL*AV_TIME_BASE)throw Failure("mkv_sparse_seek_index");
 repairReservedHevcLevel(stream->codecpar);
 if(audio>=0 && format->streams[audio]->codecpar->codec_id==AV_CODEC_ID_EAC3)audioAdapter.reset(new CastAudioAdapter(format,audio,origin,duration,[this]{check();}));
 Output out;out.begin(*this);
 if(out.packetHeader){
  if(api().av_seek_frame(format,video,keys.front(),AVSEEK_FLAG_BACKWARD)<0)throw Failure("mkv_header_seek_failed");
  Packet packet;int seen=0;
  // Two real independent Dolby audio packets let FFmpeg finish dec3/dac3.
  // This isolated bootstrap output is discarded except its empty init header.
  // Each actual segment gets a FRESH muxer and retains every original packet.
  for(int n=0;n<512 && seen<2;n++){check();int code=api().av_read_frame(format,packet.value);if(code<0)throw Failure("mkv_audio_header_packets_missing");auto* p=packet.value;
   if(p->stream_index!=audio){api().av_packet_unref(p);continue;}
   if(p->size<=0 || p->size>65536 || p->pts==AV_NOPTS_VALUE)throw Failure("mkv_audio_header_invalid");validateDolby(p,format->streams[audio]->codecpar->codec_id);
   for(int k=0;k<p->side_data_elems;k++)if(p->side_data[k].type==AV_PKT_DATA_ENCRYPTION_INFO || p->side_data[k].type==AV_PKT_DATA_ENCRYPTION_INIT_INFO)throw Failure("drm_or_unsupported_encryption");
   auto* stream=format->streams[audio];int64_t offset=api().av_rescale_q(origin-TransportEpoch,AV_TIME_BASE_Q,stream->time_base);p->pts-=offset;if(p->dts!=AV_NOPTS_VALUE){p->dts-=offset;if(p->dts<0)throw Failure("mkv_unsupported_decode_preroll");}
   api().av_packet_rescale_ts(p,stream->time_base,out.format->streams[1]->time_base);p->stream_index=1;p->pos=-1;
   if(api().av_write_frame(out.format,p)<0 || out.failure)throw Failure(out.failure?out.failure:"mkv_audio_header_parse_failed");api().av_packet_unref(p);seen++;
  }
  if(seen!=2)throw Failure("mkv_audio_header_packets_missing");
  if(api().av_write_frame(out.format,nullptr)<0 || api().av_write_trailer(out.format)<0)throw Failure("mkv_audio_header_flush_failed");api().avio_flush(out.io);check();
  if(out.failure)throw Failure(out.failure);size_t header=out.headerSize();init.assign(out.bytes.begin(),out.bytes.begin()+header);
 }else init=out.bytes;
 codecs=codecDescription(out.format->streams[0]->codecpar);if(audio>=0)codecs+=","+codecDescription(out.format->streams[1]->codecpar);check();
}
std::vector<uint8_t> State::segment(int index){
 deadline=Clock::now()+std::chrono::seconds(15);
 if(videoBridge){if(index==0&&!bootstrapVideo.empty()){check();return std::move(bootstrapVideo);}return videoSegment(index);}
 deadline=Clock::now()+std::chrono::seconds(15);check();if(index<0 || size_t(index)>=keys.size())throw Failure("mkv_segment_out_of_range");
 std::vector<CastAudioAdapter::Encoded> converted;
 if(audioAdapter)converted=audioAdapter->interval(starts[index],starts[index+1]);
 // Recover demuxer DTS before the requested cue; never infer new video DTS.
 const size_t seekIndex=audioAdapter && index>0?size_t(index-1):size_t(index);
 if(api().av_seek_frame(format,video,keys[seekIndex],AVSEEK_FLAG_BACKWARD)<0)throw Failure("mkv_segment_seek_failed");
 Output out;out.begin(*this);if(!out.packetHeader && out.bytes!=init)throw Failure("mkv_init_changed");size_t header=out.bytes.size();Packet packet;int writtenVideo=0,writtenAudio=0;bool boundary=false;int64_t readPackets=0;
 const int64_t begin=starts[index]+origin,end=starts[index+1]+origin;
 for(auto& encoded:converted){check();auto* p=packet.value;if(audioAdapter->a.av_new_packet(p,int(encoded.data.size()))<0)throw Failure("mkv_memory_limit");std::memcpy(p->data,encoded.data.data(),encoded.data.size());p->pts=p->dts=encoded.sample+10LL*audioAdapter->Rate;p->duration=encoded.duration;p->flags=encoded.flags;for(auto& side:encoded.side){auto* target=audioAdapter->a.av_packet_new_side_data(p,side.type,side.data.size());if(!target)throw Failure("mkv_memory_limit");std::memcpy(target,side.data.data(),side.data.size());}p->stream_index=1;p->pos=-1;if(api().av_interleaved_write_frame(out.format,p)<0 || out.failure)throw Failure(out.failure?out.failure:"mkv_aac_packet_mux_failed");writtenAudio++;}
 for(;;){check();if(++readPackets>250000)throw Failure("mkv_packet_limit");int result=api().av_read_frame(format,packet.value);if(result==AVERROR_EOF)break;if(result<0)throw Failure("mkv_packet_read_failed");auto* p=packet.value;
  int source=p->stream_index;if((source!=video && source!=audio) || (source==audio && audioAdapter)){api().av_packet_unref(p);continue;}
  auto* stream=format->streams[source];if(out.packetHeader && source==audio)validateDolby(p,stream->codecpar->codec_id);if(p->pts==AV_NOPTS_VALUE)throw Failure("mkv_missing_packet_timestamp");int64_t at=micros(p->pts,stream->time_base);
  if(source==video && (p->flags&AV_PKT_FLAG_KEY) && at>=end){if(boundary && at>end){api().av_packet_unref(p);break;}boundary=true;}
  if(at<begin || at>=end){api().av_packet_unref(p);continue;}
  if(source==video && writtenVideo==0){if(!(p->flags&AV_PKT_FLAG_KEY) || p->pts!=keys[index])throw Failure("mkv_keyframe_mismatch");if(!closedPicture(p,stream->codecpar))throw Failure("mkv_open_gop_not_supported");}
  for(int n=0;n<p->side_data_elems;n++)if(p->side_data[n].type==AV_PKT_DATA_ENCRYPTION_INFO || p->side_data[n].type==AV_PKT_DATA_ENCRYPTION_INIT_INFO)throw Failure("drm_or_unsupported_encryption");
  int mapped=source==video?0:1;int64_t offset=api().av_rescale_q(origin-TransportEpoch,AV_TIME_BASE_Q,stream->time_base);p->pts-=offset;if(p->dts!=AV_NOPTS_VALUE){p->dts-=offset;if(p->dts<0)throw Failure("mkv_unsupported_decode_preroll");}
  api().av_packet_rescale_ts(p,stream->time_base,out.format->streams[mapped]->time_base);p->stream_index=mapped;p->pos=-1;
  if(api().av_interleaved_write_frame(out.format,p)<0 || out.failure)throw Failure(out.failure?out.failure:"mkv_packet_mux_failed");
  if(source==video)writtenVideo++;else writtenAudio++;
 }
 if(!writtenVideo || (audio>=0 && !audioAdapter && !writtenAudio))throw Failure("mkv_empty_segment");
 if(api().av_interleaved_write_frame(out.format,nullptr)<0 || api().av_write_frame(out.format,nullptr)<0 || api().av_write_trailer(out.format)<0)throw Failure("mkv_fragment_flush_failed");api().avio_flush(out.io);check();
 if(out.failure)throw Failure(out.failure);
 if(out.packetHeader){header=out.headerSize();if(std::vector<uint8_t>(out.bytes.begin(),out.bytes.begin()+header)!=init)throw Failure("mkv_init_changed");}
 if(out.bytes.size()<=header)throw Failure("mkv_empty_fragment");
 return std::vector<uint8_t>(out.bytes.begin()+header,out.bytes.end());
}

void State::configureVideo(std::unique_ptr<CastVideoBridge> bridge){
 if(videoBridge||!bridge||!format||video<0)throw Failure("cast_hw_configuration_state");
 for(int n=0;n<format->streams[video]->nb_side_data;n++){auto& side=format->streams[video]->side_data[n];
  if(side.type==AV_PKT_DATA_DOVI_CONF || side.type==AV_PKT_DATA_STEREO3D)throw Failure("cast_hw_display_layout_unsupported");
  if(side.type==AV_PKT_DATA_DISPLAYMATRIX){int32_t m[9];if(side.size!=sizeof(m))throw Failure("cast_hw_display_transform_unsupported");std::memcpy(m,side.data,sizeof(m));const int32_t identity[9]={65536,0,0,0,65536,0,0,0,1073741824};if(!std::equal(std::begin(m),std::end(m),std::begin(identity)))throw Failure("cast_hw_display_transform_unsupported");}
 }
 if(audio>=0&&!audioAdapter&&format->streams[audio]->codecpar->codec_id!=AV_CODEC_ID_AAC)throw Failure("cast_hw_audio_format_unsupported");
 videoBridge=std::move(bridge);videoConfigured=false;bootstrapVideo=videoSegment(0);
}
std::vector<uint8_t> State::videoSegment(int index){
 const auto workStarted=Clock::now();
 deadline=Clock::now()+std::chrono::seconds(15);check();if(index<0||size_t(index)>=keys.size())throw Failure("mkv_segment_out_of_range");
 std::vector<CastAudioAdapter::Encoded> converted;if(audioAdapter)converted=audioAdapter->interval(starts[index],starts[index+1]);
 auto* source=format->streams[video];auto* p=source->codecpar;auto csd=CastVideoSource::configuration(p);auto fps=source->avg_frame_rate.num>0?source->avg_frame_rate:source->r_frame_rate;auto sar=source->sample_aspect_ratio.num>0?source->sample_aspect_ratio:p->sample_aspect_ratio;
 std::ostringstream descriptor;descriptor<<"{\"video\":\""<<(p->codec_id==AV_CODEC_ID_HEVC?"hevc":"h264")<<"\",\"width\":"<<p->width<<",\"height\":"<<p->height<<",\"profile\":"<<p->profile<<",\"level\":"<<p->level<<",\"transfer\":"<<p->color_trc<<",\"primaries\":"<<p->color_primaries<<",\"matrix\":"<<p->color_space<<",\"range\":"<<p->color_range<<",\"fps_num\":"<<fps.num<<",\"fps_den\":"<<fps.den<<",\"sar_num\":"<<sar.num<<",\"sar_den\":"<<sar.den<<"}";
 if(api().av_seek_frame(format,video,keys[index],AVSEEK_FLAG_BACKWARD)<0)throw Failure("cast_hw_video_seek_failed");
 CastVideoResult result;
 struct AudioPacket{std::vector<uint8_t> data;int64_t pts,dts,duration;int flags;std::vector<CastAudioAdapter::Side> side;};std::vector<AudioPacket> passthrough;
 const int64_t begin=origin+starts[index],end=origin+starts[index+1];bool started=false,first=true,boundary=false;int packets=0;Packet packet;
 try{
  check();std::string description=descriptor.str();description.pop_back();description+=",\"budget_ms\":"+std::to_string(std::max<int64_t>(0,std::chrono::duration_cast<std::chrono::milliseconds>(deadline-Clock::now()).count()-100))+"}";started=true;videoBridge->begin(description,csd.first,csd.second,starts[index],starts[index+1]);
  for(;;){check();if(++packets>250000)throw Failure("mkv_packet_limit");int code=api().av_read_frame(format,packet.value);if(code==AVERROR_EOF)break;if(code<0)throw Failure("mkv_packet_read_failed");auto* q=packet.value;
   int stream=q->stream_index;if(stream!=video&&stream!=audio){api().av_packet_unref(q);continue;}
   for(int n=0;n<q->side_data_elems;n++)if(q->side_data[n].type==AV_PKT_DATA_ENCRYPTION_INFO||q->side_data[n].type==AV_PKT_DATA_ENCRYPTION_INIT_INFO)throw Failure("drm_or_unsupported_encryption");
   if(q->pts==AV_NOPTS_VALUE)throw Failure("mkv_missing_packet_timestamp");auto* track=format->streams[stream];int64_t at=micros(q->pts,track->time_base);
   if(stream==video&&(q->flags&AV_PKT_FLAG_KEY)&&at>=end){if(boundary&&at>end){api().av_packet_unref(q);break;}boundary=true;}
   if(at<begin||at>=end){api().av_packet_unref(q);continue;}
   if(stream==video){if(first){if(!(q->flags&AV_PKT_FLAG_KEY)||q->pts!=keys[index]||!closedPicture(q,p))throw Failure("mkv_open_gop_not_supported");first=false;}videoBridge->offer(CastVideoSource::accessUnit(p,q),at-origin);}
   else if(!audioAdapter){if(q->size<=0||q->size>65536||passthrough.size()>2000)throw Failure("cast_hw_audio_packet_limit");AudioPacket a{std::vector<uint8_t>(q->data,q->data+q->size),q->pts,q->dts,q->duration,q->flags,{}};for(int k=0;k<q->side_data_elems;k++){auto& side=q->side_data[k];if(side.type==AV_PKT_DATA_NEW_EXTRADATA)throw Failure("cast_hw_audio_configuration_changed");if(side.size>65536||a.side.size()>16)throw Failure("cast_hw_audio_side_limit");a.side.push_back({side.type,std::vector<uint8_t>(side.data,side.data+side.size)});}passthrough.push_back(std::move(a));}
   api().av_packet_unref(q);
  }
  result=CastVideoResult::parse(videoBridge->finish(),starts[index],starts[index+1]);started=false;
 }catch(...){if(started)try{videoBridge->abort();}catch(...){}throw;}
 if(first||result.packets.empty())throw Failure("cast_hw_video_empty");
 if(videoConfigured&&videoFormat.config!=result.config)throw Failure("cast_hw_avc_configuration_changed");
 videoFormat.width=result.width;videoFormat.height=result.height;videoFormat.profile=result.profile;videoFormat.level=result.level;videoFormat.config=result.config;
 AVCodecParameters proof{};proof.codec_id=AV_CODEC_ID_H264;proof.extradata=videoFormat.config.data();proof.extradata_size=int(videoFormat.config.size());
 for(size_t n=0;n<result.packets.size();n++){auto& item=result.packets[n];AVPacket checkPacket{};checkPacket.data=item.data.data();checkPacket.size=int(item.data.size());if(n==0&&(!(item.flags&AV_PKT_FLAG_KEY)||!closedPicture(&checkPacket,&proof)))throw Failure("cast_hw_first_picture_not_idr");}
 Output out;out.begin(*this);if(videoConfigured&&out.bytes!=init)throw Failure("mkv_init_changed");size_t header=out.bytes.size();
 struct MuxPacket{const std::vector<uint8_t>* data;int stream;int64_t pts,dts,duration;int flags;AVRational base;const std::vector<CastAudioAdapter::Side>* side;};std::vector<MuxPacket> mux;
 for(auto& v:result.packets)mux.push_back({&v.data,0,v.pts+TransportEpoch,v.pts+TransportEpoch,v.duration,v.flags,AV_TIME_BASE_Q,nullptr});
 for(auto& a:converted)mux.push_back({&a.data,1,a.sample+10LL*audioAdapter->Rate,a.sample+10LL*audioAdapter->Rate,a.duration,a.flags,{1,audioAdapter->Rate},&a.side});
 if(!passthrough.empty()){auto* track=format->streams[audio];int64_t offset=api().av_rescale_q(origin-TransportEpoch,AV_TIME_BASE_Q,track->time_base);for(auto& a:passthrough)mux.push_back({&a.data,1,a.pts-offset,a.dts==AV_NOPTS_VALUE?a.dts:a.dts-offset,a.duration,a.flags,track->time_base,&a.side});}
 std::stable_sort(mux.begin(),mux.end(),[&](const MuxPacket& a,const MuxPacket& b){return micros(a.dts==AV_NOPTS_VALUE?a.pts:a.dts,a.base)<micros(b.dts==AV_NOPTS_VALUE?b.pts:b.dts,b.base);});
 AudioApi allocator;for(auto& item:mux){check();auto* q=packet.value;api().av_packet_unref(q);if(allocator.av_new_packet(q,int(item.data->size()))<0)throw Failure("mkv_memory_limit");std::copy(item.data->begin(),item.data->end(),q->data);q->pts=item.pts;q->dts=item.dts;q->duration=item.duration;q->flags=item.flags;q->stream_index=item.stream;q->pos=-1;if(item.side)for(auto& side:*item.side){auto* data=allocator.av_packet_new_side_data(q,side.type,side.data.size());if(!data)throw Failure("mkv_memory_limit");std::copy(side.data.begin(),side.data.end(),data);}api().av_packet_rescale_ts(q,item.base,out.format->streams[item.stream]->time_base);if(api().av_interleaved_write_frame(out.format,q)<0||out.failure)throw Failure("cast_hw_packet_mux_failed");}
 if(api().av_interleaved_write_frame(out.format,nullptr)<0||api().av_write_frame(out.format,nullptr)<0||api().av_write_trailer(out.format)<0)throw Failure("cast_hw_mux_flush_failed");api().avio_flush(out.io);check();if(out.failure||out.bytes.size()<=header)throw Failure("cast_hw_fragment_empty");
 videoBridge->qualifyDelivery(std::chrono::duration_cast<std::chrono::milliseconds>(Clock::now()-workStarted).count(),(starts[index+1]-starts[index])/1000);
 if(!videoConfigured){init.assign(out.bytes.begin(),out.bytes.begin()+header);codecs=codecDescription(out.format->streams[0]->codecpar);if(audio>=0)codecs+=","+codecDescription(out.format->streams[1]->codecpar);videoConfigured=true;}
 return std::vector<uint8_t>(out.bytes.begin()+header,out.bytes.end());
}
std::string safeName(const std::string& value){if(value.empty() || value.size()>32 || value.find_first_not_of("abcdefghijklmnopqrstuvwxyz0123456789_")!=std::string::npos)return "unknown";return value;}
std::string State::describe()const{std::ostringstream out;out<<"{\"video\":\""<<safeName(videoBridge?"h264":videoName)<<"\",\"audio\":\""<<safeName(audioAdapter?"aac":audioName)<<"\",\"audio_input\":\""<<safeName(audioName)<<"\",\"codecs\":\""<<codecs<<"\",\"origin_us\":"<<origin<<",\"duration_us\":"<<duration<<",\"starts_us\":[";for(size_t n=0;n<starts.size();n++){if(n)out<<',';out<<starts[n];}out<<"]";if(format && video>=0){auto* stream=format->streams[video];auto* v=stream->codecpar;auto fps=stream->avg_frame_rate;out<<",\"video_profile\":"<<(videoConfigured?videoFormat.profile:v->profile)<<",\"video_level\":"<<(videoConfigured?videoFormat.level:v->level)<<",\"width\":"<<(videoConfigured?1280:v->width)<<",\"height\":"<<(videoConfigured?720:v->height)<<",\"fps_num\":"<<fps.num<<",\"fps_den\":"<<fps.den<<",\"color_transfer\":"<<(videoConfigured?int(AVCOL_TRC_BT709):int(v->color_trc))<<",\"input_color_transfer\":"<<v->color_trc;}out<<"}";return out.str();}
} // namespace InfinityMkv
#ifndef INFINITY_REMUX_HOST
namespace {
using namespace InfinityMkv;
struct JniInput:Input {
 JavaVM* vm=nullptr;jobject object=nullptr;jbyteArray buffer=nullptr;jmethodID reader=nullptr,seeker=nullptr;
 JniInput(JNIEnv* e,jobject input){e->GetJavaVM(&vm);object=e->NewGlobalRef(input);buffer=static_cast<jbyteArray>(e->NewGlobalRef(e->NewByteArray(65536)));jclass type=e->GetObjectClass(input);reader=e->GetMethodID(type,"read","([BI)I");seeker=e->GetMethodID(type,"seek","(JI)J");e->DeleteLocalRef(type);if(!object || !buffer || !reader || !seeker || e->ExceptionCheck()){if(object)e->DeleteGlobalRef(object);if(buffer)e->DeleteGlobalRef(buffer);object=nullptr;buffer=nullptr;throw Failure("mkv_input_callback_failed");}}
 ~JniInput(){JNIEnv* e=nullptr;if(vm && vm->GetEnv(reinterpret_cast<void**>(&e),JNI_VERSION_1_6)==JNI_OK){if(object)e->DeleteGlobalRef(object);if(buffer)e->DeleteGlobalRef(buffer);}}
 JNIEnv* env(){JNIEnv* e=nullptr;if(vm->GetEnv(reinterpret_cast<void**>(&e),JNI_VERSION_1_6)!=JNI_OK)return nullptr;return e;}
 int read(uint8_t* dst,int n)override{auto* e=env();if(!e)return AVERROR(EIO);n=std::min(n,65536);int got=e->CallIntMethod(object,reader,buffer,n);if(e->ExceptionCheck()){e->ExceptionClear();return AVERROR(EIO);}if(got>0 && got<=n)e->GetByteArrayRegion(buffer,0,got,reinterpret_cast<jbyte*>(dst));if(e->ExceptionCheck()){e->ExceptionClear();return AVERROR(EIO);}return got<0?AVERROR(EIO):got;}
 int64_t seek(int64_t at,int mode)override{auto* e=env();if(!e)return AVERROR(EIO);int64_t result=e->CallLongMethod(object,seeker,jlong(at),jint(mode));if(e->ExceptionCheck()){e->ExceptionClear();return AVERROR(EIO);}return result;}
};

struct JniVideo:CastVideoBridge {
 JavaVM* vm=nullptr;jobject object=nullptr;jmethodID beginId=nullptr,offerId=nullptr,finishId=nullptr,abortId=nullptr,qualifyId=nullptr;
 static void allocation(JNIEnv* e,const void* p){if(!p||e->ExceptionCheck()){if(e->ExceptionCheck())e->ExceptionClear();throw Failure("cast_hw_jni_allocation");}}
 JniVideo(JNIEnv* e,jobject video){e->GetJavaVM(&vm);object=e->NewGlobalRef(video);allocation(e,object);jclass type=nullptr;
  try{type=e->GetObjectClass(video);allocation(e,type);auto method=[&](const char* name,const char* signature){auto id=e->GetMethodID(type,name,signature);if(!id||e->ExceptionCheck()){if(e->ExceptionCheck())e->ExceptionClear();throw Failure("cast_hw_java_contract");}return id;};beginId=method("begin","(Ljava/lang/String;[B[BJJ)V");offerId=method("offer","([BJ)V");finishId=method("finish","()[B");abortId=method("abortSegment","()V");qualifyId=method("qualifyDelivery","(JJ)V");e->DeleteLocalRef(type);}
  catch(...){if(type)e->DeleteLocalRef(type);e->DeleteGlobalRef(object);object=nullptr;throw;}
 }
 ~JniVideo(){JNIEnv* e=nullptr;if(object&&vm->GetEnv(reinterpret_cast<void**>(&e),JNI_VERSION_1_6)==JNI_OK)e->DeleteGlobalRef(object);}
 JNIEnv* env(){JNIEnv* e=nullptr;if(vm->GetEnv(reinterpret_cast<void**>(&e),JNI_VERSION_1_6)!=JNI_OK)throw Failure("cast_hw_jni_thread");return e;}
 void checked(JNIEnv* e){if(!e->ExceptionCheck())return;auto failure=e->ExceptionOccurred();e->ExceptionClear();std::string reason="cast_hw_java_failure";auto type=e->GetObjectClass(failure);if(!type||e->ExceptionCheck()){if(e->ExceptionCheck())e->ExceptionClear();e->DeleteLocalRef(failure);throw Failure(reason);}auto get=e->GetMethodID(type,"getMessage","()Ljava/lang/String;");if(get){auto message=static_cast<jstring>(e->CallObjectMethod(failure,get));if(!e->ExceptionCheck()&&message){const char* raw=e->GetStringUTFChars(message,nullptr);if(raw){std::string value(raw);if(value.size()<=64&&value.find_first_not_of("abcdefghijklmnopqrstuvwxyz0123456789_")==std::string::npos)reason=value;e->ReleaseStringUTFChars(message,raw);}e->DeleteLocalRef(message);}}if(e->ExceptionCheck())e->ExceptionClear();e->DeleteLocalRef(type);e->DeleteLocalRef(failure);throw Failure(reason);}
 jbyteArray array(JNIEnv* e,const std::vector<uint8_t>& bytes){auto out=e->NewByteArray(jsize(bytes.size()));allocation(e,out);if(!bytes.empty())e->SetByteArrayRegion(out,0,jsize(bytes.size()),reinterpret_cast<const jbyte*>(bytes.data()));if(e->ExceptionCheck()){e->ExceptionClear();e->DeleteLocalRef(out);throw Failure("cast_hw_jni_allocation");}return out;}
 void begin(const std::string& desc,const std::vector<uint8_t>& a,const std::vector<uint8_t>& b,int64_t start,int64_t end)override {auto* e=env();jstring text=nullptr;jbyteArray first=nullptr,second=nullptr;
  try{text=e->NewStringUTF(desc.c_str());allocation(e,text);first=array(e,a);second=array(e,b);e->CallVoidMethod(object,beginId,text,first,second,jlong(start),jlong(end));checked(e);}
  catch(...){if(text)e->DeleteLocalRef(text);if(first)e->DeleteLocalRef(first);if(second)e->DeleteLocalRef(second);throw;}
  e->DeleteLocalRef(text);e->DeleteLocalRef(first);e->DeleteLocalRef(second);
 }
 void offer(const std::vector<uint8_t>& packet,int64_t pts)override{auto* e=env();auto data=array(e,packet);e->CallVoidMethod(object,offerId,data,jlong(pts));e->DeleteLocalRef(data);checked(e);}
 std::vector<uint8_t> finish()override{auto* e=env();auto output=static_cast<jbyteArray>(e->CallObjectMethod(object,finishId));checked(e);if(!output)throw Failure("cast_hw_java_empty_result");jsize n=e->GetArrayLength(output);if(n<1||n>int(FragmentLimit)){e->DeleteLocalRef(output);throw Failure("cast_hw_java_result_limit");}std::vector<uint8_t> result(size_t(n),0);e->GetByteArrayRegion(output,0,n,reinterpret_cast<jbyte*>(result.data()));e->DeleteLocalRef(output);checked(e);return result;}
 void abort()override{auto* e=env();e->CallVoidMethod(object,abortId);checked(e);}
 void qualifyDelivery(int64_t elapsed,int64_t span)override{auto* e=env();e->CallVoidMethod(object,qualifyId,jlong(elapsed),jlong(span));checked(e);}
};
std::mutex handlesMutex;std::unordered_map<jlong,std::shared_ptr<State>> handles;jlong nextHandle=0;
std::shared_ptr<State> get(jlong handle){std::lock_guard<std::mutex> lock(handlesMutex);auto i=handles.find(handle);if(i==handles.end())throw Failure("mkv_stale_handle");return i->second;}
void error(JNIEnv* e,const char* reason){if(e->ExceptionCheck())e->ExceptionClear();e->ThrowNew(e->FindClass("java/io/IOException"),reason);}
jbyteArray bytes(JNIEnv* e,const std::vector<uint8_t>& data){auto result=e->NewByteArray(jsize(data.size()));if(result)e->SetByteArrayRegion(result,0,jsize(data.size()),reinterpret_cast<const jbyte*>(data.data()));return result;}
}
extern "C" JNIEXPORT jlong JNICALL Java_com_projectinfinity_kodi_InfinityCastRemuxNative_open(JNIEnv* e,jclass,jobject input){try{auto state=std::make_shared<State>(std::unique_ptr<Input>(new JniInput(e,input)));std::lock_guard<std::mutex> lock(handlesMutex);if(!handles.empty())throw Failure("mkv_previous_context_draining");jlong id=++nextHandle;handles.emplace(id,std::move(state));return id;}catch(const std::exception& x){error(e,x.what());return 0;}}
extern "C" JNIEXPORT jstring JNICALL Java_com_projectinfinity_kodi_InfinityCastRemuxNative_inspect(JNIEnv* e,jclass,jlong h){try{auto s=get(h);std::string problem;try{s->inspect();}catch(const Failure& f){problem=f.what();}std::string result=s->describe();result.pop_back();result+=",\"status\":\""+std::string(problem.empty()?"ok":"error")+"\",\"reason\":\""+problem+"\"}";return e->NewStringUTF(result.c_str());}catch(const std::exception& x){error(e,x.what());return nullptr;}}
extern "C" JNIEXPORT jstring JNICALL Java_com_projectinfinity_kodi_InfinityCastRemuxNative_configureVideo(JNIEnv* e,jclass,jlong h,jobject video){try{auto s=get(h);s->configureVideo(std::unique_ptr<CastVideoBridge>(new JniVideo(e,video)));return e->NewStringUTF(s->describe().c_str());}catch(const std::exception& x){error(e,x.what());return nullptr;}}
extern "C" JNIEXPORT jbyteArray JNICALL Java_com_projectinfinity_kodi_InfinityCastRemuxNative_init(JNIEnv* e,jclass,jlong h){try{return bytes(e,get(h)->init);}catch(const std::exception& x){error(e,x.what());return nullptr;}}
extern "C" JNIEXPORT jbyteArray JNICALL Java_com_projectinfinity_kodi_InfinityCastRemuxNative_segment(JNIEnv* e,jclass,jlong h,jint n){try{return bytes(e,get(h)->segment(n));}catch(const std::exception& x){error(e,x.what());return nullptr;}}
extern "C" JNIEXPORT void JNICALL Java_com_projectinfinity_kodi_InfinityCastRemuxNative_cancel(JNIEnv*,jclass,jlong h){try{get(h)->cancelled=true;}catch(...) {}}
extern "C" JNIEXPORT void JNICALL Java_com_projectinfinity_kodi_InfinityCastRemuxNative_close(JNIEnv*,jclass,jlong h){std::shared_ptr<State> last;{std::lock_guard<std::mutex> lock(handlesMutex);auto i=handles.find(h);if(i==handles.end())return;last=i->second;last->cancelled=true;handles.erase(i);}}
extern "C" JNIEXPORT jint JNICALL Java_com_projectinfinity_kodi_InfinityCastRemuxNative_active(JNIEnv*,jclass){std::lock_guard<std::mutex> lock(handlesMutex);return jint(handles.size());}
#endif
