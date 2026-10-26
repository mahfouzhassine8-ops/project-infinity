"""Exact bundled service: keep desktop distribution probing out of Infinity Android."""
import hashlib

MEMBER='assets/addons/service.xbmc.versioncheck/resources/lib/version_check/service.py'
BEFORE_SHA='166a1f5974fd2f7c297f801dd36040b4e7d6ccf6655e2edfa335803f3bbc58d5'
BEFORE=b"if sys.platform.startswith('linux'):\r\n"
AFTER=(b"# Android Infinity uses the existing non-APT version check. Desktop\r\n"
       b"# distribution probing here runs before the service reads its settings.\r\n"
       b"if (xbmc.getSkinDir() == 'skin.infinity.diggz' and\r\n"
       b"        xbmc.getCondVisibility('System.Platform.Android')):\r\n"
       b"    DISTRIBUTION = 'android'\r\n"
       b"elif sys.platform.startswith('linux'):\r\n")


def patch(raw):
    if hashlib.sha256(raw).hexdigest()!=BEFORE_SHA or raw.count(BEFORE)!=1:
        raise ValueError('Exact signed VersionCheck source required')
    changed=raw.replace(BEFORE,AFTER,1)
    if changed.replace(AFTER,BEFORE,1)!=raw:raise ValueError('Unowned VersionCheck edit')
    compile(changed,'version_check/service.py','exec')
    return changed
