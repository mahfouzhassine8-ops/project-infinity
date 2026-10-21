"""Read-only actual Kodi-resolved code, kept separate from on-disk copies."""
import hashlib,json,os,time
from pathlib import Path
import xbmc,xbmcaddon,xbmcgui,xbmcvfs
IDS=('script.infinity.commandcenter','script.infinity.uirepair','script.infinity.watchedbridge','skin.infinity.diggz','script.infinity.rails','script.kodihealthcenter','service.infinity.compat')

def collect():
 result={'schema':1,'pid':os.getpid(),'epoch_ms':int(time.time()*1000),'runtime_resolved':True,'read_only':True,'proves_physical_acceptance':False,'addons':[]}
 for aid in IDS:
  row={'id':aid};result['addons'].append(row)
  try:
   addon=xbmcaddon.Addon(aid);raw_root=addon.getAddonInfo('path');root=Path(xbmcvfs.translatePath(raw_root))
   row.update(version=addon.getAddonInfo('version'),resolved_directory=raw_root,enabled=xbmc.getCondVisibility('System.AddonIsEnabled('+aid+')'),files={},state='OBSERVED')
   names={'addon.xml'}
   if aid=='script.infinity.commandcenter':names.update(('addon.xml', 'checkpoint_runtime.py', 'common.py', 'context.py', 'default.py', 'experience.py', 'infinity_search.py', 'infinity_settings.py', 'infinity_trakt.py', 'persistence_participant.py', 'plugin.py', 'resources/settings.xml', 'resume_hub.py', 'runtime_visibility.py', 'service.py', 'skin_upgrade.py', 'view_mode.py'))
   if aid=='script.infinity.uirepair':names.update(('home_option_b.py','runtime.py','controller_access.py','CONTROLLER-PREIMAGES.json','resources/skins/Default/1080i/InfinityHomeOptionB.xml'))
   if aid=='script.kodihealthcenter':names.update(('default.py','service.py','khc_lifecycle.py','khc_diagnostics.py','infinity_runtime_identity.py'))
   if aid=='script.infinity.rails':names.update(('default.py','service.py','addon.xml'))
   if aid=='script.infinity.watchedbridge':names.update(('controller.py','CONTROLLER-PREIMAGES.json'))
   if aid=='skin.infinity.diggz':names.update(('unified/Home.xml','Infinity-Protected-Manifest.json','infinity-skin.json'))
   if aid=='service.infinity.compat':names.update(('runtime_service.py','compat_runtime.py','checkpoint_runtime.py','resources/settings.xml'))
   for n in sorted(names):
    p=root/n
    if p.is_symlink() or not p.is_file() or p.stat().st_size>4194304:row['files'][n]={'state':'MISSING_OR_UNVERIFIED'};continue
    row['files'][n]={'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}
   dependencies=__import__('xml.etree.ElementTree',fromlist=['fromstring']).fromstring((root/'addon.xml').read_bytes())
   row['dependencies']=[dict(e.attrib) for e in dependencies.findall('requires/import')]
  except Exception as error:row.update(state='UNVERIFIED',error_type=type(error).__name__)
 try:
  owner=xbmcaddon.Addon('script.infinity.commandcenter');home=xbmcgui.Window(10000)
  result['settings']={key:owner.getSetting(key) for key in ('ambient_home','motion_mode')}
  result['home']={key:home.getProperty(key) for key in ('Infinity.AmbientHome.Mode','Infinity.MotionModeUser','Infinity.MotionModeEffective','Infinity.EffectiveViewMode','Infinity.SystemTheme','Infinity.NativeSystemTheme')}
 except Exception as error:result['settings_error']=type(error).__name__
 return result
