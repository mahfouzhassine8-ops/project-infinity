"""Disposable actual native multi-image workload; never shipped or granted writer authority."""
import json
from pathlib import Path
import re
import time
from urllib.parse import quote

ADDON='script.future.multiimage.7fa29'
IDS=set(range(2100,2116))
SCRIPT='''import gc,json,os
from pathlib import Path
import xbmc,xbmcaddon,xbmcgui,xbmcvfs
addon=xbmcaddon.Addon()
root=Path(xbmcvfs.translatePath(addon.getAddonInfo('profile')))
root.mkdir(parents=True,exist_ok=True)
window=xbmcgui.WindowXML('native-images.xml',addon.getAddonInfo('path'),'Default','1080i')
window.show()
xbmc.sleep(4000)
window_id=xbmcgui.getCurrentWindowId()
window.close()
del window
gc.collect()
(root/('native-image-done-'+str(os.getpid())+'.json')).write_text(json.dumps(dict(pid=os.getpid(),window=window_id,controls=list(range(2100,2116)))))
'''


def image_path(control):
    # A relative wrapped URL is considered cached by Kodi before the job.
    # A full noncached path in this fixture's own profile exercises the factory.
    inner='special://profile/addon_data/'+ADDON+'/native-directory-'+str(control)
    return 'image://'+quote(inner,safe='')+'/'


def xml():
    controls=''.join('<control type="multiimage" id="'+str(i)+'"><left>'+str((i-2100)%4*240)+'</left><top>'+str((i-2100)//4*200)+'</top><width>240</width><height>200</height><imagepath>'+image_path(i)+'</imagepath><timeperimage>10000</timeperimage><fadetime>0</fadetime><randomize>false</randomize><loop>yes</loop></control>' for i in sorted(IDS))
    return '<window><defaultcontrol always="true">2100</defaultcontrol><coordinates><system>1</system></coordinates><controls>'+controls+'</controls></window>'


def stage(folder,args,report,device,aid):
    from android17_candidate_probe import require_disposable
    require_disposable(device)
    if args.case!='final-participant' or aid!='service.future.persistence.7fa29' or Path(folder).resolve()!=args.out.resolve()/'fixture':
        raise ValueError('Only exact disposable independent stage permitted')
    target=Path(folder)/ADDON
    if target.exists() or target.is_symlink():raise ValueError('Existing native control refused')
    target.mkdir()
    (target/'addon.xml').write_text('<addon id="'+ADDON+'" name="Disposable native image control" version="1.0.0" provider-name="Disposable CI"><requires><import addon="xbmc.python" version="3.0.0"/></requires><extension point="xbmc.python.script" library="default.py"/><extension point="xbmc.addon.metadata"><summary lang="en_GB">Actual native multi-image directory workload</summary><description lang="en_GB">Fresh API37 test fixture only</description><platform>all</platform><license>GPL-2.0-or-later</license></extension></addon>')
    (target/'default.py').write_text(SCRIPT)
    layout=target/'resources/skins/Default/1080i/native-images.xml';layout.parent.mkdir(parents=True);layout.write_text(xml())
    report['native_multiimage_fixture']=dict(addon=ADDON,controls=sorted(IDS),production_changes=False,automatically_started=False)


def verify_log(text,window):
    if type(window) is not int or window<=0:raise AssertionError('Actual native window identity absent')
    resource=r'window='+str(window)+r';control=(21\d\d);multiimage-protocol:image'
    began={};retired={}
    for line in text.splitlines():
        start=re.search(r'INFINITY_MULTIIMAGE_BEGIN token=(\d+) job=(\d+) resource='+resource+r'$',line)
        end=re.search(r'INFINITY_MULTIIMAGE_RETIRED token=(\d+) job=(\d+) unchanged_receipt=(true|false) phase=(\S+) reason=(.*?) resource='+resource+r'$',line)
        if start:
            token,job,control=map(int,start.groups())
            if control not in IDS:continue
            if control in began:raise AssertionError('Duplicate native control start')
            began[control]=(token,job)
        if end:
            token,job,unchanged,phase,reason,control=end.groups();control=int(control)
            if control not in IDS:continue
            if control in retired:raise AssertionError('Duplicate native control retirement')
            if unchanged!='true' or phase!='completion_receipt_verified' or reason:
                raise AssertionError('Native multiimage receipt is unresolved')
            retired[control]=(int(token),int(job))
    if set(began)!=IDS or retired!=began or len(set(began.values()))!=16:
        raise AssertionError('All16 actual native image jobs and exact retirement identities required')
    return dict(window=window,controls=sorted(IDS),actual_native_jobs=16,verified_readonly_receipts=16,
                jobs={str(k):dict(token=v[0],job=v[1]) for k,v in began.items()})


def run(transport,owner,out):
    out=Path(out);report=dict(passed=False,owner=owner)
    save=lambda:(out/'NATIVE-MULTIIMAGE-CONTROL.json').write_text(json.dumps(report,indent=2)+'\n')
    try:
        transport.rpc('Addons.ExecuteAddon',{'addonid':ADDON,'wait':False})
        deadline=time.monotonic()+45
        target=transport.PROFILE+'/addon_data/'+ADDON+'/native-image-done-'+str(owner['pid'])+'.json'
        while time.monotonic()<deadline:
            done=transport.read_json(target)
            if done.get('pid')==owner['pid']:break
            time.sleep(.25)
        else:raise AssertionError('Actual native image window did not finish')
        report['script_observation']=done;save()
        if done.get('controls')!=sorted(IDS):raise AssertionError('Actual window control identity differs')
        deadline=time.monotonic()+15
        while True:
            raw=transport.shell('cat',transport.PROFILE+'/../temp/kodi.log',check=False)
            (out/'native-multiimage-kodi.log').write_text(raw)
            try:report['native']=verify_log(raw,done.get('window'));break
            except AssertionError:
                if time.monotonic()>=deadline:raise
                time.sleep(.25)
        report['passed']=True;save();return report
    finally:save()
