#!/usr/bin/env python3
import argparse,csv,hashlib,json,zipfile,xml.etree.ElementTree as ET
from pathlib import Path
PARENT='e0e70f6a0fc8ff9fbd8836f5979f90c64de4678fe0d468336fc59ce7cf4e9f0c'
ANCESTOR='dba26141addbacd64f334bcc32633669ffcc3c4677961e7ce3e23f01684416a0'
H=lambda b:hashlib.sha256(b).hexdigest()
p=argparse.ArgumentParser();p.add_argument('--parent',type=Path,required=True);p.add_argument('--ancestor',type=Path,required=True);p.add_argument('--candidate',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args()
assert H(a.parent.read_bytes())==PARENT;assert H(a.ancestor.read_bytes())==ANCESTOR
a.out.mkdir(parents=True,exist_ok=True);rows=[];native={};xml_count=0;xml_errors=[]
with zipfile.ZipFile(a.parent) as parent,zipfile.ZipFile(a.ancestor) as ancestor,zipfile.ZipFile(a.candidate) as candidate:
    assert all(z.testzip() is None for z in (parent,ancestor,candidate))
    assert set(parent.namelist())==set(ancestor.namelist())==set(candidate.namelist())
    for name in sorted(candidate.namelist()):
        b=parent.read(name);old=ancestor.read(name);c=candidate.read(name);same=b==c
        allowed=('AndroidManifest.xml','classes.dex','META-INF/INFINITY.RSA','META-INF/INFINITY.SF','META-INF/MANIFEST.MF')
        assert same or name in allowed,name
        assert old==c or name in allowed,name
        rows.append({'path':name,'parent_2103297_bytes':len(b),'candidate_2103298_bytes':len(c),'parent_2103297_sha256':H(b),
            'candidate_2103298_sha256':H(c),'ancestor_2103295_sha256':H(old),'status':'unchanged' if same else 'changed'})
        if name.startswith('lib/') and not name.endswith('/'):
            assert old==b==c;native[name]={'parent_2103297':H(b),'candidate_2103298':H(c),'ancestor_2103295':H(old),'identical':True}
        if name.startswith('assets/') and name.endswith('.xml'):
            try:ET.fromstring(c);xml_count+=1
            except ET.ParseError as e:xml_errors.append({'path':name,'error':str(e),'identical_to_both_parents':old==b==c})
changed=[r for r in rows if r['status']=='changed']
with (a.out/'APK-Payload-Byte-Manifest-2103298.csv').open('w') as f:
    w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
(a.out/'CHANGED-APK-FILES-2103298.json').write_text(json.dumps(changed,indent=2)+'\n')
report={'apk_sha256':H(a.candidate.read_bytes()),'direct_locked_parent_sha256':PARENT,'locked_ancestor_sha256':ANCESTOR,'version_code':2103298,
        'native_libraries_byte_identical_to_2103297_and_2103295':native,'unchanged_payloads':sum(r['status']=='unchanged' for r in rows),
        'changed_payloads':[r['path'] for r in changed],'unexpected_changes':0,
        'assets_byte_identical':sum(r['path'].startswith('assets/') and r['status']=='unchanged' for r in rows),
        'xml_assets_parsed':xml_count,'preexisting_xml_parse_findings':xml_errors,'xml_findings_introduced':0,
        'android_resources_byte_identical':True,'physical_device_verified':False,'locked':False}
(a.out/'PAYLOAD-AUDIT-2103298.json').write_text(json.dumps(report,indent=2,sort_keys=True)+'\n')
print(json.dumps({k:v for k,v in report.items() if k not in ('native_libraries_byte_identical_to_2103297_and_2103295','preexisting_xml_parse_findings')},indent=2))
