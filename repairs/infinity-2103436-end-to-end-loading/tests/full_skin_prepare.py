"""Full signed skin rendering on upstream Linux, isolated from protected services.

All production XML/media/fonts are exact baseline plus the reviewed staging.
Only QA add-on registrations and an independent QA service are installed; this
does not execute or disable authentication in the signed Android application.
"""
from pathlib import Path
from zipfile import ZipFile
import shutil
import json
import xml.etree.ElementTree as ET

R=Path('/tmp/infinity-kodi-renderer')
addons=R/'root/usr/share/kodi/addons'
skin=addons/'skin.infinity.diggz'
if not (R/'minimal-skin').exists():skin.rename(R/'minimal-skin')
stage=Path('/tmp/infinity-loading437-final/members/assets/addons/skin.infinity.diggz')
with ZipFile('/workspace/cobra-evidence/consolidated435/registered-review/prepared/components/INFINITY.zip') as z:
    prefix='payload/assets/addons/skin.infinity.diggz/'
    for n in z.namelist():
        if not n.startswith(prefix):continue
        rel=n.removeprefix(prefix)
        # No production Python service or helper is executed by a skin fixture.
        if rel.endswith(('.py','.pyc','.pyo')):continue
        p=skin/rel;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(z.read(n))
for p in stage.rglob('*'):
    if p.is_file():
        target=skin/p.relative_to(stage);target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,target)
manifest=R/'root/usr/share/kodi/system/addon-manifest.xml';root=ET.fromstring(manifest.read_bytes())
registered={n.text for n in root}
requirements=ET.fromstring((skin/'addon.xml').read_bytes()).findall('./requires/import')
for dep in requirements:
    name=dep.get('addon')
    if name.startswith('xbmc.'):continue
    target=addons/name;target.mkdir(exist_ok=True)
    point='xbmc.python.script' if name.startswith('script.') else 'kodi.resource.images'
    (target/'addon.xml').write_text('<addon id="'+name+'" version="'+dep.get('version')+'" name="QA registration only" provider-name="Local QA"><extension point="'+point+'" library="noop.py"/></addon>')
    (target/'noop.py').write_text('# QA registration only; no production provider or protected service\n')
    if name not in registered:ET.SubElement(root,'addon').text=name
qa=addons/'script.loading.fullskinqa';qa.mkdir(exist_ok=True)
(qa/'addon.xml').write_text('<addon id="script.loading.fullskinqa" version="1.0.0" name="Full skin QA" provider-name="Local QA"><requires><import addon="xbmc.python" version="3.0.0"/></requires><extension point="xbmc.service" library="probe.py" start="startup"/></addon>')
shutil.copy2(Path(__file__).with_name('full_skin_probe.py'),qa/'probe.py')
if 'script.loading.fullskinqa' not in registered:ET.SubElement(root,'addon').text='script.loading.fullskinqa'
manifest.write_bytes(ET.tostring(root))
plugin=addons/'plugin.video.loadingqa';plugin.mkdir(exist_ok=True)
(plugin/'addon.xml').write_text('<addon id="plugin.video.loadingqa" version="1.0.0" name="Native directory QA" provider-name="Local QA"><requires><import addon="xbmc.python" version="3.0.0"/></requires><extension point="xbmc.python.pluginsource" library="default.py"><provides>video</provides></extension></addon>')
shutil.copy2(Path(__file__).with_name('full_skin_directory.py'),plugin/'default.py')
if 'plugin.video.loadingqa' not in registered:ET.SubElement(root,'addon').text='plugin.video.loadingqa'
manifest.write_bytes(ET.tostring(root))
print('Full skin XML/assets staged; providers/services are not under test')
