#!/usr/bin/env python3
from __future__ import annotations
import argparse,hashlib,json,re,zipfile
from pathlib import Path

VERSION=2103221
NAME='1.0.9-Cobra-Options-UI-Owner-Guard-RC1'
CERT='d7adeb68e9341596a02bd3262b737a0f45fc6e771ed7e60285437e833b58c6d7'
NATIVE='db92b30f5523cacd9029aa21d7b52c8bc7819e4cd5c1dea76d4bfcdcf9205375'

def hb(b):return hashlib.sha256(b).hexdigest()
def req(v,m):
    if not v:raise RuntimeError(m)

def main():
    p=argparse.ArgumentParser()
    p.add_argument('--apk',type=Path,required=True)
    p.add_argument('--audit',type=Path,required=True)
    p.add_argument('--base',type=Path,required=True)
    p.add_argument('--source',type=Path,required=True)
    a=p.parse_args()

    report=json.loads(a.audit.read_text())
    req(report.get('version_code')==VERSION and report.get('version_name')==NAME,'candidate identity mismatch')
    req(report.get('signer_certificate_sha256')==CERT,'signer changed')
    req(report.get('apk_sha256')==hb(a.apk.read_bytes()),'APK receipt mismatch')

    splash=(a.source/'tools/android/packaging/xbmc/src/Splash.java.in').read_text()
    activity=(a.source/'tools/android/packaging/xbmc/src/InfinityLiveActivity.java.in').read_text()
    smart=(a.source/'tools/android/packaging/xbmc/src/CobraSmartReturn.java.in').read_bytes()

    start=splash.index('  private void showExperienceCardSettings(')
    next_method=splash.find('\n  private ',start+10)
    options=splash[start:next_method if next_method>start else len(splash)]
    req('android.app.AlertDialog.Builder' not in options,'stock Android AlertDialog remains in experience options')
    req('CobraVisualRenderer.DialogBuilder' not in options,'legacy AlertDialog renderer remains in experience options')
    for token in (
        'experience-options-cobra','experience-options-infinity',
        'experience-option-remember','experience-option-once','experience-option-ask',
        'experience-option-health','experience-option-recovery',
        'Remember & launch ','Launch ','Ask every time',
        'Infinity Health Center','Cobra Recovery'
    ):
        req(token in splash,'options UI source contract missing: '+token)
    req('Smart Return' not in options and 'cobra_smart_return' not in options,
        'Smart Return returned to chooser gear options')

    req(activity.count('cobraSelectActiveSection(destination);')==1,
        'active-section owner has non-drawer writers')
    req('2103221 drawer-owner guard' in activity,'central active-section guard missing')
    req('showCobraPrimaryView' in activity and 'cobraOpenLiveTv' in activity,'Live fallback methods missing')

    scope=json.loads(Path('audit221/scope.json').read_text())
    for key in (
        'infinity_options_custom_ui','cobra_options_custom_ui',
        'stock_alert_dialog_removed_from_experience_options',
        'smart_return_untouched','active_section_changes_only_from_drawer',
        'legacy_primary_live_fallback_guarded','cobra_open_live_guarded',
        'playback_unchanged','providers_unchanged','health_center_unchanged'
    ):
        req(scope.get(key) is True,'scope gate failed: '+key)
    req(hb(smart)==scope.get('smart_return_sha256'),'Smart Return source hash drift')

    with zipfile.ZipFile(a.apk) as z,zipfile.ZipFile(a.base) as b:
        req(hb(z.read('lib/arm64-v8a/libkodi.so'))==NATIVE,'native engine changed')
        for n in b.namelist():
            if n.startswith('lib/') and not n.endswith('/'):
                req(n in z.namelist() and z.read(n)==b.read(n),'native payload drift: '+n)
            if n.startswith(('assets/','res/')) or n=='resources.arsc':
                req(n in z.namelist() and z.read(n)==b.read(n),'protected resource drift: '+n)
        dex=b''.join(z.read(n) for n in z.namelist() if re.fullmatch(r'classes\d*\.dex',n))
        for token in (
            b'experience-options-cobra',b'experience-options-infinity',
            b'experience-option-remember',b'experience-option-recovery',
            b'cobra_active_section_owner',b'cobraRestoreVodLandingReturn',
            b'cobra_smart_return_experience_display',
            b'LIVE TV AMBIENT BLUE',b'Infinity Health Center'
        ):
            req(token in dex,'compiled contract missing: '+repr(token))

    result={
        'build':VERSION,'version_name':NAME,'apk_sha256':hb(a.apk.read_bytes()),
        'signer_certificate_sha256':CERT,'native_engine_sha256':NATIVE,
        'infinity_options_custom_ui':True,'cobra_options_custom_ui':True,
        'smart_return_untouched':True,'active_section_changes_only_from_drawer':True,
        'physical_device_verified':False,
        'status':'TEST CANDIDATE - options UI and Android lifecycle behavior require device acceptance'
    }
    Path('audit221/final.json').write_text(json.dumps(result,indent=2)+'\n')
    Path('signed221/ACCEPTANCE.json').write_text(json.dumps(result,indent=2)+'\n')
    print('PASS: 2103221 premium options UI + drawer-owned navigation verified')

if __name__=='__main__':main()
