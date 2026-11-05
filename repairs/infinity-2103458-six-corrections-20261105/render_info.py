"""Selected Info-only upstream Linux observation; explicit geometry projection.
No Android, playback, application shutdown, phone data or package operation.
"""
import sys,json,hashlib,xml.etree.ElementTree as E
from pathlib import Path
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parent/'infinity-browser-visual-20261105'))
import render_fixture as F
original=F.setup

def setup(width,height,actions,attempt,slim=False):
    share,old=original(width,height,False,'info-'+attempt,False)
    out=HERE/'results'/('%dx%d-%s'%(width,height,attempt));out.mkdir(parents=True,exist_ok=False)
    config=json.loads((F.QA/'config.json').read_text());config['output']=str(out)
    src=share/'addons/skin.infinity.diggz/unified/DialogVideoInfo.xml'
    data=src.read_bytes();doc=E.fromstring(data);records=[]
    for control in doc.findall('./controls/control'):
        F.native_geometry(control,*config['logical'],records)
    config['info_sha256']=hashlib.sha256(data).hexdigest()
    F.replace(src,E.tostring(doc,encoding='utf-8',xml_declaration=True))
    (F.QA/'config.json').write_text(json.dumps(config))
    projection=json.loads((old/'PROJECTION.json').read_text())
    projection.update(info_source_sha256=config['info_sha256'],info_geometry=records)
    projection['fixture_only'].append('Info recursive percentage coordinates explicitly projected for upstream renderer')
    (out/'PROJECTION.json').write_text(json.dumps(projection,indent=2)+'\n')
    (old/'PROJECTION.json').unlink();old.rmdir()
    probe=(HERE/'info_probe.py').read_text().replace('QA_PATH',repr(str(F.QA)))
    F.replace(share/'addons/script.infinitybrowserqa/entry.py',probe.encode())
    return share,out
F.setup=setup
if __name__=='__main__':raise SystemExit(F.main())
