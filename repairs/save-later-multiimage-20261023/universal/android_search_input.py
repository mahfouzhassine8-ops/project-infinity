"""Actual Android Search input on the already guarded disposable API37 device."""
import json
import re
import time
import xml.etree.ElementTree as ET


def submit_node(values, selected=None):
    """Locate the actual TextView submission control, never a provider row.

    The original Surface changes its label from Search to Search All/POV on
    selection; it has never been an android.widget.Button. New helpers expose
    a stable content description, while the signed reference uses the exact
    dynamic label and clickable TextView contract.
    """
    labels={'Search All'} if selected=='all' else {'Search POV'} if selected=='plugin.video.pov' else {'Search','Search All','Search POV'}
    matches=[n for n in values if n.get('enabled')=='true' and n.get('clickable')=='true'
             and n.get('class') in ('android.widget.TextView','android.widget.Button')
             and (n.get('content-desc')=='Submit Infinity Search' or n.get('text') in labels)]
    if len(matches)!=1:return None
    return matches[0]


def editor_node(values):
    edits=[n for n in values if n.get('class')=='android.widget.EditText' and n.get('enabled')=='true']
    return edits[0] if len(edits)==1 and submit_node(values) is not None else None


def provider_node(values, name):
    matches=[n for n in values if n.get('enabled')=='true' and n.get('clickable')=='true' and
             (n.get('content-desc','').startswith(name+', ') or n.get('content-desc','').startswith(name+'. '))]
    return matches[0] if len(matches)==1 else None


def submit(device, out, owner, case, fixture_id):
    pid=owner['pid'];root=device.PROFILE+'/addon_data/'+fixture_id
    ready=root+'/search-ui-ready-'+str(pid)+'.json'
    failed=root+'/navigation-ready-'+str(pid)+'.json'
    def prepared():
        result=device.read_json(failed)
        if result and not result.get('passed'):
            raise RuntimeError('Search setup failed: '+str(result.get('failure')))
        return device.read_json(ready)
    proof=device.until(prepared,600)
    if proof.get('pid')!=pid or proof.get('mode')!=case:raise RuntimeError('Search input handshake mismatch')
    def nodes():
        device.shell('uiautomator','dump','/sdcard/infinity-search-ui.xml')
        raw=device.shell('cat','/sdcard/infinity-search-ui.xml')
        (out/'search-ui.xml').write_text(raw)
        return list(ET.fromstring(raw).iter('node'))
    def keyboard():
        values=nodes()
        edit=editor_node(values)
        return (values,edit) if edit is not None else None
    values,edit=device.until(keyboard,45)
    def tap(node):
        match=re.fullmatch(r'\[(\d+),(\d+)\]\[(\d+),(\d+)\]',node.get('bounds',''))
        if not match:raise RuntimeError('Android control bounds unavailable')
        left,top,right,bottom=map(int,match.groups())
        device.shell('input','tap',str((left+right)//2),str((top+bottom)//2))
    if case!='final-search-all-enter':
        choice=provider_node(values,'POV')
        if choice is None:raise RuntimeError('Exactly one available POV selector required')
        tap(choice)
    tap(edit);device.shell('input','text','The%sMatrix')
    values=nodes()
    if not any(n.get('class')=='android.widget.EditText' and n.get('text')=='The Matrix' for n in values):
        raise RuntimeError('Actual Android search text was not confirmed')
    (out/'search-before-memory.txt').write_text(device.shell('dumpsys','meminfo',str(pid),check=False))
    started=time.monotonic()
    if case.endswith('-button'):
        selected='all' if case=='final-search-all-enter' else 'plugin.video.pov'
        button=submit_node(values,selected)
        if button is None:raise RuntimeError('Exactly one enabled selected-provider Search control required')
        tap(button)
    else:
        device.shell('input','keyevent','66')
    marker=out/'search-submitted.json'
    marker.write_text(json.dumps(dict(pid=pid,mode=case,actual_android_input=True,
        input='Search button' if case.endswith('-button') else 'KEYCODE_ENTER',submitted_monotonic=started)))
    device.adb('push',marker,root+'/search-submitted-'+str(pid)+'.json')
    return json.loads(marker.read_text())
