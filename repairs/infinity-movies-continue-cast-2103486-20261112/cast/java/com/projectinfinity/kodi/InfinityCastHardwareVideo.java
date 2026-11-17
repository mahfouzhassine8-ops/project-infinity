package com.projectinfinity.kodi;

import android.content.Context;
import android.media.*;
import android.os.*;
import android.view.Surface;
import java.io.*;
import java.nio.*;
import java.util.*;
import java.util.concurrent.atomic.AtomicBoolean;
import org.json.*;

/** Cast-only decoder -> GPU -> AVC. Production never selects software video. */
final class InfinityCastHardwareVideo implements AutoCloseable {
 interface Factory {InfinityCastHardwareVideo create()throws IOException;}
 private static final String CI_PACKAGE="com.projectinfinity.castqa.pipeline";
 private final Context context;private final boolean ciSoftware;
 private final AtomicBoolean cancelled=new AtomicBoolean();
 private MediaCodec decoder,encoder;private Surface encoderInput;private InfinityCastGpuSurface gpu;
 private boolean decoderStarted,encoderStarted,decoderEos,encoderEos,signalledEncoder,requestSdr,decoderFormatVerified;
 private final Set<Long> inputTimestamps=new HashSet<>();
 private final ArrayDeque<Long> presentedTimestamps=new ArrayDeque<>();private double sourceFps;
 private long deliveredSpan,deliveredTime;
 private long owner=-1,deadline,begin,end,lastSlot,lastDecoded,lastEncoded,activeNanos,frames,totalSpan,totalActive;
 private int inputWidth,inputHeight,bytes,thermalSamples;
 private byte[] avcc;private final List<InfinityCastVideoContract.Packet> packets=new ArrayList<>();
 InfinityCastHardwareVideo(Context context)throws IOException{this(context,false);}
 /** CI reflection only; both exact separate package and small raster are enforced. */
 private InfinityCastHardwareVideo(Context context,boolean ciSoftware)throws IOException{this.context=context.getApplicationContext();this.ciSoftware=ciSoftware;need(!ciSoftware||CI_PACKAGE.equals(context.getPackageName()),"cast_hw_software_forbidden");}
 private static void need(boolean v,String reason)throws IOException{InfinityCastVideoContract.require(v,reason);}
 private void owner()throws IOException{need(owner==Thread.currentThread().getId(),"cast_hw_wrong_owner");}
 void cancel(){cancelled.set(true);InfinityCastGpuSurface current=gpu;if(current!=null)current.wake();}
 private void check()throws IOException {
  need(!cancelled.get(),"cast_hw_video_cancelled");need(SystemClock.elapsedRealtime()<deadline,"cast_hw_video_deadline");
  if(++thermalSamples%16==0&&!ciSoftware){PowerManager p=(PowerManager)context.getSystemService(Context.POWER_SERVICE);need(p!=null&&p.getCurrentThermalStatus()<PowerManager.THERMAL_STATUS_SEVERE,"cast_hw_thermal_limit");}
 }
 private static int level(String mime,int nativeLevel)throws IOException {
  if(mime.equals("video/hevc")){int[] l={30,60,63,90,93,120,123,150,153,156,180,183,186};for(int n=0;n<l.length;n++)if(l[n]==nativeLevel)return 1<<(2*n);}
  else {int[] l={10,9,11,12,13,20,21,22,30,31,32,40,41,42,50,51,52};for(int n=0;n<l.length;n++)if(l[n]==nativeLevel)return 1<<n;}
  throw new IOException("cast_hw_source_level_unknown");
 }
 private static String codecCode(String name){String value=name.toLowerCase(java.util.Locale.ROOT).replaceAll("[^a-z0-9_]","_");return value.matches("[a-z][a-z0-9_]{0,63}")?value:"component_name_unavailable";}
 private MediaCodecInfo choose(String mime,boolean encode,MediaFormat format)throws IOException {
  for(MediaCodecInfo info:new MediaCodecList(MediaCodecList.ALL_CODECS).getCodecInfos()){
   if(info.isAlias()||info.isEncoder()!=encode)continue;
   if(ciSoftware?!info.isSoftwareOnly():(!info.isHardwareAccelerated()||info.isSoftwareOnly()))continue;
   for(String type:info.getSupportedTypes())if(type.equals(mime))try{
    MediaCodecInfo.CodecCapabilities caps=info.getCapabilitiesForType(type);
    if(caps.isFormatSupported(format))return info;
   }catch(IllegalArgumentException unsupported){}
  }
  throw new IOException(encode?"cast_hw_avc_encoder_unavailable":"cast_hw_decoder_format_unavailable");
 }
 /** Invoked synchronously by the Cast native owner, before any phone pause. */
 void begin(String description,byte[] csd0,byte[] csd1,long beginUs,long endUs)throws IOException {
  long entered=System.nanoTime();owner=Thread.currentThread().getId();deadline=SystemClock.elapsedRealtime()+14000;
  try{
   check();JSONObject budget=new JSONObject(description);long remaining=budget.getLong("budget_ms");need(remaining>0,"cast_hw_video_deadline");deadline=SystemClock.elapsedRealtime()+Math.min(14000,remaining);need(decoder==null&&encoder==null&&gpu==null,"cast_hw_previous_segment_alive");JSONObject c=new JSONObject(description);
   inputWidth=c.getInt("width");inputHeight=c.getInt("height");long fpsNum=c.getLong("fps_num"),fpsDen=c.getLong("fps_den");need(inputWidth>0&&inputHeight>0&&inputWidth<=8192&&inputHeight<=4320&&fpsNum>0&&fpsDen>0,"cast_hw_source_geometry");double fps=(double)fpsNum/fpsDen;sourceFps=fps;need(fps>0&&fps<=120,"cast_hw_source_rate");
   need(!ciSoftware||(inputWidth<=640&&inputHeight<=360&&fps<=30),"cast_hw_software_raster_forbidden");need(beginUs>=0&&endUs>beginUs&&endUs-beginUs<=30000000,"cast_hw_segment_window");
   if(!ciSoftware){PowerManager power=(PowerManager)context.getSystemService(Context.POWER_SERVICE);need(power!=null&&power.getCurrentThermalStatus()<PowerManager.THERMAL_STATUS_MODERATE,"cast_hw_thermal_unavailable");}
   String codec=c.getString("video");String mime=codec.equals("hevc")?"video/hevc":codec.equals("h264")?"video/avc":"";need(!mime.isEmpty(),"cast_hw_source_codec");int profile=c.getInt("profile"),trc=c.getInt("transfer");
   MediaFormat source=MediaFormat.createVideoFormat(mime,inputWidth,inputHeight);source.setFloat(MediaFormat.KEY_FRAME_RATE,(float)fps);source.setInteger(MediaFormat.KEY_MAX_INPUT_SIZE,4*1024*1024);
   if(mime.equals("video/hevc")){need(profile==1||profile==2,"cast_hw_source_profile");source.setInteger(MediaFormat.KEY_PROFILE,profile==2?MediaCodecInfo.CodecProfileLevel.HEVCProfileMain10:MediaCodecInfo.CodecProfileLevel.HEVCProfileMain);}
   else {int p=profile&255;need(p==66||p==77||p==100,"cast_hw_source_profile");source.setInteger(MediaFormat.KEY_PROFILE,p==66?MediaCodecInfo.CodecProfileLevel.AVCProfileBaseline:p==77?MediaCodecInfo.CodecProfileLevel.AVCProfileMain:MediaCodecInfo.CodecProfileLevel.AVCProfileHigh);}
   int primaries=c.optInt("primaries",0),matrix=c.optInt("matrix",0),range=c.optInt("range",0);
   boolean bt709=primaries==1&&matrix==1,bt2020=primaries==9&&matrix==9;
   need(bt709||bt2020,"cast_hw_source_color_tuple_unsupported");
   source.setInteger(MediaFormat.KEY_COLOR_STANDARD,bt709?MediaFormat.COLOR_STANDARD_BT709:MediaFormat.COLOR_STANDARD_BT2020);
   if(range==1||range==2)source.setInteger(MediaFormat.KEY_COLOR_RANGE,range==1?MediaFormat.COLOR_RANGE_LIMITED:MediaFormat.COLOR_RANGE_FULL);
   source.setInteger(MediaFormat.KEY_LEVEL,level(mime,c.getInt("level")));source.setByteBuffer("csd-0",ByteBuffer.wrap(csd0));if(csd1!=null&&csd1.length>0)source.setByteBuffer("csd-1",ByteBuffer.wrap(csd1));
   requestSdr=trc!=1&&trc!=6&&trc!=13; // Unknown requires verified conversion, not an SDR guess.
   if(requestSdr){need(Build.VERSION.SDK_INT>=31,"cast_hw_sdr_request_unavailable");source.setInteger("color-transfer-request",MediaFormat.COLOR_TRANSFER_SDR_VIDEO);}
   if(trc==16||trc==18){source.setInteger(MediaFormat.KEY_COLOR_TRANSFER,trc==16?MediaFormat.COLOR_TRANSFER_ST2084:MediaFormat.COLOR_TRANSFER_HLG);need(bt2020,"cast_hw_hdr_color_tuple_unsupported");}
   MediaFormat target=MediaFormat.createVideoFormat("video/avc",1280,720);target.setInteger(MediaFormat.KEY_COLOR_FORMAT,MediaCodecInfo.CodecCapabilities.COLOR_FormatSurface);target.setInteger(MediaFormat.KEY_BIT_RATE,2000000);target.setFloat(MediaFormat.KEY_FRAME_RATE,(float)Math.min(30,fps));target.setInteger(MediaFormat.KEY_I_FRAME_INTERVAL,2);target.setInteger(MediaFormat.KEY_PROFILE,MediaCodecInfo.CodecProfileLevel.AVCProfileBaseline);target.setInteger(MediaFormat.KEY_LEVEL,MediaCodecInfo.CodecProfileLevel.AVCLevel31);target.setInteger(MediaFormat.KEY_MAX_B_FRAMES,0);target.setInteger(MediaFormat.KEY_COLOR_STANDARD,MediaFormat.COLOR_STANDARD_BT709);target.setInteger(MediaFormat.KEY_COLOR_TRANSFER,MediaFormat.COLOR_TRANSFER_SDR_VIDEO);target.setInteger(MediaFormat.KEY_COLOR_RANGE,MediaFormat.COLOR_RANGE_LIMITED);
   MediaCodecInfo enc=choose("video/avc",true,target),dec=choose(mime,false,source);check();
   InfinityCastDiagnostics.event("hw_decoder",codecCode(dec.getName()),profile);InfinityCastDiagnostics.event("hw_encoder",codecCode(enc.getName()),31);InfinityCastDiagnostics.event("hw_source","width",inputWidth);InfinityCastDiagnostics.event("hw_source","height",inputHeight);InfinityCastDiagnostics.event("hw_source","fps_milli",(int)Math.round(fps*1000));InfinityCastDiagnostics.event("hw_source","transfer",trc);InfinityCastDiagnostics.event("hw_capability","decoder_instances_declared",dec.getCapabilitiesForType(mime).getMaxSupportedInstances());InfinityCastDiagnostics.event("hw_capability","encoder_instances_declared",enc.getCapabilitiesForType("video/avc").getMaxSupportedInstances());
   encoder=MediaCodec.createByCodecName(enc.getName());encoder.configure(target,null,null,MediaCodec.CONFIGURE_FLAG_ENCODE);encoderInput=encoder.createInputSurface();encoder.start();encoderStarted=true;
   gpu=new InfinityCastGpuSurface(encoderInput,inputWidth,inputHeight,c.optInt("sar_num",1),c.optInt("sar_den",1));decoder=MediaCodec.createByCodecName(dec.getName());decoder.configure(source,gpu.decoderSurface(),null,0);
   if(requestSdr)need(decoder.getInputFormat().getInteger("color-transfer-request",0)==MediaFormat.COLOR_TRANSFER_SDR_VIDEO,"cast_hw_tonemap_not_supported");decoder.start();decoderStarted=true;
   begin=beginUs;end=endUs;lastSlot=InfinityCastVideoContract.firstSlot(begin)-1;lastDecoded=lastEncoded=-1;frames=bytes=0;activeNanos=0;packets.clear();avcc=null;decoderEos=encoderEos=signalledEncoder=decoderFormatVerified=false;inputTimestamps.clear();presentedTimestamps.clear();
   InfinityCastDiagnostics.event("hardware_video",ciSoftware?"ci_small_software_backend":"hardware_pair_configured",0);
  }catch(Throwable e){try{releaseSegment();}catch(IOException cleanup){e.addSuppressed(cleanup);}if(e instanceof IOException)throw (IOException)e;if(e instanceof Error)throw (Error)e;throw new IOException("cast_hw_codec_configure");}
  finally{activeNanos+=System.nanoTime()-entered;}
 }
 void offer(byte[] accessUnit,long ptsUs)throws IOException {
  long entered=System.nanoTime();try{owner();check();need(accessUnit!=null&&accessUnit.length>0&&accessUnit.length<=4*1024*1024,"cast_hw_input_limit");int index;
   while((index=decoder.dequeueInputBuffer(0))<0){pump();check();pause();}
   ByteBuffer target=decoder.getInputBuffer(index);need(target!=null&&target.capacity()>=accessUnit.length,"cast_hw_decoder_input_capacity");target.clear();target.put(accessUnit);need(inputTimestamps.add(ptsUs)&&inputTimestamps.size()<=2000,"cast_hw_source_duplicate_pts");decoder.queueInputBuffer(index,0,accessUnit.length,ptsUs,0);pump();
  }catch(RuntimeException e){throw new IOException("cast_hw_codec_feed");}finally{activeNanos+=System.nanoTime()-entered;}
 }
 private void pause()throws IOException{try{Thread.sleep(1);}catch(InterruptedException e){Thread.currentThread().interrupt();throw new IOException("cast_hw_interrupted");}}
 private void pump()throws IOException {
  check();drainEncoder();MediaCodec.BufferInfo info=new MediaCodec.BufferInfo();
  for(int n=0;n<16&&!decoderEos;n++){
   int index=decoder.dequeueOutputBuffer(info,0);if(index==MediaCodec.INFO_TRY_AGAIN_LATER)break;
   if(index==MediaCodec.INFO_OUTPUT_FORMAT_CHANGED){MediaFormat f=decoder.getOutputFormat();need(f.getInteger(MediaFormat.KEY_COLOR_TRANSFER,-1)==MediaFormat.COLOR_TRANSFER_SDR_VIDEO&&f.getInteger(MediaFormat.KEY_COLOR_STANDARD,-1)==MediaFormat.COLOR_STANDARD_BT709,"cast_hw_sdr_output_unverified");int w=f.getInteger(MediaFormat.KEY_WIDTH),h=f.getInteger(MediaFormat.KEY_HEIGHT);int left=f.getInteger("crop-left",0),top=f.getInteger("crop-top",0);need(f.getInteger("crop-right",w-1)-left+1==inputWidth&&f.getInteger("crop-bottom",h-1)-top+1==inputHeight,"cast_hw_decoder_geometry_changed");decoderFormatVerified=true;continue;}
   if(index<0)continue;boolean eos=(info.flags&MediaCodec.BUFFER_FLAG_END_OF_STREAM)!=0;
   boolean render=info.size>0&&info.presentationTimeUs>=begin&&info.presentationTimeUs<end;
   if(render){need(decoderFormatVerified&&inputTimestamps.remove(info.presentationTimeUs),"cast_hw_decoder_format_or_timestamp");need(info.presentationTimeUs>lastDecoded,"cast_hw_decoder_pts_order");lastDecoded=info.presentationTimeUs;render=InfinityCastVideoContract.select(info.presentationTimeUs,begin,end,sourceFps,lastSlot);if(render)lastSlot=InfinityCastVideoContract.slot(info.presentationTimeUs);}
   long pts=info.presentationTimeUs;decoder.releaseOutputBuffer(index,render);
   if(render){drainEncoder();presentedTimestamps.addLast(pts);gpu.render(pts,this::check);frames++;drainEncoder();}
   if(eos){need(inputTimestamps.isEmpty(),"cast_hw_decoder_frame_loss");decoderEos=true;}
  }
  if(decoderEos&&!signalledEncoder){encoder.signalEndOfInputStream();signalledEncoder=true;}drainEncoder();
 }
 private static byte[] copy(ByteBuffer b){if(b==null)return null;ByteBuffer value=b.duplicate();byte[] out=new byte[value.remaining()];value.get(out);return out;}
 private void drainEncoder()throws IOException {
  MediaCodec.BufferInfo info=new MediaCodec.BufferInfo();for(int n=0;n<32&&!encoderEos;n++){
   check();int index=encoder.dequeueOutputBuffer(info,0);if(index==MediaCodec.INFO_TRY_AGAIN_LATER)return;
   if(index==MediaCodec.INFO_OUTPUT_FORMAT_CHANGED){MediaFormat format=encoder.getOutputFormat();need(format.getInteger(MediaFormat.KEY_WIDTH)==1280&&format.getInteger(MediaFormat.KEY_HEIGHT)==720,"cast_hw_encoder_geometry_changed");need(format.getInteger(MediaFormat.KEY_COLOR_STANDARD,-1)==MediaFormat.COLOR_STANDARD_BT709&&format.getInteger(MediaFormat.KEY_COLOR_TRANSFER,-1)==MediaFormat.COLOR_TRANSFER_SDR_VIDEO&&format.getInteger(MediaFormat.KEY_COLOR_RANGE,-1)==MediaFormat.COLOR_RANGE_LIMITED,"cast_hw_encoder_color_unverified");byte[] config=InfinityCastVideoContract.configuration(copy(format.getByteBuffer("csd-0")),copy(format.getByteBuffer("csd-1")));need(avcc==null||Arrays.equals(avcc,config),"cast_hw_encoder_config_changed");avcc=config;continue;}
   if(index<0)continue;
   try{if(info.size>0&&(info.flags&MediaCodec.BUFFER_FLAG_CODEC_CONFIG)==0){need(avcc!=null,"cast_hw_encoder_config_missing");ByteBuffer data=encoder.getOutputBuffer(index);need(data!=null&&info.offset>=0&&info.size<=data.capacity()-info.offset,"cast_hw_encoder_buffer");data.position(info.offset);data.limit(info.offset+info.size);byte[] sample=InfinityCastVideoContract.sample(copy(data),avcc);need(info.presentationTimeUs>=begin&&info.presentationTimeUs<end&&info.presentationTimeUs>lastEncoded,"cast_hw_encoder_pts_order");need(!presentedTimestamps.isEmpty()&&presentedTimestamps.removeFirst()==info.presentationTimeUs,"cast_hw_encoder_pts_shift");lastEncoded=info.presentationTimeUs;bytes+=sample.length;need(bytes<=InfinityCastVideoContract.LIMIT&&packets.size()<1000,"cast_hw_encoder_memory_limit");packets.add(new InfinityCastVideoContract.Packet(sample,info.presentationTimeUs,InfinityCastVideoContract.idr(sample)));}if((info.flags&MediaCodec.BUFFER_FLAG_END_OF_STREAM)!=0)encoderEos=true;}finally{encoder.releaseOutputBuffer(index,false);}
  }
 }
 byte[] finish()throws IOException {
  long entered=System.nanoTime();try{owner();check();int index;while((index=decoder.dequeueInputBuffer(0))<0){pump();check();pause();}decoder.queueInputBuffer(index,0,0,end,MediaCodec.BUFFER_FLAG_END_OF_STREAM);
   while(!encoderEos){pump();check();pause();}
   need(frames==packets.size()&&presentedTimestamps.isEmpty(),"cast_hw_encoder_frame_loss");long active=activeNanos+System.nanoTime()-entered,span=(end-begin)*1000;totalSpan+=span;totalActive+=active;
   // Emulator software correctness never qualifies production throughput.
   if(!ciSoftware){need(span>=100000000L&&active*4<=span*3,"cast_hw_sample_not_realtime");need(totalActive*10<=totalSpan*9,"cast_hw_sustained_not_realtime");}
   byte[] output=InfinityCastVideoContract.batch(avcc,packets,begin,end);InfinityCastDiagnostics.event("hardware_video",ciSoftware?"ci_correctness_only":"video_stage_sample",(int)Math.min(Integer.MAX_VALUE,active/1000000));return output;
  }catch(RuntimeException e){throw new IOException("cast_hw_codec_drain");}finally{releaseSegment();}
 }
 void qualifyDelivery(long elapsedMs,long spanMs)throws IOException {
  if(ciSoftware)return;need(elapsedMs>=0&&spanMs>0&&elapsedMs*10<=spanMs*9,"cast_hw_delivery_not_realtime");deliveredTime+=elapsedMs;deliveredSpan+=spanMs;need(deliveredTime*10<=deliveredSpan*9,"cast_hw_delivery_not_realtime");InfinityCastDiagnostics.event("hardware_video",deliveredSpan>=30000?"cumulative_delivery_samples":"delivery_sample",(int)Math.min(Integer.MAX_VALUE,elapsedMs));
 }
 boolean idle(){return decoder==null&&encoder==null&&gpu==null&&encoderInput==null;}
 /** All release operations stay on the converter owner, never UI/cancel threads. */
 void abortSegment()throws IOException{owner();releaseSegment();}
 private void releaseSegment()throws IOException {
  IOException problem=null;
  if(decoder!=null){try{if(decoderStarted)decoder.stop();}catch(Throwable e){problem=new IOException("cast_hw_decoder_stop");}finally{try{decoder.release();decoder=null;decoderStarted=false;}catch(Throwable e){problem=new IOException("cast_hw_decoder_release");}}}
  if(encoder!=null){try{if(encoderStarted)encoder.stop();}catch(Throwable e){problem=new IOException("cast_hw_encoder_stop");}finally{try{encoder.release();encoder=null;encoderStarted=false;}catch(Throwable e){problem=new IOException("cast_hw_encoder_release");}}}
  if(gpu!=null){try{gpu.close();gpu=null;}catch(IOException e){problem=e;}}
  if(encoderInput!=null){encoderInput.release();encoderInput=null;}packets.clear();avcc=null;
  if(problem!=null)throw problem;
 }
 @Override public void close()throws IOException{cancel();if(!idle()&&owner!=Thread.currentThread().getId())throw new IOException("cast_hw_wrong_cleanup_owner");releaseSegment();}
}
