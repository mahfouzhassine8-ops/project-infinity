"""Observe actual unchanged Power UI; no direct Close intent in this lane."""
import hashlib
from pathlib import Path
import time
import xml.etree.ElementTree as ET
from zipfile import ZipFile

SKIN='assets/addons/skin.infinity.diggz/unified/DialogButtonMenu.xml'
ACTION='com.projectinfinity.kodi.action.CLOSE_KODI'
ACTIVITY='com.projectinfinity.kodi.InfinityPowerControlActivity'
BUILTIN='StartAndroidActivity(com.projectinfinity.kodi,'+ACTION+',,,,,,,'+ACTIVITY+')'


def source_route(apk):
    with ZipFile(apk) as archive:raw=archive.read(SKIN)
    root=ET.fromstring(raw)
    rows=root.findall('.//control[@id="200"]')
    if len(rows)!=1 or rows[0].findtext('label')!='CLOSE KODI':
        raise AssertionError('Actual shipped Power Close row differs')
    android=[n.text for n in rows[0].findall('onclick') if n.get('condition')=='System.Platform.Android']
    if android!=['SetProperty(Infinity.Close.InProgress,true,Home)',BUILTIN]:
        raise AssertionError('Visible Close UI does not map to the tested backend')
    if root.findtext('defaultcontrol')!='200':
        raise AssertionError('Actual default Power focus differs')
    return dict(skin_member=SKIN,skin_sha256=hashlib.sha256(raw).hexdigest(),control=200,
                action=ACTION,activity=ACTIVITY,exact_builtin=BUILTIN,backend_matches=True)


def partition_processes(rows,owner):
    return dict(kodi_engine=[p for p in rows if p['pid']==owner['pid']],
                android_coordinator=[p for p in rows if p['pid']!=owner['pid'] and p['name']=='com.projectinfinity.kodi'],
                other_owned_processes=[p for p in rows if p['pid']!=owner['pid'] and p['name']!='com.projectinfinity.kodi'])


def preference(transport):
    path=transport.PRIVATE+'/shared_prefs/infinity_experience.xml'
    # cat of a nonexistent file returns no stdout; retain absence explicitly.
    raw=transport.shell('cat',path,check=False)
    if not raw:return dict(present=False,sha256=None,remembered='ask')
    root=ET.fromstring(raw)
    value=root.find('string[@name="default"]')
    saved=value.text if value is not None else ''
    if saved not in ('','infinity','live'):raise AssertionError('Unknown remembered experience')
    return dict(present=True,sha256=hashlib.sha256(raw.encode()).hexdigest(),
                remembered={'':'ask','infinity':'infinity','live':'cobra'}[saved])


def close(transport,apk,out):
    proof=source_route(apk);out=Path(out)
    transport.rpc('GUI.ActivateWindow',{'window':'shutdownmenu'})
    deadline=time.monotonic()+15
    labels=['Control.GetLabel(200)','System.CurrentControlID','System.CurrentControl']
    required_flags=['Window.IsActive(shutdownmenu)','Control.IsVisible(200)','Control.IsEnabled(200)']
    while time.monotonic()<deadline:
        state=transport.rpc('XBMC.GetInfoLabels',{'labels':labels})
        flags=transport.rpc('XBMC.GetInfoBooleans',{'booleans':required_flags})
        if (state.get(labels[0])=='CLOSE KODI' and state.get(labels[1])=='200' and
                all(flags.get(k) is True for k in required_flags)):
            break
        time.sleep(.1)
    else:raise AssertionError('Actual visible, enabled and focused Power Close row not observed')
    transport.adb('shell','screencap','-p','/sdcard/infinity-power-ui-before.png')
    transport.adb('pull','/sdcard/infinity-power-ui-before.png',out/'power-ui-before.png')
    proof.update(observed_labels=state,observed_flags=flags,input='Android KEYCODE_DPAD_CENTER')
    # Android key input activates the actual skin button and its existing onclick.
    # Never invoke the backend intent or write its receipts from this lane.
    proof['input_result']=transport.shell('input','keyevent','23')
    return proof
