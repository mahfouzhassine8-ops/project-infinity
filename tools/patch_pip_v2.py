from pathlib import Path
import re

root = Path('/tmp/decoded')
manifest = root / 'AndroidManifest.xml'
s = manifest.read_text(encoding='utf-8')

# Find the real launcher activity.
activities = list(re.finditer(r'<activity\b[^>]*>', s))
activity_match = None
for m in activities:
    close = s.find('</activity>', m.end())
    if close == -1:
        continue
    body = s[m.start():close + len('</activity>')]
    if 'android.intent.action.MAIN' in body and 'android.intent.category.LAUNCHER' in body:
        activity_match = m
        break
if activity_match is None:
    raise SystemExit('Launcher activity not found')

tag = activity_match.group(0)
name_m = re.search(r'android:name="([^"]+)"', tag)
if not name_m:
    raise SystemExit('Launcher activity has no android:name')
activity_name = name_m.group(1)
package_m = re.search(r'package="([^"]+)"', s)
package = package_m.group(1) if package_m else ''
if activity_name.startswith('.'):
    fqcn = package + activity_name
elif '.' not in activity_name:
    fqcn = package + '.' + activity_name
else:
    fqcn = activity_name

# Keep v1 manifest capability enabled.
new = tag
if 'android:supportsPictureInPicture=' not in new:
    new = new[:-1] + ' android:supportsPictureInPicture="true">'
if 'android:resizeableActivity=' not in new:
    new = new[:-1] + ' android:resizeableActivity="true">'
s = s[:activity_match.start()] + new + s[activity_match.end():]
manifest.write_text(s, encoding='utf-8')

# Locate launcher activity smali across all dex directories.
rel = fqcn.replace('.', '/') + '.smali'
smali_file = None
for d in sorted(root.glob('smali*')):
    candidate = d / rel
    if candidate.exists():
        smali_file = candidate
        break
if smali_file is None:
    # Fallback by class declaration if obfuscation/path differs.
    descriptor = 'L' + fqcn.replace('.', '/') + ';'
    for d in sorted(root.glob('smali*')):
        for p in d.rglob('*.smali'):
            try:
                head = p.read_text(encoding='utf-8', errors='ignore')[:1200]
            except Exception:
                continue
            if descriptor in head and '.class' in head:
                smali_file = p
                break
        if smali_file:
            break
if smali_file is None:
    raise SystemExit(f'Launcher smali not found for {fqcn}')

sm = smali_file.read_text(encoding='utf-8')
if 'Infinity PiP v2 automatic entry' in sm:
    print('PiP v2 already present')
    raise SystemExit(0)

# Read the superclass so onUserLeaveHint can call through correctly.
super_m = re.search(r'^\.super\s+(L[^;]+;)', sm, re.M)
if not super_m:
    raise SystemExit('Launcher superclass not found')
super_desc = super_m.group(1)

# Do not double-define an existing callback; patch into it instead when present.
method_re = re.compile(r'(\.method\s+[^\n]*onUserLeaveHint\(\)V.*?\.end method)', re.S)
mm = method_re.search(sm)
call_block = f'''\n    # Infinity PiP v2 automatic entry\n    sget v0, Landroid/os/Build$VERSION;->SDK_INT:I\n    const/16 v1, 0x1a\n    if-lt v0, v1, :infinity_pip_done\n    invoke-virtual {{p0}}, Landroid/app/Activity;->enterPictureInPictureMode()Z\n    :infinity_pip_done\n'''

if mm:
    block = mm.group(1)
    # Ensure enough locals/registers. Convert .locals 0/1 to .locals 2 where possible.
    if re.search(r'\.locals\s+([01])\b', block):
        block = re.sub(r'\.locals\s+[01]\b', '.locals 2', block, count=1)
    elif '.locals' not in block and '.registers' in block:
        regm = re.search(r'\.registers\s+(\d+)', block)
        if regm and int(regm.group(1)) < 3:
            block = block.replace(regm.group(0), '.registers 3', 1)
    ret = block.rfind('    return-void')
    if ret == -1:
        raise SystemExit('Existing onUserLeaveHint has no return-void')
    block = block[:ret] + call_block + block[ret:]
    sm = sm[:mm.start()] + block + sm[mm.end():]
else:
    injected = f'''\n.method protected onUserLeaveHint()V\n    .locals 2\n\n    invoke-super {{p0}}, {super_desc}->onUserLeaveHint()V\n\n    # Infinity PiP v2 automatic entry\n    sget v0, Landroid/os/Build$VERSION;->SDK_INT:I\n    const/16 v1, 0x1a\n    if-lt v0, v1, :infinity_pip_done\n    invoke-virtual {{p0}}, Landroid/app/Activity;->enterPictureInPictureMode()Z\n\n    :infinity_pip_done\n    return-void\n.end method\n'''
    sm = sm.rstrip() + '\n' + injected

smali_file.write_text(sm, encoding='utf-8')
print(f'Infinity PiP v2 patched launcher {fqcn} at {smali_file}')
