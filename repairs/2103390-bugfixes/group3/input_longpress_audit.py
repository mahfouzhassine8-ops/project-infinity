#!/usr/bin/env python3
"""Read-only Group #3 signed-APK input / touch compatibility inventory.

NO changes to Kodi keymaps, native .so, Cobra, Home, plugin providers or data.
The existing rails-specific native handler is not a verified generic hook.
"""
from __future__ import annotations
from pathlib import Path
import hashlib
import zipfile
import xml.etree.ElementTree as ET

APK_SHA256='778b84a5f0d8712f250c538bacfa3c01e1352a936e0b7b9aa79cbaada9b22dbb'
HOME_PREFIX='assets/addons/skin.infinity.diggz/'


def analyze(apk: Path) -> dict:
    raw=Path(apk).read_bytes()
    if hashlib.sha256(raw).hexdigest()!=APK_SHA256:
        raise ValueError('Unexpected original signed APK')
    with zipfile.ZipFile(apk) as z:
        n=z.namelist()
        touch=ET.fromstring(z.read('assets/system/keymaps/touchscreen.xml'))
        mouse=ET.fromstring(z.read('assets/system/keymaps/mouse.xml'))
        touch_long=touch.findtext('./global/touch/longpress')
        mouse_long=mouse.findtext('./global/mouse/longclick')
        home_touch=touch.find('./Home/touch')
        homes=[x for x in n if x.startswith(HOME_PREFIX) and x.endswith('/Home.xml')]
        if len(homes)!=14:raise ValueError('Original Infinity Home layout count differs')
        count=0
        for name in homes:
            root=ET.fromstring(z.read(name))
            for panel,section,owner in ((8101,'movies','plugin.video.umbrella'),
                                        (8102,'tvshows','plugin.video.umbrella')):
                p=root.find(f".//control[@id='{panel}']")
                if p is None or p.get('type')!='panel' or p.findtext('orientation')!='horizontal':
                    raise ValueError('Unexpected Home release panel: '+name)
                if owner not in (p.findtext('content') or ''):
                    raise ValueError('Original release provider changed: '+name)
                if p.find('onclick') is not None:
                    raise ValueError('Original short-tap overridden: '+name)
                count+=1
        return {
            'original_apk_sha256':APK_SHA256,
            'top_movie_tv_panels_verified':count,
            'touch_global_longpress':touch_long,
            'mouse_global_longclick':mouse_long,
            'home_specific_touch_mapping_present':home_touch is not None,
            'direct_home_option_b_longpress_connected':False,
            'native_rail_hold_reuse':'NOT_PROVEN_FOR_PANELS_8101_8102',
            'scope_warning':('Native rail hold source guards 9200,8820,8720,19601; direct '
                'Option B needs per-gesture hit item and original click suppression. '
                'Do not globally remap Home touch or modify shared native code.'),
            'original_members_unmodified':len(n)
        }

if __name__=='__main__':
    import argparse,json
    a=argparse.ArgumentParser();a.add_argument('original_apk',type=Path)
    args=a.parse_args();print(json.dumps(analyze(args.original_apk),indent=2))
