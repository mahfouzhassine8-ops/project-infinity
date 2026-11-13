package com.projectinfinity.kodi;

import java.net.URI;
import java.net.URLDecoder;
import java.nio.charset.StandardCharsets;
import java.util.Collections;
import java.util.LinkedHashMap;
import java.util.Locale;
import java.util.Map;

/** Private sender-only URL/headers from the exact native playing item.
 * This object is never handed to Cast, a receiver, diagnostics or persistence.
 */
final class InfinityCastSource {
    final URI uri;
    final Map<String,String> headers;
    final String hint;
    final Map<String,String> streamHeaders;
    private InfinityCastSource(URI uri,Map<String,String> headers,String hint) {
        this.uri=uri;this.headers=Collections.unmodifiableMap(headers);this.streamHeaders=this.headers;this.hint=hint;
    }
    static InfinityCastSource parse(String raw) {
        if(raw==null || raw.isEmpty() || raw.length()>65536)return null;
        for(int i=0;i<raw.length();i++)if(raw.charAt(i)<32 || raw.charAt(i)==127)return null;
        try {
            String[] parts=raw.split("\\|",-1);if(parts.length>2)return null;
            URI uri=new URI(parts[0]);String scheme=uri.getScheme();
            if(!("https".equalsIgnoreCase(scheme) || "http".equalsIgnoreCase(scheme)) ||
                uri.getHost()==null || uri.getRawUserInfo()!=null || uri.getRawFragment()!=null)return null;
            String path=uri.getPath()==null?"":uri.getPath().toLowerCase(Locale.ROOT);
            String hint=path.endsWith(".m3u8")?"application/vnd.apple.mpegurl":path.endsWith(".mpd")?"application/dash+xml":
                path.endsWith(".mp4") || path.endsWith(".m4v")?"video/mp4":path.endsWith(".webm")?"video/webm":
                path.endsWith(".ts")?"video/mp2t":path.endsWith(".mpeg") || path.endsWith(".mpg")?"video/mpeg":null;
            Map<String,String> headers=new LinkedHashMap<>();
            if(parts.length==2 && !parts[1].isEmpty()) {
                if(parts[1].length()>16384)return null;
                for(String field:parts[1].split("&")) {
                    int equals=field.indexOf('=');if(equals<=0)return null;
                    String name=URLDecoder.decode(field.substring(0,equals),"UTF-8").toLowerCase(Locale.ROOT);
                    String value=URLDecoder.decode(field.substring(equals+1),"UTF-8");
                    if(!(java.util.Arrays.asList("user-agent","referer","origin","cookie","authorization","accept","accept-language").contains(name) || name.matches("x-[a-z0-9-]{1,48}")) ||
                        value.length()>4096 || headers.containsKey(name))return null;
                    for(int i=0;i<value.length();i++)if(value.charAt(i)<32 || value.charAt(i)==127)return null;
                    headers.put(name,value);
                }
            }
            return new InfinityCastSource(uri,headers,hint);
        } catch(Exception invalid){return null;}
    }
    private InfinityCastSource(InfinityCastSource source,Map<String,String> manifest,Map<String,String> stream) {
        uri=source.uri;hint=source.hint;Map<String,String> root=new LinkedHashMap<>(source.headers);root.putAll(manifest);
        Map<String,String> media=new LinkedHashMap<>(source.headers);media.putAll(stream.isEmpty()?manifest:stream);
        headers=Collections.unmodifiableMap(root);streamHeaders=Collections.unmodifiableMap(media);
    }
    static InfinityCastSource parse(String raw,String manifest,String stream,boolean drm) {
        if(drm)return null;InfinityCastSource source=parse(raw);if(source==null)return null;
        InfinityCastSource root=parse("https://headers.invalid/media.mp4|"+(manifest==null?"":manifest));
        InfinityCastSource media=parse("https://headers.invalid/media.mp4|"+(stream==null?"":stream));
        return root==null || media==null?null:new InfinityCastSource(source,root.headers,media.headers);
    }
    static String mime(String contentType,String hint) {
        String type=contentType==null?"":contentType.split(";",2)[0].trim().toLowerCase(Locale.ROOT);
        if(type.equals("video/mp4") || type.equals("application/mp4") || type.equals("video/x-m4v"))return "video/mp4";
        if(type.equals("video/webm"))return "video/webm";
        if(type.equals("application/vnd.apple.mpegurl") || type.equals("application/x-mpegurl") ||
            type.equals("audio/mpegurl") || type.equals("audio/x-mpegurl"))return "application/vnd.apple.mpegurl";
        if(type.equals("application/dash+xml"))return type;
        if(type.equals("video/mp2t") || type.equals("video/mpeg"))return type;
        return (type.isEmpty() || type.equals("application/octet-stream"))?hint:null;
    }
    /** Bounded EBML header parse. Matroska and WebM share the same magic. */
    static String ebmlDocType(byte[] bytes) {
        if(bytes.length<5 || (bytes[0]&255)!=0x1a || (bytes[1]&255)!=0x45 || (bytes[2]&255)!=0xdf || (bytes[3]&255)!=0xa3)return "";
        int[] at={4};long size=ebmlVint(bytes,at,false,8);
        if(size<0 || size>4096 || size>bytes.length-at[0])return "";
        int end=at[0]+(int)size;
        while(at[0]<end) {
            long id=ebmlVint(bytes,at,true,4),length=ebmlVint(bytes,at,false,8);
            if(id<0 || length<0 || length>end-at[0])return "";
            if(id==0x4282) {
                if(length!=4 && length!=8)return "";
                return new String(bytes,at[0],(int)length,StandardCharsets.US_ASCII);
            }
            at[0]+=(int)length;
        }
        return "";
    }
    private static long ebmlVint(byte[] bytes,int[] at,boolean id,int max) {
        if(at[0]>=bytes.length)return -1;
        int first=bytes[at[0]]&255,width=1,mask=128;
        while(width<=max && (first&mask)==0){width++;mask>>=1;}
        if(width>max || at[0]+width>bytes.length)return -1;
        long value=id?first:first&(mask-1);at[0]++;
        for(int i=1;i<width;i++)value=(value<<8)|(bytes[at[0]++]&255);
        if(!id && value==((1L<<(7*width))-1))return -1;
        return value;
    }
    static String sniff(byte[] bytes,String contentType,String hint) {
        String type=mime(contentType,hint);
        String text=new String(bytes,0,Math.min(bytes.length,512),StandardCharsets.UTF_8).trim();
        if(text.startsWith("\ufeff"))text=text.substring(1).trim();
        if(text.startsWith("#EXTM3U"))return "application/vnd.apple.mpegurl";
        if(text.startsWith("<?xml") || text.startsWith("<MPD")) {
            if(text.contains("<MPD") || "application/dash+xml".equals(type))return "application/dash+xml";
        }
        // An HTML/error body must never be advertised as video by a URL hint.
        if(text.toLowerCase(Locale.ROOT).startsWith("<!doctype html") || text.toLowerCase(Locale.ROOT).startsWith("<html"))return null;
        if(bytes.length>=12 && bytes[4]=='f' && bytes[5]=='t' && bytes[6]=='y' && bytes[7]=='p')return "video/mp4";
        if(bytes.length>=4 && (bytes[0]&255)==0x1a && (bytes[1]&255)==0x45 && (bytes[2]&255)==0xdf && (bytes[3]&255)==0xa3)
            return "webm".equals(ebmlDocType(bytes))?"video/webm":null;
        if("video/webm".equals(type))return null;
        return type;
    }
    static String receiverTitle(String title) {
        if(title==null || title.isEmpty() || title.length()>256 || title.contains("://") || title.contains("|") ||
            title.contains("?") || title.contains("=") || title.toLowerCase(Locale.ROOT).matches(".*\\.(mp4|m4v|webm|m3u8|mpd).*"))return "Infinity video";
        for(int i=0;i<title.length();i++)if(title.charAt(i)<32 || title.charAt(i)==127)return "Infinity video";
        if(title.matches("[A-Za-z0-9_=-]{24,}"))return "Infinity video";
        return title;
    }
}
