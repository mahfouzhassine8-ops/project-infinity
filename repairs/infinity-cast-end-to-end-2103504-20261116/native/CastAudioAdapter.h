#pragma once
// Cast-only experimental audio adapter. No provider, global codec or Kodi state.
// Canonical AAC windows use one source sample grid, independent of video cues.
#include <functional>
#include <map>
extern "C" {
#include <libswresample/swresample.h>
#include <libavutil/channel_layout.h>
#include <libavutil/frame.h>
}
namespace InfinityMkv {
struct AudioApi {
 void* resamplerImage=nullptr;
#define AUDIO_FUNCTIONS(F) F(av_packet_new_side_data) F(av_new_packet) F(avcodec_find_decoder) F(avcodec_find_encoder) F(avcodec_alloc_context3) F(avcodec_parameters_to_context) F(avcodec_parameters_from_context) F(avcodec_open2) F(avcodec_free_context) F(avcodec_send_packet) F(avcodec_receive_frame) F(avcodec_send_frame) F(avcodec_receive_packet) F(av_frame_alloc) F(av_frame_free) F(av_frame_unref) F(av_frame_get_buffer) F(av_frame_make_writable) F(av_channel_layout_copy) F(av_channel_layout_uninit) F(av_channel_layout_compare) F(swr_alloc_set_opts2) F(swr_init) F(swr_convert) F(swr_get_delay) F(swr_free)
#define FIELD(f) decltype(&::f) f=nullptr;
 AUDIO_FUNCTIONS(FIELD)
#undef FIELD
 AudioApi(){
#ifdef INFINITY_REMUX_HOST
  resamplerImage=dlopen("libswresample.so.4",RTLD_NOW|RTLD_LOCAL);
  if(!resamplerImage)throw Failure("host_resampler_unavailable");
#endif
try {
#define BIND_AUDIO(f) f=reinterpret_cast<decltype(f)>(dlsym(api().image,#f));if(!f && resamplerImage)f=reinterpret_cast<decltype(f)>(dlsym(resamplerImage,#f));if(!f)throw Failure("mkv_audio_api_unavailable");
 AUDIO_FUNCTIONS(BIND_AUDIO)
#undef BIND_AUDIO
  }catch(...){if(resamplerImage)dlclose(resamplerImage);resamplerImage=nullptr;throw;}
 }
 ~AudioApi(){if(resamplerImage)dlclose(resamplerImage);}
};
struct CastAudioAdapter {
 static constexpr int FrameSize=1024,WindowFrames=192,WarmupFrames=32;
 const int Rate;
 struct Side {AVPacketSideDataType type;std::vector<uint8_t> data;};
 struct Encoded {std::vector<uint8_t> data;int64_t sample;int duration;int flags;std::vector<Side> side;};
 struct Window {std::vector<Encoded> packets;};
 AudioApi a; AVFormatContext* input;int stream;int64_t origin,duration;
 std::function<void()> check;std::function<bool(int64_t)> sourceSeek;AVCodecContext* encoder=nullptr;
 std::map<int64_t,Window> cache;int64_t knownEnd=-1,clockAnchor=AV_NOPTS_VALUE;
 CastAudioAdapter(AVFormatContext* input,int stream,int64_t origin,int64_t duration,std::function<void()> check,std::function<bool(int64_t)> sourceSeek={})
  :Rate(input->streams[stream]->codecpar->sample_rate),input(input),stream(stream),origin(origin),duration(duration),check(std::move(check)),sourceSeek(std::move(sourceSeek)) {
  if(Rate!=32000 && Rate!=44100 && Rate!=48000)throw Failure("mkv_aac_sample_rate_unsupported");
  encoder=openEncoder();
 }
 ~CastAudioAdapter(){if(encoder)a.avcodec_free_context(&encoder);}
 AVCodecContext* openEncoder(){
  auto* codec=a.avcodec_find_encoder(AV_CODEC_ID_AAC);if(!codec)throw Failure("mkv_aac_encoder_unavailable");
  auto* c=a.avcodec_alloc_context3(codec);if(!c)throw Failure("mkv_memory_limit");
  c->sample_rate=Rate;c->sample_fmt=AV_SAMPLE_FMT_FLTP;c->ch_layout=AV_CHANNEL_LAYOUT_STEREO;
  c->time_base={1,Rate};c->bit_rate=192000;c->flags|=AV_CODEC_FLAG_GLOBAL_HEADER;c->thread_count=1;
  if(a.avcodec_open2(c,codec,nullptr)<0){a.avcodec_free_context(&c);throw Failure("mkv_aac_encoder_open_failed");}
  if(c->frame_size!=FrameSize || c->initial_padding!=FrameSize){a.avcodec_free_context(&c);throw Failure("mkv_aac_delay_contract_changed");}
  return c;
 }
 void parameters(AVCodecParameters* target){if(a.avcodec_parameters_from_context(target,encoder)<0)throw Failure("mkv_aac_parameters_failed");}
 int64_t samples(int64_t us)const{return api().av_rescale_q(us,AV_TIME_BASE_Q,{1,Rate});}
 // Warm-up and look-ahead are fixed for a canonical window, never for a
 // requesting video fragment. Repeated/out-of-order requests get identical AAC.
 Window generate(int64_t index){
  check();if(index>0 && clockAnchor==AV_NOPTS_VALUE){cache.emplace(0,generate(0));}
  const int64_t first=index*WindowFrames*FrameSize;
  const int64_t total=samples(duration);int64_t last=std::min(total,first+WindowFrames*FrameSize);
  if(first<0 || first>=total)throw Failure("mkv_audio_window_range");
  const int64_t warm=first-WarmupFrames*FrameSize;
  const int64_t stop=last+FrameSize*2;const size_t count=size_t(stop-warm);
  std::vector<float> left(count,0),right(count,0);std::vector<uint8_t> covered(count,0);
  AVCodecContext* dec=nullptr;AVCodecContext* enc=nullptr;SwrContext* swr=nullptr;AVFrame* frame=nullptr;AVFrame* pcm=nullptr;AVChannelLayout inputLayout{};int inputFormat=-1;
  auto cleanup=[&]{if(frame)a.av_frame_free(&frame);if(pcm)a.av_frame_free(&pcm);if(dec)a.avcodec_free_context(&dec);if(enc)a.avcodec_free_context(&enc);if(swr)a.swr_free(&swr);a.av_channel_layout_uninit(&inputLayout);};
  try {
   auto* source=input->streams[stream];auto* codec=a.avcodec_find_decoder(source->codecpar->codec_id);
   if(!codec)throw Failure("mkv_audio_decoder_unavailable");dec=a.avcodec_alloc_context3(codec);
   if(!dec || a.avcodec_parameters_to_context(dec,source->codecpar)<0)throw Failure("mkv_audio_decoder_parameters");
   dec->pkt_timebase=source->time_base;dec->thread_count=1;
   if(a.avcodec_open2(dec,codec,nullptr)<0)throw Failure("mkv_audio_decoder_open_failed");
   frame=a.av_frame_alloc();pcm=a.av_frame_alloc();if(!frame || !pcm)throw Failure("mkv_memory_limit");
   // Seek earlier than the warm-up boundary so decoder and resampler reach
   // steady state before the exact, source-anchored PCM extraction interval.
   const int64_t seekUs=origin+std::max<int64_t>(0,api().av_rescale_q(warm,{1,Rate},AV_TIME_BASE_Q)-AV_TIME_BASE/2);
   // Optional Cast-owned indexed source access; no PCM/sample-grid/encoder change.
   // The callback must select a real cue no later than the same warm-up point.
   if(!sourceSeek || !sourceSeek(seekUs)){
    if(api().av_seek_frame(input,stream,api().av_rescale_q(seekUs,AV_TIME_BASE_Q,source->time_base),AVSEEK_FLAG_BACKWARD)<0)throw Failure("mkv_audio_seek_failed");
   }
   int64_t next=AV_NOPTS_VALUE,observedEnd=0;bool complete=false,eof=false;int packets=0;
   auto receive=[&]{
    for(;;){check();int code=a.avcodec_receive_frame(dec,frame);if(code==AVERROR(EAGAIN) || code==AVERROR_EOF)return;if(code<0)throw Failure("mkv_audio_decode_failed");
     if(frame->sample_rate<=0 || frame->nb_samples<=0 || frame->nb_samples>16384 || frame->ch_layout.nb_channels<1 || frame->ch_layout.nb_channels>8 || frame->pts==AV_NOPTS_VALUE)throw Failure("mkv_audio_unverified_frame");
     if(frame->sample_rate!=Rate)throw Failure("mkv_audio_configuration_changed");
     if(swr && (frame->format!=inputFormat || a.av_channel_layout_compare(&frame->ch_layout,&inputLayout)!=0))throw Failure("mkv_audio_configuration_changed");
     if(!swr){if(a.av_channel_layout_copy(&inputLayout,&frame->ch_layout)<0)throw Failure("mkv_memory_limit");inputFormat=frame->format;AVChannelLayout stereo=AV_CHANNEL_LAYOUT_STEREO;
      if(a.swr_alloc_set_opts2(&swr,&stereo,AV_SAMPLE_FMT_FLTP,Rate,&frame->ch_layout,AVSampleFormat(frame->format),frame->sample_rate,0,nullptr)<0 || !swr || a.swr_init(swr)<0)throw Failure("mkv_audio_resampler_failed");
     }
     int64_t stampUs=api().av_rescale_q(frame->pts,source->time_base,AV_TIME_BASE_Q);
     if(stampUs==AV_NOPTS_VALUE || stampUs<origin-AV_TIME_BASE || stampUs>origin+duration+AV_TIME_BASE)throw Failure("mkv_audio_timestamp_range");
     int64_t stamp=samples(stampUs-origin);
     if(clockAnchor==AV_NOPTS_VALUE){if(index!=0 || seekUs!=origin)throw Failure("mkv_audio_clock_unverified");clockAnchor=stamp;if(clockAnchor>=samples(duration))throw Failure("mkv_audio_clock_unverified");}
     if(next==AV_NOPTS_VALUE){
      // EAC3 consists of 256-sample audio blocks (not a fixed packet size).
      // Decode from the single first-frame clock, recovering block position
      // from quantized Matroska timestamps; reject ambiguous source behavior.
      int64_t blocks=api().av_rescale_q(stamp-clockAnchor,{1,1},{256,1});next=clockAnchor+blocks*256;
      if(std::abs(next-stamp)>Rate/1000 || frame->nb_samples%256)throw Failure("mkv_audio_clock_unverified");
     }
     // Matroska timestamp quantization is bounded; actual discontinuities fail.
     int64_t delayed=api().av_rescale_q(a.swr_get_delay(swr,frame->sample_rate),{1,frame->sample_rate},{1,Rate});
     if(std::abs(stamp-(next+delayed))>Rate/1000)throw Failure("mkv_audio_timestamp_discontinuity");
     constexpr int Capacity=32768;std::vector<float> l(Capacity),r(Capacity);uint8_t* dst[]={reinterpret_cast<uint8_t*>(l.data()),reinterpret_cast<uint8_t*>(r.data())};
     int n=a.swr_convert(swr,dst,Capacity,const_cast<const uint8_t**>(frame->extended_data),frame->nb_samples);if(n<0 || n>=Capacity)throw Failure("mkv_audio_resample_limit");
     for(int k=0;k<n;k++){int64_t at=next+k;if(at>=warm && at<stop){size_t slot=size_t(at-warm);if(covered[slot])throw Failure("mkv_audio_sample_overlap");covered[slot]=1;left[slot]=l[k];right[slot]=r[k];}}
     next+=n;observedEnd=std::max(observedEnd,next);complete=next>=stop;a.av_frame_unref(frame);
    }
   };
   Packet packet;
   while(!complete){check();if(++packets>250000)throw Failure("mkv_audio_packet_limit");int code=api().av_read_frame(input,packet.value);
    if(code==AVERROR_EOF){eof=true;if(a.avcodec_send_packet(dec,nullptr)<0)throw Failure("mkv_audio_decoder_drain_failed");receive();break;}
    if(code<0)throw Failure("mkv_audio_packet_read_failed");
    if(packet.value->stream_index==stream){for(int k=0;k<packet.value->side_data_elems;k++)if(packet.value->side_data[k].type==AV_PKT_DATA_ENCRYPTION_INFO || packet.value->side_data[k].type==AV_PKT_DATA_ENCRYPTION_INIT_INFO)throw Failure("drm_or_unsupported_encryption");validateDolby(packet.value,AV_CODEC_ID_EAC3);if(a.avcodec_send_packet(dec,packet.value)<0)throw Failure("mkv_audio_decode_admission_failed");receive();}
    api().av_packet_unref(packet.value);
   }
   if(eof && next==AV_NOPTS_VALUE)throw Failure("mkv_audio_empty_decode");
   if(eof){knownEnd=observedEnd;last=std::min(last,knownEnd);if(last<=first){cleanup();return Window{};}}
   const int64_t feedEnd=eof?std::min(stop,std::min(total,knownEnd)):stop;
   // Only the source-declared leading audio offset and bounded final
   // encoder padding may be synthesized. Missing interior PCM is never hidden.
   for(size_t k=0;k<count;k++){int64_t at=warm+int64_t(k);if(!covered[k] && at>=std::max<int64_t>(0,clockAnchor) && at<std::min(feedEnd,observedEnd))throw Failure("mkv_audio_sample_gap");}
   if(!complete && !eof)throw Failure("mkv_audio_incomplete_window");
   enc=openEncoder();pcm->format=enc->sample_fmt;pcm->sample_rate=Rate;pcm->ch_layout=AV_CHANNEL_LAYOUT_STEREO;pcm->nb_samples=FrameSize;
   if(a.av_frame_get_buffer(pcm,0)<0)throw Failure("mkv_audio_frame_allocation");
   Window result;
   auto encoded=[&]{for(;;){check();int code=a.avcodec_receive_packet(enc,packet.value);if(code==AVERROR(EAGAIN) || code==AVERROR_EOF)return;if(code<0)throw Failure("mkv_audio_encode_failed");
    auto* p=packet.value;
    if(p->pts==AV_NOPTS_VALUE || p->pts < -FrameSize || p->pts > stop-warm+FrameSize)throw Failure("mkv_audio_unverified_packet");int64_t at=p->pts+warm;
    if( (p->duration<=0 || p->duration>FrameSize) || p->size<=0 || p->size>65536)throw Failure("mkv_audio_unverified_packet");
    if(at>=first && at<last){Encoded item{{p->data,p->data+p->size},at,int(std::min<int64_t>(p->duration,(knownEnd>=0?std::min(total,knownEnd):total)-at)),p->flags,{}};
     if(p->side_data_elems>16)throw Failure("mkv_audio_side_data_limit");size_t sideBytes=0;for(int k=0;k<p->side_data_elems;k++){sideBytes+=p->side_data[k].size;if(sideBytes>65536)throw Failure("mkv_audio_side_data_limit");item.side.push_back({p->side_data[k].type,{p->side_data[k].data,p->side_data[k].data+p->side_data[k].size}});}result.packets.push_back(std::move(item));}api().av_packet_unref(p);
   }};
   for(int64_t at=warm;at<feedEnd;at+=FrameSize){check();if(a.av_frame_make_writable(pcm)<0)throw Failure("mkv_audio_frame_writable");
    size_t offset=size_t(at-warm);pcm->nb_samples=int(std::min<int64_t>(FrameSize,feedEnd-at));std::memcpy(pcm->data[0],left.data()+offset,pcm->nb_samples*sizeof(float));std::memcpy(pcm->data[1],right.data()+offset,pcm->nb_samples*sizeof(float));pcm->pts=at-warm;
    if(a.avcodec_send_frame(enc,pcm)<0)throw Failure("mkv_audio_encoder_admission_failed");encoded();}
   if(eof && feedEnd==std::min(total,knownEnd)){if(a.avcodec_send_frame(enc,nullptr)<0)throw Failure("mkv_audio_encoder_drain_failed");encoded();}
   const int64_t expected=(last-first+FrameSize-1)/FrameSize;
   if(int64_t(result.packets.size())!=expected)throw Failure("mkv_audio_packet_coverage");
   for(size_t k=0;k<result.packets.size();k++)if(result.packets[k].sample!=first+int64_t(k)*FrameSize)throw Failure("mkv_audio_packet_grid");
   cleanup();return result;
  }catch(...){cleanup();throw;}
 }
 std::vector<Encoded> interval(int64_t beginUs,int64_t endUs){
  int64_t first=(samples(beginUs)+FrameSize-1)/FrameSize,last=(samples(endUs)+FrameSize-1)/FrameSize;
  if(knownEnd>=0)last=std::min(last,(knownEnd+FrameSize-1)/FrameSize);
  std::vector<Encoded> out;
  for(int64_t frame=first;frame<last;){check();int64_t window=frame/WindowFrames;
   auto found=cache.find(window);if(found==cache.end()){while(cache.size()>=2)cache.erase(cache.begin());found=cache.emplace(window,generate(window)).first;}
   if(knownEnd>=0)last=std::min(last,(knownEnd+FrameSize-1)/FrameSize);
   int64_t until=std::min(last,(window+1)*WindowFrames);
   for(auto& p:found->second.packets)if(p.sample>=frame*FrameSize && p.sample<until*FrameSize)out.push_back(p);frame=until;
  }
  if(int64_t(out.size())!=std::max<int64_t>(0,last-first))throw Failure("mkv_audio_interval_coverage");return out;
 }
};

} // namespace InfinityMkv
