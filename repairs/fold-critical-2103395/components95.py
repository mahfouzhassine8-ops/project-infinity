"""Narrow corrections over the permanently signed 2103394 APK, never user data."""
from __future__ import annotations
import ast,hashlib,json,sys,os
from pathlib import Path
from zipfile import ZipFile
import xml.etree.ElementTree as ET
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1]
sys.path.insert(0,str(HERE.parent/'fold-corrective-2103394'))
import components94 as old
from native94 import once,require
PARENT='d61fdb4f3e5ee260810082a17174fb6973140de435857c706558cbe41c92547d'
COMMIT='4e4ca79f134ce9b0ac22c66cd13e246a11207de8'
CC,UI,WB,SKIN,HEALTH=old.CC,old.UI,old.WB,old.SKIN,old.HEALTH
PACKAGES=[(CC,'0.3.5.24','0.3.5.25'),(WB,'1.0.5','1.0.6'),(UI,'0.1.6','0.1.7'),(HEALTH,'2.5.21','2.5.22'),(SKIN,'1.0.5.231','1.0.5.232'),('script.infinity.rails','0.2.7','0.2.7')]
sha=old.sha;digest=old.digest

def read_parent(path):
 require(digest(path)==PARENT,'wrong signed 2103394 baseline')
 with ZipFile(path) as z:
  require(z.testzip() is None and len(z.namelist())==len(set(z.namelist())),'invalid baseline')
  return {n[14:]:z.read(n) for n in z.namelist() if n.startswith('assets/addons/') and not n.endswith('/') and n.split('/')[2] in {a for a,_,_ in PACKAGES}}

def option_b(raw):
 raw=once(raw,b"CONTROLS = {8101: 'movies', 8102: 'tvshows', 8601: 'movies', 8602: 'tvshows', 8701: 'movies', 8702: 'tvshows', 8801: 'movies', 8802: 'tvshows'}",b"CONTROLS = {8101: 'movies', 8102: 'tvshows', 8801: 'movies', 8802: 'tvshows'}")
 require(raw.count(b"args[0] not in tuple(str(value) for value in CONTROLS)")==1,'actual shipped control guard differs')
 # Distinguish each rejection without relaxing any proof or item guard.
 replacements=[
 (b"    if xbmcgui.getCurrentWindowId() != 10000:\n        return None",b"    if xbmcgui.getCurrentWindowId() != 10000:\n        _trace(xbmc, 'python.window', 'not_home')\n        return None"),
 (b"    if xbmcgui.getCurrentWindowDialogId() not in (0, -1, 9999):\n        return None",b"    if xbmcgui.getCurrentWindowDialogId() not in (0, -1, 9999):\n        _trace(xbmc, 'python.window', 'modal_active')\n        return None"),
 (b"        if control not in CONTROLS or (native is not None and control != native.control):\n            return None",b"        if control not in CONTROLS or (native is not None and control != native.control):\n            _trace(xbmc, 'python.focus', 'mismatch', control)\n            return None"),
 (b"        if section != CONTROLS[control]:\n            return None",b"        if section != CONTROLS[control]:\n            _trace(xbmc, 'python.section', 'mismatch', control)\n            return None"),
 (b"            if observed_label and observed_label != native.label:\n                return None",b"            if observed_label and observed_label != native.label:\n                _trace(xbmc, 'python.label', 'mismatch', control, idx)\n                return None"),
 (b"            if path and path != native.path:\n                return None",b"            if path and path != native.path:\n                _trace(xbmc, 'python.path', 'mismatch', control, idx)\n                return None"),
 (b"        if not title or not _media_path(path):\n            return None",b"        if not title or not _media_path(path):\n            _trace(xbmc, 'python.metadata', 'missing', control, idx)\n            return None"),
 (b"        choice=window.selected_action",b"        choice=window.selected_action\n        _trace(xbmc, 'popup.closed', choice or 'cancelled', native.control, native.index)")]
 for a,b in replacements:raw=once(raw,a,b)
 return raw

def common(raw):
 # Same checked Python byte writes/rename/fsync path as existing atomic_json;
 # backup content does not require source timestamps/xattrs/permissions.
 helper=b'''def _copy_verified_bytes(source, target):
    source, target = Path(source), Path(target)
    if source.is_symlink() or target.is_symlink():
        raise RuntimeError('Linked UI backup source or target rejected')
    fd, name = tempfile.mkstemp(prefix='.' + target.name + '.', suffix='.tmp', dir=str(target.parent))
    try:
        expected = hashlib.sha256()
        with source.open('rb') as src, os.fdopen(fd, 'wb') as dst:
            for chunk in iter(lambda: src.read(65536), b''):
                expected.update(chunk)
                if dst.write(chunk) != len(chunk):
                    raise OSError('Incomplete UI backup')
            dst.flush()
            os.fsync(dst.fileno())
        actual = hashlib.sha256()
        with open(name, 'rb') as saved:
            for chunk in iter(lambda: saved.read(65536), b''):
                actual.update(chunk)
        if expected.digest() != actual.digest():
            raise OSError('UI backup verification failed')
        os.replace(name, target)
        parent_fd = os.open(str(target.parent), os.O_RDONLY | os.O_DIRECTORY)
        try:
            os.fsync(parent_fd)
        finally:
            os.close(parent_fd)
    finally:
        if os.path.exists(name):
            os.unlink(name)


'''
 raw=once(raw,b'@persistence_serialized\ndef backup_ui_if_healthy',helper+b'@persistence_serialized\ndef backup_ui_if_healthy')
 # Only the current automatic backup; preserve unrelated manual restore logic.
 raw=once(raw,b'                shutil.copy2(source, dest)',b'                _copy_verified_bytes(source, dest)')
 return raw

