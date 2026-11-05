"""Reuse finite Info fixture; no production source transform beyond projection."""
from pathlib import Path
import hashlib,json
import render_info as I
F=I.F
original=I.setup
HERE=Path(__file__).resolve().parent

def setup(width,height,actions,attempt,slim=False):
 share,out=original(width,height,actions,'media-'+attempt,slim)
 c=json.loads((F.QA/'config.json').read_text());c['media_sources']={
  'Info':c['info_sha256'],'List':c['source_sha256'],'genre_presentation':c['presentation_sha256'],
  'Variables':hashlib.sha256((share/'addons/skin.infinity.diggz/unified/Variables.xml').read_bytes()).hexdigest()}
 for aid,name in [('script.infinitybrowserqa','media_probe.py'),('plugin.video.infinitybrowserqa','media_fixture.py')]:
  src=(HERE/name).read_text();c['media_sources'][name]=hashlib.sha256(src.encode()).hexdigest()
  F.replace(share/'addons'/aid/'entry.py',src.replace('QA_PATH',repr(str(F.QA))).encode())
 (F.QA/'config.json').write_text(json.dumps(c));(out/'CONFIG.json').write_text(json.dumps(c,indent=2)+'\n')
 return share,out
F.setup=setup
if __name__=='__main__':raise SystemExit(F.main())
