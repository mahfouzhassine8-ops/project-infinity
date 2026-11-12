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
    private InfinityCastSource(URI uri,Map<String,String> headers,String hint) {
        this.uri=uri;this.headers=Collections.unmodifiableMap(headers);this.hint=hint;
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
            if(path.endsWith(".m3u8") || path.endsWith(".mpd"))return null;
            String hint=path.endsWith(".mp4") || path.endsWith(".m4v")?"video/mp4":path.endsWith(".webm")?"video/webm":null;
            Map<String,String> headers=new LinkedHashMap<>();
            if(parts.length==2 && !parts[1].isEmpty()) {
                if(parts[1].length()>16384)return null;
                for(String field:parts[1].split("&")) {
                    int equals=field.indexOf('=');if(equals<=0)return null;
                    String name=URLDecoder.decode(field.substring(0,equals),"UTF-8").toLowerCase(Locale.ROOT);
                    String value=URLDecoder.decode(field.substring(equals+1),"UTF-8");
                    if(!java.util.Arrays.asList("user-agent","referer","origin","cookie","authorization","accept","accept-language").contains(name) ||
                        value.length()>4096 || headers.containsKey(name))return null;
                    for(int i=0;i<value.length();i++)if(value.charAt(i)<32 || value.charAt(i)==127)return null;
                    headers.put(name,value);
                }
            }
            return new InfinityCastSource(uri,headers,hint);
        } catch(Exception invalid){return null;}
    }
    static String mime(String contentType,String hint) {
        String type=contentType==null?"":contentType.split(";",2)[0].trim().toLowerCase(Locale.ROOT);
        if(type.equals("video/mp4") || type.equals("application/mp4") || type.equals("video/x-m4v"))return "video/mp4";
        if(type.equals("video/webm"))return "video/webm";
        return (type.isEmpty() || type.equals("application/octet-stream"))?hint:null;
    }
    static String receiverTitle(String title) {
        if(title==null || title.isEmpty() || title.length()>256 || title.contains("://") || title.contains("|") ||
            title.contains("?") || title.contains("=") || title.toLowerCase(Locale.ROOT).matches(".*\\.(mp4|m4v|webm|m3u8|mpd).*"))return "Infinity video";
        for(int i=0;i<title.length();i++)if(title.charAt(i)<32 || title.charAt(i)==127)return "Infinity video";
        if(title.matches("[A-Za-z0-9_=-]{24,}"))return "Infinity video";
        return title;
    }
}