def home(raw):
 root=ET.fromstring(raw);parents={c:p for p in root.iter() for c in p};count=0
 for ctrl in root.iter('control'):
  visible=ctrl.findtext('visible','');label=ctrl.findtext('label','')
  if label=='$INFO[Container(9000).ListItem.Property(widgetName.2)]' and ',compact)' in visible:
   old.settext(ctrl,'top','56.8%');count+=1
  if ctrl.findtext('texture')=='infinity_polish/infinity_mark.png' and ',compact)' in parents[ctrl].findtext('visible',''):
   old.settext(ctrl,'left','104');old.settext(ctrl,'top','8');count+=1
 require(count==2,'exact Compact heading/logo controls required')
 return old.xmlbytes(root)

def components(original):
 final=dict(original)
 final[CC+'/common.py']=common(original[CC+'/common.py'])
 for name,body in list(final.items()):
  if name.startswith(HEALTH+'/') and name.endswith('.py'):
   final[name]=body.replace(b"2.5.21",b"2.5.22")
 final[HEALTH+'/infinity_runtime_identity.py']=(HERE/'infinity_runtime_identity.py').read_bytes()
 final[HEALTH+'/khc_diagnostics.py']=once(original[HEALTH+'/khc_diagnostics.py'],b"        bundle.json('environment-now.json', environment, 'environment_at_export_not_at_crash')",b"        bundle.json('environment-now.json', environment, 'environment_at_export_not_at_crash')\n        from infinity_runtime_identity import collect as runtime_identity\n        bundle.json('runtime-component-identity.json', runtime_identity(), 'actual_resolved_kodi_addons')")
 final[CC+'/infinity_settings.py']=(HERE/'infinity_settings.py').read_bytes()
 final[CC+'/infinity_search.py']=(HERE/'infinity_search.py').read_bytes()
 final[UI+'/home_option_b.py']=option_b(original[UI+'/home_option_b.py'])
 final[UI+'/runtime.py']=once(original[UI+'/runtime.py'],b"    if home.getProperty('Infinity.UI.MenuActive'):\n        return",b"    if home.getProperty('Infinity.UI.MenuActive'):\n        if args and args[0] == 'option-b':\n            _trace(xbmc, 'python.entry', 'another_menu_active')\n        return")
 for name,raw in list(final.items()):
  if name==SKIN+'/unified/Home.xml': final[name]=home(raw)
  if name.startswith(SKIN+'/') and name.endswith('/Custom_1194_InfinityCommandCenter.xml'):
   final[name]=once(raw,b'INFINITY COMMAND CENTER  \xe2\x80\xa2  SEARCH',b'INFINITY COMMAND CENTER')
 for aid,previous,version in PACKAGES:
  if previous!=version:final[aid+'/addon.xml']=once(final[aid+'/addon.xml'],('version="'+previous+'"').encode(),('version="'+version+'"').encode())
 final[WB+'/controller.py']=once(final[WB+'/controller.py'],b'"0.3.5.24"',b'"0.3.5.25"')
 # Pin the setting schema as well as every original executable controller source.
 pins={n.split('/',1)[1]:sha(b) for n,b in final.items() if n.startswith(CC+'/') and (n.endswith('.py') or n.endswith('/addon.xml') or n==CC+'/resources/settings.xml')}
 for aid in (UI,WB):final[aid+'/CONTROLLER-PREIMAGES.json']=(json.dumps(pins,indent=2,sort_keys=True)+'\n').encode()
 for leaf in ('infinity-skin.json','Infinity-Protected-Manifest.json'):
  key=SKIN+'/'+leaf;data=json.loads(final[key]);data.update(candidate=232,skin_version='1.0.5.232',candidate_locked=False)
  if 'version' in data:data['version']='1.0.5.232'
  if 'candidate_version' in data:data['candidate_version']='1.0.5.232'
  data['critical_232']={'source_parent_commit':COMMIT,'physical_fold_verified':False,'final_lock':False,'compact_header_only':True}
  if 'protected_files' in data:data['protected_files']={p:sha(final[SKIN+'/'+p]) for p in data['protected_files']}
  final[key]=(json.dumps(data,indent=2,sort_keys=True)+'\n').encode()
 for name,body in final.items():
  if name.startswith(HEALTH+'/') and name.endswith('.py'):
   body=body.replace(b'2.5.21',b'2.5.22');final[name]=body
  if name.endswith('.py'):ast.parse(body.decode(),filename=name)
  elif name.endswith('.xml'):ET.fromstring(body)
 return final

def evidence_manifest(final):
 result={}
 for name,body in final.items():
  aid,rel=name.split('/',1)
  if rel.endswith(('.py','.xml','.json')) and len(body)<=4194304:
   result.setdefault(aid,{})[rel]=sha(body)
 return (json.dumps(result,sort_keys=True,separators=(',',':'))+'\n').encode()

def ledger(before,after):
 return {'parent_apk_sha256':PARENT,'parent_source_commit':COMMIT,'versions':{a:v for a,_,v in PACKAGES},'changed':{n:{'before':sha(before[n]) if n in before else None,'after':sha(after[n])} for n in sorted(after) if before.get(n)!=after[n]},'removed':sorted(set(before)-set(after)),'physical_fold_verified':False,'final_lock':False}

def stage(apk,out):
 before=read_parent(apk);after=components(before)
 require(not out.exists(),'component destination exists')
 for n,b in after.items():p=out/n;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(b)
 return ledger(before,after)
if __name__=='__main__':print(json.dumps(stage(Path(sys.argv[1]),Path(sys.argv[2])),indent=2,sort_keys=True))
