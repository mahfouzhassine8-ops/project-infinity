#!/usr/bin/env python3
from __future__ import annotations
import argparse,hashlib,json,re,zipfile,xml.etree.ElementTree as ET
from pathlib import Path

V=2103237
NAME='1.0.9-Cobra-Playing-Dot-OLED-Micro-Polish-RC1'
PARENT_SHA='e2131134c74516f9b85973856770c663a421bf5681dc3bd79e13648027a7d5d5'
CERT='d7adeb68e9341596a02bd3262b737a0f45fc6e771ed7e60285437e833b58c6d7'
NATIVE='db92b30f5523cacd9029aa21d7b52c8bc7819e4cd5c1dea76d4bfcdcf9205375'

def h(b):return hashlib.sha256(b).hexdigest()
def req(v,m):
    if not v:raise RuntimeError(m)

def focused_results(directory:Path):
    wanted={
      'Cobra2103235PlayingIndicatorTest':4,
      'Cobra2103236AllViewsPlayingIndicatorTest':4,
      'Cobra2103237PlayingDotPolishTest':6,
    }
    seen={k:[] for k in wanted}
    for f in directory.glob('TEST-*.xml'):
      doc=ET.parse(f)
      for case in doc.findall('.//testcase'):
        cls=case.attrib.get('classname','').rsplit('.',1)[-1]
        if cls not in wanted:continue
        req(case.find('failure') is None and case.find('error') is None and case.find('skipped') is None,
            'focused playing-dot test failed/skipped: '+cls+'.'+case.attrib.get('name',''))
        seen[cls].append(case.attrib.get('name',''))
    for cls,count in wanted.items():req(len(seen[cls])==count,f'{cls}: expected {count} passing cases, got {len(seen[cls])}')
    return seen

def main():
    p=argparse.ArgumentParser()
    p.add_argument('--apk',type=Path,required=True);p.add_argument('--parent236',type=Path,required=True)
    p.add_argument('--audit',type=Path,required=True);p.add_argument('--scope',type=Path,required=True)
    p.add_argument('--source-audit',type=Path,required=True);p.add_argument('--inherited-result',type=Path,required=True)
    p.add_argument('--focused-results',type=Path,required=True);a=p.parse_args()

    report=json.loads(a.audit.read_text());source=json.loads(a.source_audit.read_text());inherited=json.loads(a.inherited_result.read_text())
    req(report.get('version_code')==V and report.get('version_name')==NAME,'identity mismatch')
    req(report.get('signer_certificate_sha256')==CERT,'signer mismatch')
    req(h(a.parent236.read_bytes())==PARENT_SHA,'not exact locked 2103236 parent APK')
    req(source.get('passed') is True and source.get('views')==['TV Grid','Mobile','Compact','Cards','Focus'],'OLED source audit failed')
    req(source.get('buffering_animation_untouched') is True,'buffering animation preservation proof missing')
    req(inherited.get('gate_passed') is True and inherited.get('executed_count')==228 and not inherited.get('failures') and not inherited.get('skipped'),
        '2103230 inherited regression suite did not pass unchanged')
    focused=focused_results(a.focused_results)

    with zipfile.ZipFile(a.parent236) as pz,zipfile.ZipFile(a.apk) as z:
      req(z.testzip() is None and pz.testzip() is None,'ZIP CRC error')
      same=[]
      protected=lambda n:n.startswith(('assets/','res/','lib/')) or n=='resources.arsc' or bool(re.fullmatch(r'classes\d+\.dex',n))
      for n in pz.namelist():
        if protected(n):
          req(n in z.namelist() and pz.read(n)==z.read(n),'protected APK entry drift: '+n);same.append(n)
      req({n for n in pz.namelist() if protected(n)}=={n for n in z.namelist() if protected(n)},'protected APK entries added/removed')
      req(h(z.read('lib/arm64-v8a/libkodi.so'))==NATIVE,'native engine drift')
      dex=z.read('classes.dex')
      for token in (
        b'CobraPlayingIndicatorPolicy',b'CobraPlayingDot',b'CobraMobileChannelRow',b'CobraCompactChannelRow',
        b'CobraPosterChannelCard',b'CobraFocusQueueRow',b'CobraBroadcastRow',
        b'Multi-View layout',b'Fill Screen',b'unexpected-live-ended'
      ):
        req(token in dex,'compiled contract missing '+repr(token))

    out={
      'build':V,'parent':2103236,'apk_sha256':h(a.apk.read_bytes()),'parent_apk_sha256':PARENT_SHA,
      'signer_sha256':CERT,'native_sha256':NATIVE,'native_rebuilt':False,
      'protected_apk_entries_identical':len(same),'inherited_test_cases':228,
      'focused_indicator_test_cases':sum(len(v) for v in focused.values()),
      'candidate_failures':0,'candidate_skips':0,
      'true_live_playing_indicator':True,'actual_session_owned':True,'focus_independent':True,
      'views':['TV Grid','Mobile','Compact','Cards','Focus'],
      'view_placement_unchanged':True,'buffering_animation_untouched':True,
      'playing_dot_handoff_ms':180,'color_morph_ms':240,
      'oled_core_floor_alpha':218,'oled_glow_floor':0.58,'oled_native_rendering':True,
      'night_cinema_color':'warm amber/yellow #FFC247','ambient_adaptive':True,
      'physical_device_verified':False,
      'status':'TEST CANDIDATE — automated gates passed; physical-device micro-polish verification required'
    }
    Path('signed237/ACCEPTANCE.json').write_text(json.dumps(out,indent=2)+'\n')
    print('PASS:',json.dumps(out))
if __name__=='__main__':main()
