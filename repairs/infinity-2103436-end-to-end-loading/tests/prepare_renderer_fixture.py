"""Prepare an isolated upstream Linux Kodi skin fixture, never a user profile."""
from pathlib import Path
from zipfile import ZipFile
import shutil
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from inventory import SKIN
from skin_coverage import legacy, transform

root=Path('/tmp/infinity-kodi-renderer/root')
skin=root/'usr/share/kodi/addons/skin.infinity.diggz'
for part in ('xml','media','fonts'): (skin/part).mkdir(parents=True,exist_ok=True)
(skin/'addon.xml').write_text('''<addon id="skin.infinity.diggz" version="1.0.0" name="Loading QA fixture" provider-name="Local QA"><requires><import addon="xbmc.gui" version="5.17.0"/></requires><extension point="xbmc.gui.skin"><res width="1280" height="720" aspect="16:9" default="true" folder="xml"/></extension></addon>''')
with ZipFile('/workspace/cobra-evidence/consolidated435/registered-review/prepared/components/INFINITY.zip') as z:
    for name in z.namelist():
        if name.startswith(SKIN+'media/') and name.endswith(('action_loading.gif','action_loading_still.png','frame.png')):
            dest=skin/name.removeprefix(SKIN);dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(z.read(name))
staged=Path('/workspace/infinity-loading436-stage-v3/members/assets/addons/skin.infinity.diggz/unified/Includes_InfinityActionLoading.xml')
shutil.copy2(staged,skin/'xml/Includes_InfinityActionLoading.xml')
shutil.copy2('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',skin/'fonts/QA.ttf')
(skin/'xml/Font.xml').write_text('<fonts><fontset id="Default" unicode="true"><font><name>font13</name><filename>QA.ttf</filename><size>24</size></font></fontset></fonts>')
(skin/'xml/Includes.xml').write_text('<includes><include file="Includes_InfinityActionLoading.xml"/><variable name="InfinityCollectiveFrameColor"><value>FF00FFFF</value></variable></includes>')
frame=legacy.frame_call(dict(left='120',top='200',width='400',height='120'),'45',window='0').decode()
global_frame=legacy.frame_call(dict(left='24',top='24',width='80',height='80'),'90',window='0',global_frame=True).decode()
worker=Path(__file__).with_name('renderer_work.py').resolve()
controls='''<controls><control type="button" id="45"><left>120</left><top>200</top><width>400</width><height>120</height><label>Native renderer fixture</label><font>font13</font><texturefocus>infinity_ui/frame.png</texturefocus><texturenofocus>infinity_ui/frame.png</texturenofocus><onclick>RunScript('''+str(worker)+''')</onclick></control>'''+frame+'''<control type="button" id="90"><left>24</left><top>24</top><width>80</width><height>80</height><label>Menu</label><font>font13</font><texturefocus>infinity_ui/frame.png</texturefocus><texturenofocus>infinity_ui/frame.png</texturenofocus></control>'''+global_frame+'</controls>'
prefix='<defaultcontrol always="true">45</defaultcontrol><onload>SetProperty(Infinity.Loading.FrameControls,|45|)</onload>'
script=Path(__file__).with_name('renderer_probe.py').resolve()
for name, text in [('Home.xml','<window>'+prefix+'<onload>RunScript('+str(script)+')</onload>'+controls+'</window>'),('Custom_1190_Renderer.xml','<window id="1190" type="window">'+prefix+controls+'</window>')]:
    revised,counts=transform(text.encode(),name)
    assert counts['actions']==1 and counts['frames']==0
    (skin/'xml'/name).write_bytes(revised)
# The fixture never loads Infinity's services, providers or protected lifecycle.
manifest=root/'usr/share/kodi/system/addon-manifest.xml'
text=manifest.read_text()
if '<addon>skin.infinity.diggz</addon>' not in text: manifest.write_text(text.replace('</addons>','<addon>skin.infinity.diggz</addon></addons>'))
# A non-service fixture registration makes the original enabled-addon guard
# evaluable. No signed Command Center module or authentication is replaced in
# an APK; this minimal renderer has never loaded the production add-on.
stub=root/'usr/share/kodi/addons/script.infinity.commandcenter'
stub.mkdir(exist_ok=True)
(stub/'addon.xml').write_text('<addon id="script.infinity.commandcenter" version="1.0.0" name="Loading observer QA guard" provider-name="Local QA"><requires><import addon="xbmc.python" version="3.0.0"/></requires><extension point="xbmc.python.script" library="default.py"/></addon>')
(stub/'default.py').write_text('raise RuntimeError("QA guard must never be used as an action handler")\n')
text=manifest.read_text()
if '<addon>script.infinity.commandcenter</addon>' not in text:manifest.write_text(text.replace('</addons>','<addon>script.infinity.commandcenter</addon></addons>'))
portable=root/'usr/share/kodi/portable_data/userdata'
portable.mkdir(parents=True,exist_ok=True)
(portable/'guisettings.xml').write_text('<settings version="2"><setting id="lookandfeel.skin">skin.infinity.diggz</setting><setting id="lookandfeel.startupwindow">10000</setting><setting id="services.webserver">false</setting><setting id="general.addonupdates">2</setting></settings>')
print('Prepared isolated minimal fixture; no full production skin or Android runtime claim')
