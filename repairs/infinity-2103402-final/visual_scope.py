"""Exact-baseline owned visual corrections; never updates the locked input."""
from pathlib import Path
from zipfile import ZipFile
import hashlib,json,re
import xml.etree.ElementTree as ET
from osd_playpause_scope import patch_one, MEMBERS, OLD, NEW
ROOT=Path(__file__).parent
LEDGER=json.loads((ROOT/'FILE-AUTHORIZATION-LEDGER.json').read_text())
PINS={row['path']:row['baseline_sha256'] for row in LEDGER['files']
      if row['path'] in MEMBERS or row['path']=='script.infinity.commandcenter/resources/skins/Default/1080i/InfinityInformation.xml'}
INK=b'<textcolor>FFFFFFFF</textcolor><shadowcolor>FF000000</shadowcolor>'
ORIGINAL_INK=b'<textcolor>$VAR[InfinityGlassTextPrimary]</textcolor>'
LABEL=re.compile(rb'<control type="label">.*?</control>',re.S)

def transform(name,data):
    if name not in PINS or hashlib.sha256(data).hexdigest()!=PINS[name]:
        raise ValueError('Unauthorized or changed baseline: '+name)
    if name in MEMBERS:
        result=patch_one(data);count=0
        def contrast(match):
            nonlocal count
            block=match.group()
            if b'<label>$INFO[Player.Time(hh:mm:ss)]</label>' not in block and b'<label>$INFO[Player.Duration(hh:mm:ss)]</label>' not in block:return block
            if block.count(ORIGINAL_INK)!=1 or b'<shadowcolor>' in block:raise ValueError('Time label source changed')
            count+=1
            return block.replace(ORIGINAL_INK,INK,1)
        result=LABEL.sub(contrast,result) if '/unified/' in name else result
        if '/unified/' in name and count!=2:raise ValueError('Exactly two player time labels required')
        reverse=result.replace(INK,ORIGINAL_INK).replace(NEW[0],OLD[0]).replace(NEW[1],OLD[1])
    else:
        if data.count(b'<showonepage>true</showonepage>')!=2:raise ValueError('Information track source changed')
        result=data.replace(b'<showonepage>true</showonepage>',b'<showonepage>false</showonepage>')
        reverse=result.replace(b'<showonepage>false</showonepage>',b'<showonepage>true</showonepage>')
    if reverse!=data:raise ValueError('Unrelated change')
    ET.fromstring(result)
    return result

def expected(baseline):
    with ZipFile(baseline) as z:
        return {name:transform(name,z.read('assets/addons/'+name)) for name in PINS}

def stage(baseline,directory):
    # Preflight the entire authorized set before writing any candidate file.
    revised=expected(baseline)
    for name,data in revised.items():
        target=Path(directory)/name;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(data)
    return {n:hashlib.sha256(b).hexdigest() for n,b in revised.items()}

def audit_package(baseline,candidate,apk=True):
    """Permanent final ZIP/APK regression gate, including all14 OSD variants."""
    revised=expected(baseline);prefix='assets/addons/' if apk else ''
    with ZipFile(candidate) as z:
        if len(z.namelist())!=len(set(z.namelist())):raise ValueError('Duplicate archive entries')
        actual={n.removeprefix(prefix) for n in z.namelist() if n.startswith(prefix+'skin.infinity.diggz/') and n.endswith('/VideoOSD.xml')}
        if actual!=set(MEMBERS):raise ValueError('OSD variant inventory mismatch')
        for n,b in revised.items():
            if not apk and not n.startswith('skin.infinity.diggz/'):continue
            if z.read(prefix+n)!=b:raise ValueError('Packaged visual regression: '+n)
    return True
