"""Explicit capture/export only; never runs a service or changes save policy."""
import hashlib
import json
import re
import time
import zipfile
from pathlib import Path


class RailTrace:
    def __init__(self, query, section, xbmc):
        value=query.get('infinity_trace',[''])[0]
        self.request=value if re.fullmatch(r'r[0-9]{1,20}',value or '') else ''
        self.section=section;self.xbmc=xbmc;self.started=time.monotonic()
        self.mark('helper_start')

    def mark(self, stage, items=0):
        if not self.request:return
        record=dict(schema=1,request=self.request,section=self.section,stage=stage,
            monotonic_ms=time.monotonic()*1000,elapsed_ms=(time.monotonic()-self.started)*1000,items=items)
        self.xbmc.log('INFINITY_RAIL_TIMING '+json.dumps(record,separators=(',',':')),self.xbmc.LOGINFO)


def collect(xa, vfs, destination):
    """Only reviewed code/evidence files. Never add provider settings or credentials."""
    files={};manifest={'schema':1,'diagnostic_only':True,'physical_acceptance':False,'installed':{},'unavailable':[]}
    def read(label,path,limit=1024*1024):
        try:
            with open(path,'rb') as src:raw=src.read(limit+1)
            if len(raw)>limit:manifest['unavailable'].append(label+': exceeds cap');return
            files[label]=raw
        except OSError:manifest['unavailable'].append(label)
    for addon_id in ['skin.infinity.diggz','script.infinity.rails','script.infinity.commandcenter','plugin.video.umbrella','script.trakt']:
        try:
            addon=xa.Addon(addon_id);root=Path(vfs.translatePath(addon.getAddonInfo('path')))
            manifest['installed'][addon_id]={'version':addon.getAddonInfo('version'),'hashes':{}}
            names=['addon.xml']
            if addon_id=='plugin.video.umbrella':names+=['service.py','resources/lib/modules/control.py','resources/lib/modules/tools.py','resources/lib/modules/service_settings.py']
            for name in names:
                label='installed-code/'+addon_id+'/'+name
                read(label,root/name,192*1024)
                if label in files:manifest['installed'][addon_id]['hashes'][name]=hashlib.sha256(files[label]).hexdigest()
        except RuntimeError:manifest['unavailable'].append(addon_id)
    for name in ['infinity-stability-probe.jsonl','infinity-stability-probe.jsonl.previous']:
        read('native/'+name,Path(vfs.translatePath('special://temp/'+name)),768*1024)
    root=Path(vfs.translatePath('special://profile/addon_data/script.infinity.commandcenter/.android-checkpoint/'))
    for name in ['coordinator-receipt.json','addon-quarantine.tsv','android-timeline.jsonl']:
        read('checkpoint/'+name,root/name,512*1024)
    for name in ['kodi.log','kodi.old.log']:
        try:
            with open(vfs.translatePath('special://logpath/'+name),'rb') as src:
                src.seek(0,2);size=src.tell();src.seek(max(0,size-8*1024*1024));raw=src.read()
            rows=[line for line in raw.splitlines() if b'INFINITY_RESUME_TIMING' in line or b'INFINITY_RAIL_TIMING' in line]
            files['timing/'+name+'.jsonl']=b'\n'.join(rows[-1000:])+b'\n'
        except OSError:manifest['unavailable'].append(name)
    files['manifest.json']=json.dumps(manifest,indent=2).encode()
    destination=Path(destination);destination.parent.mkdir(parents=True,exist_ok=True)
    with zipfile.ZipFile(destination,'w',zipfile.ZIP_DEFLATED) as archive:
        for name,raw in files.items():archive.writestr(name,raw)
    return manifest


def menu(xbmc, xa, gui, vfs, profile, monitor):
    home=gui.Window(10000)
    ready=home.getProperty('Infinity.Stability.ProbeVersion')=='1'
    options=['Arm five-minute stability capture','Export current/previous evidence','Cancel']
    selected=gui.Dialog().select('INFINITY STABILITY — DIAGNOSTIC',options)
    if selected==0:
        if not ready:
            gui.Dialog().ok('Stability capture unavailable','Install the matching Stability Probe APK, then reopen Infinity.');return
        home.setProperty('Infinity.Stability.ProbeArm','true')
        xbmc.executebuiltin('ActivateWindow(Home)')
        gui.Dialog().notification('Stability capture armed','Reproduce the delay, or use Normal Close. Export after reopening.',time=6500)
    elif selected==1:
        # Ask the existing watchdog for a snapshot; no extra polling thread.
        if ready:
            home.setProperty('Infinity.Stability.ProbeSnapshot','true')
            if monitor.waitForAbort(0.8):return
        target=Path(profile)/('Infinity-Stability-'+time.strftime('%Y%m%d-%H%M%S')+'.zip')
        result=collect(xa,vfs,target)
        folder=gui.Dialog().browse(3,'Choose a folder to export stability evidence','files')
        if folder:
            destination=folder.rstrip('/\\')+'/'+target.name
            if vfs.copy(str(target),destination):gui.Dialog().ok('Stability evidence exported',destination)
            else:gui.Dialog().ok('Export failed','Capture retained at '+str(target))
        else:gui.Dialog().ok('Capture saved',str(target))
