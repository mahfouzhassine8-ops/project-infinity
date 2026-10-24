"""Actual Android Search input on the already guarded disposable API37 device."""
import json
import re
import time
import xml.etree.ElementTree as ET


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
        edits=[n for n in values if n.get('class')=='android.widget.EditText']
        return (values,edits[0]) if len(edits)==1 and any(n.get('text')=='Search' for n in values) else None
    values,edit=device.until(keyboard,45)
    def tap(node):
        match=re.fullmatch(r'\[(\d+),(\d+)\]\[(\d+),(\d+)\]',node.get('bounds',''))
        if not match:raise RuntimeError('Android control bounds unavailable')
        left,top,right,bottom=map(int,match.groups())
        device.shell('input','tap',str((left+right)//2),str((top+bottom)//2))
    if case!='final-search-all-enter':
        choices=[n for n in values if n.get('content-desc','').startswith('POV. ')]
        if len(choices)!=1:raise RuntimeError('Exactly one available POV selector required')
        tap(choices[0])
    tap(edit);device.shell('input','text','The%sMatrix')
    values=nodes()
    if not any(n.get('class')=='android.widget.EditText' and n.get('text')=='The Matrix' for n in values):
        raise RuntimeError('Actual Android search text was not confirmed')
    (out/'search-before-memory.txt').write_text(device.shell('dumpsys','meminfo',str(pid),check=False))
    started=time.monotonic()
    if case.endswith('-button'):
        buttons=[n for n in values if n.get('text')=='Search' and n.get('class','').endswith('Button')]
        if len(buttons)!=1:raise RuntimeError('Exactly one Search button required')
        tap(buttons[0])
    else:
        device.shell('input','keyevent','66')
    marker=out/'search-submitted.json'
    marker.write_text(json.dumps(dict(pid=pid,mode=case,actual_android_input=True,
        input='Search button' if case.endswith('-button') else 'KEYCODE_ENTER',submitted_monotonic=started)))
    device.adb('push',marker,root+'/search-submitted-'+str(pid)+'.json')
    return json.loads(marker.read_text())
