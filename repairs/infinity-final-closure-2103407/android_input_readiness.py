"""Fresh Google API37 emulator IME readiness; no text editing or retry."""
import hashlib
import json
from pathlib import Path
import re

IME='com.google.android.inputmethod.latin'
DRIVER_BEFORE="        return (values,edit) if edit is not None else None"
DRIVER_AFTER="        return (values,edit) if edit is not None and _candidate_ime_ready(device,out) else None"


def proof(state,log,pids):
    shown=bool(re.search(r'\bmInputShown\s*[=:]\s*true\b',state))
    current=IME in state
    body=[line for line in log.splitlines() if 'onKeyboardViewShown' in line and 'keyboardType=BODY' in line and
          len(line.split())>4 and line.split()[2] in pids]
    return dict(ready=shown and current and bool(body),input_shown=shown,current_expected_IME=current,
                keyboard_body_shown=bool(body),actual_IME_pids=pids,last_body_event=body[-1] if body else '')


def ready(device,out):
    # Only the already admitted fresh Google API37 CI emulator uses this path.
    # A displayed EditText alone is not a rendered/ready IME input connection.
    if device.shell('getprop','ro.kernel.qemu').strip()!='1' or device.shell('getprop','ro.build.version.sdk').strip()!='37':
        raise ValueError('IME readiness adapter refuses other devices')
    state=device.shell('dumpsys','input_method',check=False)
    log=device.adb('logcat','-d','-v','threadtime','-s','GoogleInputMethodService:I',check=False)
    pids=device.shell('pidof',IME,check=False).split()
    value=proof(state,log,pids)
    out=Path(out);(out/'input-method-state.txt').write_text(state)
    (out/'input-method-view-events.txt').write_text(log)
    (out/'IME-READINESS.json').write_text(json.dumps(value,indent=2)+'\n')
    return value['ready']


def instrument(driver,original,wanted):
    raw=Path(original).read_bytes()
    if hashlib.sha256(raw).hexdigest()!=wanted:raise ValueError('Frozen Android input driver differs')
    text=raw.decode()
    if text.count(DRIVER_BEFORE)!=1:raise ValueError('Frozen keyboard readiness boundary differs')
    changed=text.replace(DRIVER_BEFORE,DRIVER_AFTER,1)
    if changed.replace(DRIVER_AFTER,DRIVER_BEFORE,1)!=text:raise ValueError('Original input/assertions changed')
    namespace={'__file__':str(original),'_candidate_ime_ready':ready}
    exec(compile(changed,str(original),'exec'),namespace)
    driver.submit=namespace['submit']
