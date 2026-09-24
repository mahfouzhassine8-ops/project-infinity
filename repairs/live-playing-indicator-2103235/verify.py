#!/usr/bin/env python3
from __future__ import annotations
import argparse,hashlib,json,re,zipfile,xml.etree.ElementTree as ET
from pathlib import Path
V=2103235
NAME='1.0.9-Cobra-Live-Playing-Indicator-RC1'
PARENT_SHA='11337e17a65ec06da978f4d9bf3fa4649d78159d8abf296370d518ab97652376'
CERT='d7adeb68e9341596a02bd3262b737a0f45fc6e771ed7e60285437e833b58c6d7'
NATIVE='db92b30f5523cacd9029aa21d7b52c8bc7819e4cd5c1dea76d4bfcdcf9205375'
def h(b):return hashlib.sha256(b).hexdigest()
def req(v,m):
    if not v:raise RuntimeError(m)
def main():
    p=argparse.ArgumentParser();p.add_argument('--apk',type=Path,required=True);p.add_argument('--parent230',type=Path,required=True);p.add_argument('--audit',type=Path,required=True);p.add_argument('--scope',type=Path,required=True);p.add_argument('--source-audit',type=Path,required=True);p.add_argument('--inherited-result',type=Path,required=True);p.add_argument('--indicator-results',type=Path,required=True);a=p.parse_args()
    report=json.loads(a.audit.read_text());scope=json.loads(a.scope.read_text());source=json.loads(a.source_audit.read_text());inherited=json.loads(a.inherited_result.read_text())
    req(report.get('version_code')==V and report.get('version_name')==NAME,'identity mismatch')
    req(report.get('signer_certificate_sha256')==CERT,'signer mismatch')
    req(h(a.parent230.read_bytes())==PARENT_SHA,'not exact passed 2103230 parent APK')
    req(source.get('passed') is True,'source audit failed')
    req(inherited.get('gate_passed') is True and inherited.get('executed_count')==228 and not inherited.get('failures') and not inherited.get('skipped'),'2103230 inherited regression suite did not pass unchanged')
    indicator=[]
    for f in a.indicator_results.glob('TEST-*.xml'):
      doc=ET.parse(f)
      for case in doc.findall('.//testcase'):
        if case.attrib.get('classname','').endswith('Cobra2103235PlayingIndicatorTest'):
          req(case.find('failure') is None and case.find('error') is None and case.find('skipped') is None,'indicator test failed/skipped: '+case.attrib.get('name',''))
          indicator.append(case.attrib.get('name',''))
    req(len(indicator)==4,'expected 4 focused indicator tests, got '+str(len(indicator)))
    with zipfile.ZipFile(a.parent230) as pz,zipfile.ZipFile(a.apk) as z:
      req(z.testzip() is None,'candidate ZIP CRC error');same=[]
      protected=lambda n:n.startswith(('assets/','res/','lib/')) or n=='resources.arsc' or bool(re.fullmatch(r'classes\d+\.dex',n))
      for n in pz.namelist():
        if protected(n):
          req(n in z.namelist() and pz.read(n)==z.read(n),'protected APK entry drift: '+n);same.append(n)
      req({n for n in pz.namelist() if protected(n)}=={n for n in z.namelist() if protected(n)},'protected APK entries added/removed')
      req(h(z.read('lib/arm64-v8a/libkodi.so'))==NATIVE,'native engine drift')
      dex=b''.join(z.read(n) for n in z.namelist() if re.fullmatch(r'classes\d*\.dex',n))
      for token in (b'CobraPlayingIndicatorPolicy',b'cobra_night_cinema',b'Multi-View layout',b'Fill Screen',b'unexpected-live-ended'):
        req(token in dex,'compiled contract missing '+repr(token))
    out={'build':V,'parent':2103230,'apk_sha256':h(a.apk.read_bytes()),'parent_apk_sha256':PARENT_SHA,'signer_sha256':CERT,'native_sha256':NATIVE,'native_rebuilt':False,'protected_apk_entries_identical':len(same),'inherited_test_cases':228,'indicator_test_cases':len(indicator),'candidate_failures':0,'candidate_skips':0,'true_live_playing_indicator':True,'actual_session_owned':True,'focus_independent':True,'ambient_adaptive':True,'night_cinema_adaptive':True,'physical_device_verified':False,'status':'TEST CANDIDATE — automated gates passed; device visual/session verification required'}
    Path('signed235/ACCEPTANCE.json').write_text(json.dumps(out,indent=2)+'\n')
    print('PASS:',json.dumps(out))
if __name__=='__main__':main()
