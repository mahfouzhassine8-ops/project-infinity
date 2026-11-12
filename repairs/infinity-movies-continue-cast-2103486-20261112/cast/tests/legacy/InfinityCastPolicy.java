package com.projectinfinity.kodi;

import java.net.URI;
import java.net.URISyntaxException;
import java.util.Locale;

/** No credential/header/token forwarding, media proxy, DRM or provider rewrite. */
final class InfinityCastPolicy {
    private InfinityCastPolicy() {}
    static String mime(String raw) {
        if (raw == null || raw.isEmpty() || raw.length() > 65536 || raw.indexOf('|') >= 0)
            return null;
        for (int i=0;i<raw.length();i++) if (raw.charAt(i)<32 || raw.charAt(i)==127) return null;
        try {
            URI uri = new URI(raw);
            String scheme = uri.getScheme();
            if (!("https".equalsIgnoreCase(scheme) || "http".equalsIgnoreCase(scheme)) ||
                uri.getHost()==null || uri.getHost().isEmpty() || uri.getRawUserInfo()!=null ||
                uri.getRawQuery()!=null || uri.getRawFragment()!=null) return null;
            String host=uri.getHost().toLowerCase(Locale.ROOT).replace("[","").replace("]","");
            if(host.equals("localhost") || host.endsWith(".localhost") || host.startsWith("127.") ||
                host.equals("0.0.0.0") || host.equals("::") || host.equals("::1") ||
                host.equals("0:0:0:0:0:0:0:1") || host.matches("[0-9]+"))return null;
            String path = uri.getPath();
            if (path==null) return null;
            String lower=path.toLowerCase(Locale.ROOT);
            if (lower.matches(".*(/|%2f)(auth|token|session|signature|license|credential|password|key)(/|=|%2f).*")) return null;
            // Unknown opaque credential-like path components are not handed to
            // a receiver. Query/signed URLs and Kodi protocol headers are also
            // unsupported, even if the phone can play them.
            for (String part:path.split("/"))
                if (part.matches("[A-Za-z0-9_=-]{40,}(\\.[A-Za-z0-9_=-]+)*")) return null;
            if (lower.endsWith(".mp4") || lower.endsWith(".m4v")) return "video/mp4";
            if (lower.endsWith(".webm")) return "video/webm";
            if (lower.endsWith(".m3u8")) return "application/x-mpegURL";
            if (lower.endsWith(".mpd")) return "application/dash+xml";
            return null;
        } catch (URISyntaxException | IllegalArgumentException error) { return null; }
    }
}
