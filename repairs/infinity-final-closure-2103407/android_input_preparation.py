"""Prepare actual system IME on a fresh API37 fixture before Infinity first launch."""
import json
from pathlib import Path
import re
import xml.etree.ElementTree as ET

PACKAGE='com.projectinfinity.kodi'
SETTINGS={'com.android.settings','com.google.android.settings.intelligence'}


def require(value,message):
    if not value:raise ValueError(message)


def warm(device,out):
    require(device.PACKAGE==PACKAGE and device.shell('getprop','ro.kernel.qemu').strip()=='1' and
            device.shell('getprop','ro.build.version.sdk').strip()=='37','IME preparation refuses other devices')
    require(not device.shell('pm','list','packages',PACKAGE).strip() and not device.running_engine(),
            'IME preparation requires no existing Infinity installation')
    out=Path(out)/'IME-PREPARATION';out.mkdir(exist_ok=False)
    report=dict(passed=False,preparation_only=True,Infinity_launched=False,typed_query=False,
                preferences_written=False,IME_package_changed=False,cold_IME_measured=False)
    save=lambda:(out/'PREPARATION.json').write_text(json.dumps(report,indent=2)+'\n')
    def nodes():
        device.shell('uiautomator','dump','/sdcard/infinity-ime-preparation.xml')
        raw=device.shell('cat','/sdcard/infinity-ime-preparation.xml')
        (out/'latest-ui.xml').write_text(raw)
        return list(ET.fromstring(raw).iter('node'))
    def tap(node):
        match=re.fullmatch(r'\[(\d+),(\d+)\]\[(\d+),(\d+)\]',node.get('bounds',''))
        require(match,'Actual Settings Search bounds unavailable')
        left,top,right,bottom=map(int,match.groups())
        require(right>left and bottom>top,'Invalid Settings Search bounds')
        device.shell('input','tap',str((left+right)//2),str((top+bottom)//2))
    try:
        report['normal_settings_launch']=device.shell('am','start','-W','-a','android.settings.SETTINGS')
        def search_control():
            choices=[n for n in nodes() if n.get('package') in SETTINGS and n.get('enabled')=='true' and
                any(n.get(k,'').casefold()=='search settings' for k in ('text','content-desc'))]
            if len(choices)>1:raise ValueError('Ambiguous actual Settings Search control')
            return (choices[0],) if choices else None
        tap(device.until(search_control,45)[0])
        def editor():
            matches=[n for n in nodes() if n.get('package') in SETTINGS and
                n.get('class')=='android.widget.EditText' and n.get('enabled')=='true']
            return (matches[0],) if len(matches)==1 else None
        tap(device.until(editor,45)[0])
        import android_input_readiness
        recovery={'phase':'unused'}
        def prepared_keyboard():
            if android_input_readiness.ready(device,out):return True
            values=nodes()
            if recovery['phase']=='editor':
                edits=[n for n in values if n.get('package') in SETTINGS and
                       n.get('class')=='android.widget.EditText' and n.get('enabled')=='true']
                if len(edits)==1:tap(edits[0]);recovery['phase']='used'
                return False
            if recovery['phase']!='unused':return False
            controls=[n for n in values if n.get('package')=='com.android.settings' and
                      n.get('enabled')=='true' and n.get('class')!='android.widget.EditText' and
                      any(n.get(k,'').casefold()=='search settings' for k in ('text','content-desc'))]
            if len(controls)!=1:return False
            log=device.adb('logcat','-d','-v','threadtime','-s','ActivityManager:I',check=False)
            if not re.search(r'Killing \d+:com\.google\.android\.settings\.intelligence/[^\n]*: change com\.google\.android\.settings\.intelligence',log):
                return False
            report['system_settings_recovery']='One normal UI re-entry after observed Android Settings Intelligence replacement'
            tap(controls[0]);recovery['phase']='editor'
            return False
        # Keep the original wait budget and actual current-PID/body/shown proof.
        device.until(prepared_keyboard,90)
        report['actual_IME_proof']=json.loads((out/'IME-READINESS.json').read_text())
        require(report['actual_IME_proof'].get('ready') is True,'Actual system keyboard body not ready')
        device.shell('input','keyevent','3')
        report['passed']=True;save();return report
    finally:save()
