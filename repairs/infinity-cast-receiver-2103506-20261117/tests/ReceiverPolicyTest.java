package com.projectinfinity.kodi;
public final class ReceiverPolicyTest {
 static int checks;
 static InfinityCastReceiverPolicy.Media video(String codec,int profile,int level,int width,int height,int fps,int trc){return new InfinityCastReceiverPolicy.Media(codec,profile,level,width,height,fps,1,trc);}
 static void check(boolean x,String reason){checks++;if(!x)throw new AssertionError(reason);}
 static InfinityCastReceiverPolicy.Path path(String model,InfinityCastReceiverPolicy.Media m){return InfinityCastReceiverPolicy.choose(InfinityCastReceiverPolicy.receiver(model),m).path;}
 public static void main(String[] args){
  InfinityCastReceiverPolicy.Path copy=InfinityCastReceiverPolicy.Path.DOCUMENTED_COPY_CANDIDATE,hw=InfinityCastReceiverPolicy.Path.HARDWARE_AVC_720_REQUIRED,unknown=InfinityCastReceiverPolicy.Path.UNVERIFIED_DIRECT;
  InfinityCastReceiverPolicy.Media hevc=video("hevc",2,153,3840,2160,24,1),avc=video("h264",100,41,1280,720,30,1);
  for(String hub:new String[]{"Google Nest Hub","Google Home Hub","Google Nest Hub (2nd gen)","Google Nest Hub Max","Nest Hub Max"}){check(path(hub,hevc)==hw,"HEVC never documented on Hub");check(path(hub,avc)==copy,"720p AVC retained");}
  for(String model:new String[]{"Chromecast Ultra","Chromecast with Google TV (4K)","Google TV Streamer","Google TV Streamer (4K)"}){check(path(model,hevc)==copy,"4KHEVC retained");check(path(model,video("hevc",2,156,3840,2160,24,1))==hw,"HEVC abovelevel");check(path(model,video("hevc",4,153,3840,2160,24,1))==hw,"unsupportedprofile");}
  check(path("Google Nest Hub",video("h264",100,41,1280,720,60,1))==copy,"Hub60fps");check(path("Nest Hub Max",video("h264",100,41,1280,720,60,1))==hw,"Max30fps");
  check(path("Google Nest Hub",video("h264",100,41,1920,1080,30,1))==hw,"1080overHub");check(path("Google Nest Hub",video("h264",110,41,1280,720,30,1))==hw,"High10notHigh");check(path("Google Nest Hub",video("h264",578,31,1280,720,30,1))==copy,"constrainedbaseline");
  for(String model:new String[]{"Onn 4k","Chromecast","Chromecast with Google TV","Bedroom Nest Hub","My Google TV 4K",null})check(path(model,hevc)==unknown,"unknown must notbeadvertisedcompatible");
  check(!hevc.hdr(),"Main10notHDR");check(video("hevc",2,153,3840,2160,24,16).hdr(),"PQrecognized");check(video("hevc",2,153,3840,2160,24,18).hdr(),"HLGrecognized");
  check(path("Chromecast Ultra",video("hevc",2,153,0,0,0,2))==unknown,"missingfacts");check(path("Chromecast Ultra",video("hevc",2,153,3840,2160,120,1))==hw,"fpslimit");check(path("Chromecast Ultra",video("hevc",2,153,7680,4320,24,1))==hw,"8knot4k");
  check(path("Google Nest Hub",video("h264",100,41,1920,1080,0,1))==hw,"knownwidthcannotbypasswithmissingfps");
  check(path("Google Nest Hub",video("h264",110,41,1280,720,0,1))==hw,"knownHigh10cannotbypasswithmissingfps");
  check(path("Chromecast Ultra",video("hevc",-1,153,7680,4320,0,2))==hw,"known8kcannotbypassmissingprofilefps");
  check(path("Google Nest Hub",video("h264",100,41,1280,720,30,16))==hw,"HDRneedsverifiedtonemap");
  System.out.println("PASS_RECEIVER_POLICY "+checks+"; no hardwarepipeline or physicalreceiverclaim");
 }
}
