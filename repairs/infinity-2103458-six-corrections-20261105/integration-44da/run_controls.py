"""Reuse the existing disposable Linux runner, limited to newly changed controls."""
from pathlib import Path
import sys, json, hashlib, xml.etree.ElementTree as E
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parent))
import render_media as M
original=M.F.setup
def setup(*args,**kwargs):
    share,out=original(*args,**kwargs)
    c=json.loads((M.F.QA/'config.json').read_text())
    probe=(HERE/'probe.py').read_text()
    fixture=(HERE.parent/'continuation-a7/fixture_negative.py').read_text()
    fixture=fixture.replace("item.setInfo('video',info)","info['trailer']=str(BASE/'silent-test.mp4')\n item.setInfo('video',info)")
    c['media_sources']['integration_probe']=hashlib.sha256(probe.encode()).hexdigest()
    c['media_sources']['synthetic_fixture']=hashlib.sha256(fixture.encode()).hexdigest()
    M.F.replace(share/'addons/script.infinitybrowserqa/entry.py',probe.replace('QA_PATH',repr(str(M.F.QA))).encode())
    M.F.replace(share/'addons/plugin.video.infinitybrowserqa/entry.py',fixture.replace('QA_PATH',repr(str(M.F.QA))).encode())
    # Test-only bridge receiver: no external calls, Stop or playback. Production bridge untouched.
    dest=share/'addons/script.trailer.bridge'
    M.F.replace(dest/'addon.xml',b'<addon id="script.trailer.bridge" name="QA dispatch receiver" version="1.0.0" provider-name="QA"><requires><import addon="xbmc.python" version="3.0.0"/></requires><extension point="xbmc.python.script" library="entry.py"/></addon>')
    M.F.replace(dest/'entry.py',b"import xbmcgui\nh=xbmcgui.Window(10000)\nh.setProperty('Infinity.QA.TrailerCount',str(int(h.getProperty('Infinity.QA.TrailerCount') or '0')+1))\n")
    manifest=E.parse(share/'system/addon-manifest.xml').getroot()
    if not any(n.text=='script.trailer.bridge' for n in manifest): E.SubElement(manifest,'addon').text='script.trailer.bridge'
    M.F.replace(share/'system/addon-manifest.xml',E.tostring(manifest,encoding='utf-8',xml_declaration=True))
    c['fixture_only_trailer_receiver']=True
    (M.F.QA/'config.json').write_text(json.dumps(c))
    (out/'CONFIG.json').write_text(json.dumps(c,indent=2)+'\n')
    (out/'EXECUTED-PROBE.py').write_text(probe)
    return share,out
M.F.setup=setup
if __name__=='__main__':raise SystemExit(M.F.main())
