package com.projectinfinity.kodi;

import java.util.ArrayDeque;
import java.util.logging.Logger;

/** Bounded RAM-only outcome codes. No URL, header, title or exception text. */
final class InfinityCastDiagnostics {
    private static final Logger log=Logger.getLogger("InfinityCast");
    private static final ArrayDeque<String> events=new ArrayDeque<>();
    static synchronized void begin(){events.clear();}
    static void event(String stage,String code,int result) {
        if(!stage.matches("[a-z_]{1,32}") || !code.matches("[a-z][a-z0-9_]{0,63}"))return;
        String line="stage="+stage+" outcome="+code+" result="+result;
        synchronized(InfinityCastDiagnostics.class){while(events.size()>=80)events.removeFirst();events.addLast(line);}
        log.info("InfinityCast "+line);
    }
    static synchronized String summary(){StringBuilder text=new StringBuilder();for(String line:events){if(text.length()>0)text.append('\n');text.append(line);}return text.toString();}
}
