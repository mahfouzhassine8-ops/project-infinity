#!/usr/bin/env python3
import argparse, csv, hashlib, json, zipfile, xml.etree.ElementTree as ET
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('--parent',type=Path,required=True);p.add_argument('--candidate',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args()
H=lambda b:hashlib.sha256(b).hexdigest()
assert H(a.parent.read_bytes())=='dba26141addbacd64f334bcc32633669ffcc3c4677961e7ce3e23f01684416a0'
a.out.mkdir(parents=True,exist_ok=True)
rows=[];native={};xml_count=0;xml_errors=[]
with zipfile.ZipFile(a.parent) as before,zipfile.ZipFile(a.candidate) as after:
    assert before.testzip() is None and after.testzip() is None
    assert set(before.namelist())==set(after.namelist()),'Entry added/removed'
    for name in sorted(before.namelist()):
        b=before.read(name);c=after.read(name);same=b==c
        assert same or name in ('AndroidManifest.xml','classes.dex','META-INF/INFINITY.RSA','META-INF/INFINITY.SF','META-INF/MANIFEST.MF'),name
        rows.append({'path':name,'before_bytes':len(b),'after_bytes':len(c),'before_sha256':H(b),'after_sha256':H(c),'status':'unchanged' if same else 'changed'})
        if name.startswith('lib/') and not name.endswith('/'):
            assert same;native[name]=H(c)
        if name.startswith('assets/') and name.endswith('.xml'):
            # Existing upstream XML may not be strict XML. Record those unchanged pre-existing defects.
            try:ET.fromstring(c);xml_count+=1
            except ET.ParseError as e:xml_errors.append({'path':name,'error':str(e),'byte_identical_to_parent':same})
changed=[r for r in rows if r['status']=='changed']
with (a.out/'APK-Payload-Byte-Manifest-2103297.csv').open('w') as f:
    w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
(a.out/'CHANGED-APK-FILES.json').write_text(json.dumps(changed,indent=2)+'\n')
report={'apk_sha256':H(a.candidate.read_bytes()),'parent_sha256':H(a.parent.read_bytes()),'version_code':2103297,
        'native_libraries_byte_identical':native,'unchanged_payloads':sum(r['status']=='unchanged' for r in rows),
        'changed_payloads':[r['path'] for r in changed],'unexpected_changes':0,
        'asset_payloads_byte_identical':sum(r['path'].startswith('assets/') and r['status']=='unchanged' for r in rows),
        'xml_assets_parsed':xml_count,'preexisting_xml_parse_findings':xml_errors,
        'xml_asset_findings_introduced':0,'android_resources_byte_identical':True,'physical_device_verified':False,'locked':False}
(a.out/'PAYLOAD-AUDIT-2103297.json').write_text(json.dumps(report,indent=2,sort_keys=True)+'\n')
print(json.dumps({k:v for k,v in report.items() if k not in ('native_libraries_byte_identical','preexisting_xml_parse_findings')},indent=2))
