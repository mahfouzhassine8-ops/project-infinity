"""Reuse the existing finite Linux fixture, with explicit source bindings."""
from pathlib import Path
import sys,json,hashlib,os,subprocess
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parent))
import render_media as M
original=M.F.setup
if os.environ.get('INFINITY_QA_OLD_LIST')=='1':
 old=Path('/tmp/infinity-a7-list-baseline.xml');old.write_bytes(subprocess.check_output(['git','show','a7f65029:'+str(M.F.SOURCE.relative_to(M.F.prepare.ROOT))],cwd=M.F.prepare.ROOT));M.F.SOURCE=old

def setup(*args,**kwargs):
 share,out=original(*args,**kwargs)
 c=json.loads((M.F.QA/'config.json').read_text());src=(HERE/('probe_negative.py' if os.environ.get('INFINITY_QA_NEGATIVE')=='1' else 'probe_season.py' if os.environ.get('INFINITY_QA_SEASON_ONLY')=='1' else 'probe.py')).read_text()
 c['media_sources']['probe.py']=hashlib.sha256(src.encode()).hexdigest()
 if os.environ.get('INFINITY_QA_NEGATIVE')=='1':
  fixture=(HERE/'fixture_negative.py').read_text();c['media_sources']['fixture_negative.py']=hashlib.sha256(fixture.encode()).hexdigest();M.F.replace(share/'addons/plugin.video.infinitybrowserqa/entry.py',fixture.replace('QA_PATH',repr(str(M.F.QA))).encode())
 M.F.replace(share/'addons/script.infinitybrowserqa/entry.py',src.replace('QA_PATH',repr(str(M.F.QA))).encode())
 (M.F.QA/'config.json').write_text(json.dumps(c));(out/'CONFIG.json').write_text(json.dumps(c,indent=2)+'\n')
 (out/'EXECUTED-PROBE.py').write_text(src)
 return share,out
M.F.setup=setup
if __name__=='__main__':raise SystemExit(M.F.main())
