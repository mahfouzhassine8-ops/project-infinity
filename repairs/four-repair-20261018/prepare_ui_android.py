"""Stage verified full production dependencies plus explicit disposable fixtures."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import sys
import xml.etree.ElementTree as ET
import zipfile

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / 'full-system-20261017'))
import infinity_full_stack_assets as full

def prepare(a):
    full.prepare(a.skin, a.rails, a.first_party, a.additional, a.out, include_helpers=True)
    stage = a.out / 'addons'
    from test_skin import check
    check(a.skin, a.candidate)
    # Only disposable staging is replaced; original input/installed profiles stay intact.
    shutil.rmtree(stage / 'skin.infinity.diggz')
    for archive, ident in ((a.candidate, 'skin.infinity.diggz'), (a.helper, 'script.infinity.uirepair')):
        with zipfile.ZipFile(archive) as z:
            assert z.testzip() is None
            for name in z.namelist():
                assert name.startswith(ident + '/') and '..' not in Path(name).parts
            z.extractall(stage)
    helper = stage / 'script.infinity.uitest'; helper.mkdir()
    (helper / 'addon.xml').write_text('<addon id="script.infinity.uitest" name="Infinity UI test observer" version="1.0.0" provider-name="Infinity CI"><requires><import addon="xbmc.python" version="3.0.0"/></requires><extension point="xbmc.python.script" library="default.py"/><extension point="xbmc.addon.metadata"><summary lang="en_GB">Disposable emulator observer</summary><description lang="en_GB">Not distributed to devices</description><platform>all</platform><license>GPL-2.0-or-later</license></extension></addon>')
    shutil.copyfile(HERE / 'ui_fixture.py', helper / 'default.py')
    for i in range(12):
        aid = 'plugin.video.infinityuitest' + str(i)
        folder = stage / aid; folder.mkdir()
        (folder / 'addon.xml').write_text('<addon id="' + aid + '" name="Infinity UI Fixture ' + str(i).zfill(2) + '" version="1.0.0" provider-name="Infinity CI"><requires><import addon="xbmc.python" version="3.0.0"/></requires><extension point="xbmc.python.pluginsource" library="plugin.py"><provides>video</provides></extension><extension point="xbmc.addon.metadata"><summary lang="en_GB">Harmless UI fixture</summary><description lang="en_GB">Disposable native integration test only</description><platform>all</platform><license>GPL-2.0-or-later</license></extension></addon>')
        if i % 2 == 0:
            resources = folder / 'resources'; resources.mkdir()
            (resources / 'settings.xml').write_text('<settings><category label="Fixture"><setting id="fixture" type="bool" label="Harmless fixture option" default="false"/></category></settings>')
        (folder / 'plugin.py').write_text('''import sys
from urllib.parse import parse_qs
import xbmcgui, xbmcplugin
params=parse_qs(sys.argv[2].lstrip('?')); handle=int(sys.argv[1])
if 'play' in params:
    item=xbmcgui.ListItem(path='special://profile/infinity-ui-fixture.mp4')
    xbmcplugin.setResolvedUrl(handle,True,item)
else:
    item=xbmcgui.ListItem(label='Infinity UI public movie',path=sys.argv[0]+'?play=movie')
    item.setInfo('video',{'title':'Infinity UI public movie','mediatype':'movie'})
    item.setProperty('IsPlayable','true')
    xbmcplugin.addDirectoryItem(handle,sys.argv[0]+'?play=movie',item,isFolder=False)
    xbmcplugin.endOfDirectory(handle,cacheToDisc=False)
''')
    proof_path = a.out / 'FULL-STACK-INPUTS.json'
    proof = json.loads(proof_path.read_text())
    proof['ui_candidate'] = dict(skin_version='1.0.5.227',
        skin_sha256=hashlib.sha256(a.candidate.read_bytes()).hexdigest(),
        helper_sha256=hashlib.sha256(a.helper.read_bytes()).hexdigest(),
        source_files={p.relative_to(stage).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
                      for p in stage.rglob('*') if p.is_file()})
    proof_path.write_text(json.dumps(proof, indent=2))

if __name__ == '__main__':
    p=argparse.ArgumentParser()
    for name in ('skin','rails','first-party','additional','candidate','helper','out'):
        p.add_argument('--'+name, type=Path, required=True)
    prepare(p.parse_args())
