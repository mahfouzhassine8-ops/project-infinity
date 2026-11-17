#pragma once
namespace InfinityMkv {
struct CastVideoPacket {std::vector<uint8_t> data;int64_t pts=0,duration=0;int flags=0;};
struct CastVideoResult {
 int width=0,height=0,profile=0,level=0;std::vector<uint8_t> config;std::vector<CastVideoPacket> packets;
 static CastVideoResult parse(const std::vector<uint8_t>& data,int64_t begin,int64_t end){
  if(data.size()>FragmentLimit)throw Failure("cast_hw_batch_limit");size_t at=0;
  auto word=[&]()->uint32_t{if(data.size()-at<4)throw Failure("cast_hw_batch_truncated");uint32_t n=0;for(int k=0;k<4;k++)n=(n<<8)|data[at++];return n;};
  auto wide=[&]()->int64_t{uint64_t n=uint64_t(word())<<32;n|=word();if(n>uint64_t(INT64_MAX))throw Failure("cast_hw_batch_timestamp");return int64_t(n);};
  if(word()!=0x43564831)throw Failure("cast_hw_batch_version");CastVideoResult r;r.width=int(word());r.height=int(word());r.profile=int(word());r.level=int(word());
  if(r.width!=1280||r.height!=720||(r.profile!=66&&r.profile!=77&&r.profile!=100)||r.level<=0||r.level>41||word()!=1)throw Failure("cast_hw_batch_format");
  uint32_t size=word();if(size<7||size>65536||size>data.size()-at)throw Failure("cast_hw_batch_config");r.config.assign(data.begin()+at,data.begin()+at+size);at+=size;
  if(r.config[0]!=1||r.config[4]!=255||r.config[5]!=225||r.config[1]!=r.profile||r.config[3]!=r.level||r.config.size()<15)throw Failure("cast_hw_batch_config");
  size_t sps=(size_t(r.config[6])<<8)|r.config[7];
  if(sps<4||sps>r.config.size()-12||(r.config[8]&31)!=7||(r.config[8]&128)||(r.config[8]&96)==0||r.config[9]!=r.profile||r.config[11]!=r.level||r.config[8+sps]!=1)throw Failure("cast_hw_batch_config");
  size_t pps=(size_t(r.config[9+sps])<<8)|r.config[10+sps];
  if(pps<1||pps!=r.config.size()-11-sps||(r.config[11+sps]&31)!=8||(r.config[11+sps]&128)||(r.config[11+sps]&96)==0)throw Failure("cast_hw_batch_config");
  uint32_t count=word();if(!count||count>1000)throw Failure("cast_hw_batch_count");int64_t previous=-1;
  for(uint32_t n=0;n<count;n++){CastVideoPacket p;p.pts=wide();p.duration=wide();p.flags=int(word());uint32_t bytes=word();
   if(p.pts<begin||p.pts>=end||p.pts<=previous||p.duration<=0||p.duration>end-p.pts||p.flags<0||p.flags>1||bytes<5||bytes>data.size()-at)throw Failure("cast_hw_batch_packet");
   p.data.assign(data.begin()+at,data.begin()+at+bytes);at+=bytes;previous=p.pts;r.packets.push_back(std::move(p));
  }
  if(at!=data.size())throw Failure("cast_hw_batch_trailing");for(size_t n=0;n+1<r.packets.size();n++)if(r.packets[n].pts+r.packets[n].duration!=r.packets[n+1].pts)throw Failure("cast_hw_batch_gap");
  return r;
 }
};
struct CastVideoBridge {
 virtual ~CastVideoBridge()=default;
 virtual void begin(const std::string&,const std::vector<uint8_t>&,const std::vector<uint8_t>&,int64_t,int64_t)=0;
 virtual void offer(const std::vector<uint8_t>&,int64_t)=0;
 virtual std::vector<uint8_t> finish()=0;
 virtual void abort()=0;
 virtual void qualifyDelivery(int64_t,int64_t)=0;
};
struct CastVideoSource {
 static std::pair<std::vector<uint8_t>,std::vector<uint8_t>> configuration(const AVCodecParameters* p){
  const uint8_t* b=p->extradata;size_t size=size_t(p->extradata_size),at;std::vector<uint8_t> first,second;
  if(!b||size<7||size>65536||b[0]!=1)throw Failure("cast_hw_source_configuration");
  auto nal=[&](std::vector<uint8_t>& out){if(size-at<2)throw Failure("cast_hw_source_configuration");size_t n=(size_t(b[at])<<8)|b[at+1];at+=2;if(n<2||n>size-at||out.size()+n+4>65536)throw Failure("cast_hw_source_configuration");out.insert(out.end(),{0,0,0,1});out.insert(out.end(),b+at,b+at+n);at+=n;};
  if(p->codec_id==AV_CODEC_ID_HEVC){if(size<23)throw Failure("cast_hw_source_configuration");if(b[1]&32)throw Failure("cast_hw_source_high_tier_unsupported");at=23;unsigned count=0;for(unsigned n=0;n<b[22];n++){if(size-at<3)throw Failure("cast_hw_source_configuration");unsigned type=b[at++]&63;unsigned units=(unsigned(b[at])<<8)|b[at+1];at+=2;for(unsigned k=0;k<units;k++){if(++count>1024)throw Failure("cast_hw_source_configuration");std::vector<uint8_t> temp;nal(temp);if(type==32||type==33||type==34)first.insert(first.end(),temp.begin(),temp.end());}}if(at!=size||first.empty())throw Failure("cast_hw_source_configuration");}
  else if(p->codec_id==AV_CODEC_ID_H264){at=6;for(unsigned n=0;n<(b[5]&31);n++)nal(first);if(at>=size)throw Failure("cast_hw_source_configuration");unsigned count=b[at++];for(unsigned n=0;n<count;n++)nal(second);if(first.empty()||second.empty())throw Failure("cast_hw_source_configuration");}
  else throw Failure("cast_hw_source_codec");return {std::move(first),std::move(second)};
 }
 static std::vector<uint8_t> accessUnit(const AVCodecParameters* p,const AVPacket* packet){
  if(packet->size<=0||packet->size>4*1024*1024)throw Failure("cast_hw_source_packet_limit");int bytes=p->codec_id==AV_CODEC_ID_H264?(p->extradata[4]&3)+1:(p->extradata[21]&3)+1;std::vector<uint8_t> out;size_t at=0,total=size_t(packet->size);
  while(at<total){if(total-at<size_t(bytes))throw Failure("cast_hw_source_nal_length");uint32_t n=0;for(int k=0;k<bytes;k++)n=(n<<8)|packet->data[at++];if(n<1||n>total-at||out.size()+n+4>4*1024*1024)throw Failure("cast_hw_source_nal_length");out.insert(out.end(),{0,0,0,1});out.insert(out.end(),packet->data+at,packet->data+at+n);at+=n;}return out;
 }
};
} // namespace InfinityMkv
