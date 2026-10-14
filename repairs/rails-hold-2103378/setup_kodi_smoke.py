"""Prepare a disposable GitHub runner Kodi profile, with no production user data."""
from pathlib import Path
import shutil
import xml.etree.ElementTree as ET

root=Path(__file__).resolve().parents[2]
profile=Path.home()/'.kodi/userdata';addons=profile.parent/'addons'
profile.mkdir(parents=True,exist_ok=True);addons.mkdir(exist_ok=True)
source=root/'features/infinity-rails-investigation-20261014/addons/script.infinity.rails'
shutil.copytree(source,addons/source.name,dirs_exist_ok=True)
fixture=addons/'plugin.video.infinityrailfixture';fixture.mkdir(exist_ok=True)
(fixture/'addon.xml').write_text('''<addon id="plugin.video.infinityrailfixture" name="Rail Fixture" version="1.0.0" provider-name="CI"><requires><import addon="xbmc.python" version="3.0.0"/></requires><extension point="xbmc.python.pluginsource" library="default.py"><provides>video</provides></extension><extension point="xbmc.addon.metadata"><summary lang="en_GB">Offline test fixture</summary><platform>all</platform></extension></addon>''')
(fixture/'default.py').write_text("import sys,xbmcplugin,xbmcvfs\nfrom pathlib import Path\nPath(xbmcvfs.translatePath('special://profile/rail-fixture-launched.txt')).write_text('launched')\nxbmcplugin.endOfDirectory(int(sys.argv[1]))\n")
skin=addons/'skin.infinity.diggz'
shutil.copytree('/usr/share/kodi/addons/skin.estuary',skin,dirs_exist_ok=True,symlinks=True)
# Ubuntu's Kodi 20.5 package contains a dangling Roboto-Thin font symlink.
# Repair only our disposable copied fixture, never the shipped Infinity skin.
for font in (skin/'fonts').glob('*.ttf'):
    if font.is_symlink() and not font.exists():
        font.unlink()
        shutil.copyfile('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',font)
manifest=ET.parse(skin/'addon.xml');manifest.getroot().set('id','skin.infinity.diggz');manifest.getroot().set('version','1.0.5.222');manifest.write(skin/'addon.xml')
res=manifest.find("extension[@point='xbmc.gui.skin']/res").get('folder')
(skin/res/'Home.xml').write_text('''<window><defaultcontrol always="true">9000</defaultcontrol><controls><control type="list" id="9000"><left>100</left><top>100</top><width>800</width><height>200</height><itemlayout height="80" width="800"><control type="label"><width>800</width><height>80</height><font>font20</font><label>$INFO[ListItem.Label]</label></control></itemlayout><focusedlayout height="80" width="800"><control type="label"><width>800</width><height>80</height><font>font20</font><label>$INFO[ListItem.Label]</label></control></focusedlayout><content><item><label>TV Rail Test</label><property name="section">tvshows</property><onclick>noop</onclick></item></content></control></controls></window>''')
keys=profile/'keymaps';keys.mkdir(exist_ok=True)
(keys/'rail-smoke.xml').write_text('<keymap><global><keyboard><f12>RunScript('+str(Path(__file__).with_name('kodi_smoke.py'))+')</f12></keyboard></global></keymap>')
(profile/'advancedsettings.xml').write_text('<advancedsettings><loglevel>1</loglevel></advancedsettings>')
