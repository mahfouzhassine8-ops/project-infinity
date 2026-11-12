package com.projectinfinity.kodi;

import java.util.logging.Logger;

/** Outcome codes only. Never accepts a URL, header, exception message or title. */
final class InfinityCastDiagnostics {
    private static final Logger log=Logger.getLogger("InfinityCast");
    static void event(String stage,String code,int result) {
        if(!stage.matches("[a-z_]{1,32}") || !code.matches("[a-z_]{1,48}"))return;
        log.info("InfinityCast stage="+stage+" outcome="+code+" result="+result);
    }
}
