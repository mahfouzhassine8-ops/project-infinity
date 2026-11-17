package com.projectinfinity.kodi;

import java.util.Locale;

/** Cast-owned documented model limits, never friendly-name or VIDEO_OUT inference.
 * Unknown stays unverified; existing receiver-confirmed direct transfer remains intact.
 * This class does not advertise or implement a video transcoder.
 */
final class InfinityCastReceiverPolicy {
    enum Path { DOCUMENTED_COPY_CANDIDATE, HARDWARE_AVC_720_REQUIRED, UNVERIFIED_DIRECT }
    static final class Receiver {
        final String family;final int avcLevel,avcWidth,avcHeight,avcFps,hevcLevel;
        Receiver(String f,int l,int w,int h,int fps,int hevc){family=f;avcLevel=l;avcWidth=w;avcHeight=h;avcFps=fps;hevcLevel=hevc;}
    }
    static final class Media {
        final String codec;final int profile,level,width,height,transfer;final double fps;
        Media(String c,int p,int l,int w,int h,long numerator,long denominator,int t){codec=c;profile=p;level=l;width=w;height=h;fps=numerator>0 && denominator>0?(double)numerator/denominator:0;transfer=t;}
        boolean hdr(){return transfer==16 || transfer==18;} // Main10 alone is not HDR.
        boolean described(){return width>0 && height>0 && fps>0 && Double.isFinite(fps) && level>0 && profile>=0;}
    }
    static final class Choice {
        final Path path;final String reason;
        Choice(Path p,String r){path=p;reason=r;}
    }
    static Receiver receiver(String sdkModel) {
        String model=sdkModel==null?"":sdkModel.trim().toLowerCase(Locale.ROOT);
        switch(model) {
            case "google home hub":case "google nest hub":case "google nest hub (2nd gen)":
                return new Receiver("nest_hub",41,1280,720,60,0);
            case "nest hub max":case "google nest hub max":return new Receiver("nest_hub_max",41,1280,720,30,0);
            case "chromecast ultra":return new Receiver("chromecast_ultra",42,1920,1080,60,153);
            // Explicit4K SKU only: generic Chromecast/GoogleTV strings are ambiguous.
            case "chromecast with google tv (4k)":return new Receiver("chromecast_google_tv_4k",51,3840,2160,30,153);
            case "google tv streamer":case "google tv streamer (4k)":return new Receiver("google_tv_streamer",52,3840,2160,60,153);
            default:return new Receiver("unknown",0,0,0,0,-1);
        }
    }
    static Choice choose(Receiver receiver,Media media) {
        if(receiver.hevcLevel<0)return new Choice(Path.UNVERIFIED_DIRECT,"receiver_capability_unknown");
        if("hevc".equals(media.codec) && receiver.hevcLevel==0)return new Choice(Path.HARDWARE_AVC_720_REQUIRED,"receiver_hevc_not_documented");
        if(!media.described())return new Choice(Path.UNVERIFIED_DIRECT,"source_video_limits_unverified");
        boolean fits;
        if("hevc".equals(media.codec))fits=(media.profile==1 || media.profile==2) && media.level<=receiver.hevcLevel && media.width<=3840 && media.height<=2160 && media.fps<=60;
        else if("h264".equals(media.codec)) {
            int profile=media.profile&255;
            fits=(profile==66 || profile==77 || profile==100) && media.level<=receiver.avcLevel && media.width<=receiver.avcWidth && media.height<=receiver.avcHeight && media.fps<=receiver.avcFps;
        } else return new Choice(Path.UNVERIFIED_DIRECT,"source_codec_unverified");
        return fits?new Choice(Path.DOCUMENTED_COPY_CANDIDATE,"documented_video_limits_match"):new Choice(Path.HARDWARE_AVC_720_REQUIRED,"receiver_video_limits_exceeded");
    }
}
