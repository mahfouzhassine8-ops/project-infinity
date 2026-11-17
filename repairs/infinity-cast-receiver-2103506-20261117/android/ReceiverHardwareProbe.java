package com.projectinfinity.castqa;
import android.app.Activity;import android.os.*;import android.media.*;import android.view.Surface;import org.json.*;

/** Disposable CI package; no Infinity process, data, shutdown, or production installer. */
public final class ReceiverHardwareProbe extends Activity {
 static native String engineCapabilities();
 public void onCreate(Bundle b){super.onCreate(b);new Thread(new Runnable(){public void run(){runProbe();}},"CastReceiverHardwareInventory").start();}
 void runProbe(){JSONObject result=new JSONObject();int live=0;try{
  System.loadLibrary("castreceiverqaloader");JSONObject ff=new JSONObject(engineCapabilities());if(!ff.getBoolean("engine_loaded") || !ff.getBoolean("aac_encoder"))throw new IllegalStateException("original_engine_encoder_binding");
  JSONArray rows=new JSONArray(),hevc=new JSONArray(),avc=new JSONArray(),configured=new JSONArray();PowerManager power=(PowerManager)getSystemService(POWER_SERVICE);int thermal=power.getCurrentThermalStatus();
  for(MediaCodecInfo c:new MediaCodecList(MediaCodecList.ALL_CODECS).getCodecInfos()){
   if(c.isAlias())continue;
   for(String type:c.getSupportedTypes()){
    if(!type.equals("video/hevc")&&!type.equals("video/avc"))continue;
    JSONObject row=new JSONObject().put("name",c.getName()).put("mime",type).put("encoder",c.isEncoder()).put("hardware",c.isHardwareAccelerated()).put("software_only",c.isSoftwareOnly());
    try{
     MediaFormat f=MediaFormat.createVideoFormat(type,c.isEncoder()?1280:3840,c.isEncoder()?720:2160);f.setFloat(MediaFormat.KEY_FRAME_RATE,c.isEncoder()?30f:24f);
     if(type.equals("video/hevc")){f.setInteger(MediaFormat.KEY_PROFILE,MediaCodecInfo.CodecProfileLevel.HEVCProfileMain10);f.setInteger(MediaFormat.KEY_LEVEL,MediaCodecInfo.CodecProfileLevel.HEVCMainTierLevel51);}
     else if(c.isEncoder()){f.setInteger(MediaFormat.KEY_PROFILE,MediaCodecInfo.CodecProfileLevel.AVCProfileMain);f.setInteger(MediaFormat.KEY_LEVEL,MediaCodecInfo.CodecProfileLevel.AVCLevel31);f.setInteger(MediaFormat.KEY_COLOR_FORMAT,MediaCodecInfo.CodecCapabilities.COLOR_FormatSurface);f.setInteger(MediaFormat.KEY_BIT_RATE,3000000);f.setInteger(MediaFormat.KEY_I_FRAME_INTERVAL,2);f.setInteger(MediaFormat.KEY_MAX_B_FRAMES,0);}
     boolean supports=c.getCapabilitiesForType(type).isFormatSupported(f);row.put("requested_format_supported",supports);
     if(supports && c.isHardwareAccelerated() && !c.isSoftwareOnly()){
      if(!c.isEncoder() && type.equals("video/hevc"))hevc.put(c.getName());
      if(c.isEncoder() && type.equals("video/avc")){
       avc.put(c.getName());MediaCodec encoder=null;Surface surface=null;boolean started=false;
       try{encoder=MediaCodec.createByCodecName(c.getName());live++;encoder.configure(f,null,null,MediaCodec.CONFIGURE_FLAG_ENCODE);surface=encoder.createInputSurface();encoder.start();started=true;configured.put(new JSONObject().put("name",c.getName()).put("surface_configure_start",true));}
       catch(Exception unavailable){configured.put(new JSONObject().put("name",c.getName()).put("surface_configure_start",false).put("reason",unavailable.getClass().getSimpleName()));}
       finally{if(encoder!=null){try{if(started)encoder.stop();}finally{encoder.release();live--;}}if(surface!=null)surface.release();}
      }
     }
    }catch(Exception unsupported){row.put("format_check_error",unsupported.getClass().getSimpleName());}rows.put(row);
   }
  }
  result.put("pass",true).put("status","PASS_SELECTED_CODEC_INVENTORY").put("original_engine",ff).put("codec_inventory",rows).put("hardware_HEVC_Main10_4K24_decoders",hevc).put("hardware_AVC_720p30_encoders",avc).put("encoder_surface_configuration",configured).put("owned_codecs_after_close",live).put("thermal_status_before",thermal).put("thermal_status_after",power.getCurrentThermalStatus()).put("sustained_throughput","NOT_VERIFIED").put("HDR_to_SDR","NOT_VERIFIED").put("end_to_end_video_pipeline","NOT_IMPLEMENTED_NOT_VERIFIED").put("physical_Fold_TV","NOT_TESTED").put("engine_rebuilt",false).put("owner_data","NOT_ACCESSED");
 }catch(Throwable e){try{result.put("pass",false).put("status","FAIL_SELECTED_CODEC_INVENTORY").put("reason",e.getClass().getSimpleName()+":"+e.getMessage());}catch(Exception ignored){}}
 try{result.put("API",Build.VERSION.SDK_INT);}catch(Exception ignored){}android.util.Log.i("InfinityReceiverProbe",result.toString());}
}
