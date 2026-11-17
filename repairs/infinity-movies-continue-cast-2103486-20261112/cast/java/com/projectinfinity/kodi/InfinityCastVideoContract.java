package com.projectinfinity.kodi;
import java.io.*;import java.util.*;

/** Bounded compressed AVC records only; no raw decoded pixels. */
final class InfinityCastVideoContract {
 static final int LIMIT=8*1024*1024;
 static void require(boolean v,String reason)throws IOException{if(!v)throw new IOException(reason);}
 static List<byte[]> annexB(byte[] data)throws IOException {
  require(data!=null&&data.length>0&&data.length<=LIMIT,"cast_hw_avc_packet_limit");List<byte[]> result=new ArrayList<>();int at=0;
  while(at<data.length){int prefix=start(data,at);require(prefix>0,"cast_hw_avc_annexb");int begin=at+prefix,end=begin;while(end<data.length&&start(data,end)==0)end++;require(end>begin,"cast_hw_avc_empty_nal");require(result.size()<4096,"cast_hw_avc_nal_limit");result.add(Arrays.copyOfRange(data,begin,end));at=end;}
  validate(result);return result;
 }
 static List<byte[]> avcc(byte[] data)throws IOException {
  require(data!=null&&data.length>0&&data.length<=LIMIT,"cast_hw_avc_packet_limit");List<byte[]> result=new ArrayList<>();
  for(int at=0;at<data.length;){require(data.length-at>=4,"cast_hw_avc_length");long n=0;for(int k=0;k<4;k++)n=(n<<8)|(data[at++]&255);require(n>0&&n<=data.length-at,"cast_hw_avc_length");require(result.size()<4096,"cast_hw_avc_nal_limit");result.add(Arrays.copyOfRange(data,at,at+(int)n));at+=(int)n;}validate(result);return result;
 }
 private static void validate(List<byte[]> result)throws IOException{require(result.size()<=4096,"cast_hw_avc_nal_limit");for(byte[] n:result)require(n.length>0&&(n[0]&128)==0&&(n[0]&31)>0&&(n[0]&31)<24,"cast_hw_avc_nal_type");}
 private static int start(byte[] d,int at){return at+3<d.length&&d[at]==0&&d[at+1]==0&&d[at+2]==0&&d[at+3]==1?4:at+2<d.length&&d[at]==0&&d[at+1]==0&&d[at+2]==1?3:0;}
 static byte[] configuration(byte[] a,byte[] b)throws IOException {
  List<byte[]> all=new ArrayList<>(annexB(a));if(b!=null&&b.length>0)all.addAll(annexB(b));byte[] sps=null,pps=null;
  for(byte[] n:all){int type=n[0]&31;if(type==7){require(sps==null||Arrays.equals(sps,n),"cast_hw_avc_sps_conflict");sps=n;}if(type==8){require(pps==null||Arrays.equals(pps,n),"cast_hw_avc_pps_conflict");pps=n;}}
  require(sps!=null&&pps!=null&&sps.length>=4&&sps.length<=32767&&pps.length<=32767,"cast_hw_avc_config");int profile=sps[1]&255,level=sps[3]&255;require((profile==66||profile==77||profile==100)&&level>0&&level<=41,"cast_hw_avc_profile_level");
  ByteArrayOutputStream out=new ByteArrayOutputStream();DataOutputStream d=new DataOutputStream(out);d.write(new byte[]{1,sps[1],sps[2],sps[3],(byte)255,(byte)225});d.writeShort(sps.length);d.write(sps);d.writeByte(1);d.writeShort(pps.length);d.write(pps);return out.toByteArray();
 }
 static byte[] sample(byte[] data,byte[] config)throws IOException {
  ByteArrayOutputStream bytes=new ByteArrayOutputStream();DataOutputStream out=new DataOutputStream(bytes);boolean vcl=false;
  for(byte[] n:annexB(data)){int type=n[0]&31;if(type==7||type==8){int sn=((config[6]&255)<<8)|(config[7]&255);int at=type==7?8:11+sn;int len=type==7?sn:((config[9+sn]&255)<<8)|(config[10+sn]&255);require(at+len<=config.length&&Arrays.equals(n,Arrays.copyOfRange(config,at,at+len)),"cast_hw_avc_inline_config_changed");continue;}vcl|=type==1||type==5;out.writeInt(n.length);out.write(n);}
  require(vcl&&bytes.size()>4,"cast_hw_avc_missing_picture");return bytes.toByteArray();
 }
 static boolean idr(byte[] avcc)throws IOException{for(byte[] n:avcc(avcc))if((n[0]&31)==5)return true;return false;}
 static long firstSlot(long beginUs){return slot(beginUs);}
 static boolean select(long pts,long begin,long end,double sourceFps,long lastSlot)throws IOException {
  require(pts>=begin&&pts<end,"cast_hw_source_window");
  if(sourceFps<=30)return true;
  // The following cue owns the slot straddling its boundary. The previous
  // cue holds its last selected picture until that boundary, without a gap.
  require(slot(end)>slot(begin),"cast_hw_cue_too_short");
  return slot(pts)>lastSlot&&slot(pts)<slot(end);
 }
 static long slot(long ptsUs){return Math.floorDiv(Math.multiplyExact(ptsUs,30L),1000000L);}
 static final class Packet {final byte[] data;final long pts;final boolean key;Packet(byte[] d,long p,boolean k){data=d;pts=p;key=k;}}
 static byte[] batch(byte[] config,List<Packet> packets,long begin,long end)throws IOException {
  require(config!=null&&!packets.isEmpty()&&packets.size()<=1000,"cast_hw_video_empty");require(packets.get(0).key,"cast_hw_video_first_not_idr");ByteArrayOutputStream bytes=new ByteArrayOutputStream();DataOutputStream d=new DataOutputStream(bytes);d.writeInt(0x43564831);d.writeInt(1280);d.writeInt(720);d.writeInt(config[1]&255);d.writeInt(config[3]&255);d.writeInt(1);d.writeInt(config.length);d.write(config);d.writeInt(packets.size());long previous=-1;
  for(int n=0;n<packets.size();n++){Packet p=packets.get(n);long next=n+1<packets.size()?packets.get(n+1).pts:end;require(p.pts>=begin&&p.pts<end&&p.pts>previous&&next>p.pts,"cast_hw_video_timestamps");previous=p.pts;d.writeLong(p.pts);d.writeLong(next-p.pts);d.writeInt(p.key?1:0);d.writeInt(p.data.length);d.write(p.data);require(bytes.size()<=LIMIT,"cast_hw_video_fragment_limit");}return bytes.toByteArray();
 }
}
