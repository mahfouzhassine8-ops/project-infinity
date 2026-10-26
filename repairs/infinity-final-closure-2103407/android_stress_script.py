"""Script-only disposable bridge to the original Home Search action."""
from pathlib import Path
from android17_reference_observation import OLD,FIXTURE_SHA
import hashlib

ADDON='script.future.search.7fa29'
BUILTIN='RunScript(script.infinity.commandcenter,universal-search,movie)'
SCRIPT="import xbmc\nxbmc.executebuiltin("+repr(BUILTIN)+")\n"


def stage(folder,args,report,device,aid):
    from android17_candidate_probe import require_disposable
    require_disposable(device)
    if args.case!='final-search-all-enter' or aid!='service.future.persistence.7fa29' or Path(folder).resolve()!=args.out.resolve()/'fixture':
        raise ValueError('Only exact disposable Search stress stage permitted')
    raw=(OLD/'tracking/final-eight/android_selected.py').read_bytes()
    if hashlib.sha256(raw).hexdigest()!=FIXTURE_SHA or raw.count(('xbmc.executebuiltin('+repr(BUILTIN)+')').encode())!=1:
        raise ValueError('Original Home Search builtin differs')
    target=Path(folder)/ADDON
    if target.exists() or target.is_symlink():raise ValueError('Existing script bridge refused')
    target.mkdir()
    (target/'addon.xml').write_text('<addon id="'+ADDON+'" name="Disposable Home Search input" version="1.0.0" provider-name="Disposable CI"><requires><import addon="xbmc.python" version="3.0.0"/></requires><extension point="xbmc.python.script" library="default.py"/><extension point="xbmc.addon.metadata"><summary lang="en_GB">Exact Home Search action</summary><description lang="en_GB">Fresh API37 test fixture only</description><platform>all</platform><license>GPL-2.0-or-later</license></extension></addon>')
    (target/'default.py').write_text(SCRIPT)
    report['stress_script_bridge']=dict(addon=ADDON,builtin=BUILTIN,automatically_started=False,production_changes=False)


def enable(device):
    value=device.rpc('Addons.GetAddonDetails',{'addonid':ADDON,'properties':['version','enabled']})['addon']
    if value.get('version')!='1.0.0':raise ValueError('Wrong disposable script bridge')
    if not value.get('enabled'):
        if device.rpc('Addons.SetAddonEnabled',{'addonid':ADDON,'enabled':True})!='OK':
            raise RuntimeError('Cannot enable disposable script bridge')


def launch(device):
    return device.rpc('Addons.ExecuteAddon',{'addonid':ADDON,'wait':False})
