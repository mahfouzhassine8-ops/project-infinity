from pathlib import Path
import re

ROOT=Path('/tmp/decoded')
report=[]

def add(s=''):
    report.append(s)

add('STABLE 2 ANDROID-SIDE FORENSIC REPORT')
add('====================================')

manifest=(ROOT/'AndroidManifest.xml').read_text(errors='ignore')
add('\n[Manifest Main activity]')
for m in re.finditer(r'<activity\b[^>]*>', manifest, re.S):
    tag=m.group(0)
    if 'projectinfinity' in tag or 'xbmc' in tag or 'Main' in tag:
        add(tag.replace('\n',' '))

patterns=[
    'supportsPictureInPicture','resizeableActivity','configChanges','launchMode',
    'autoEnterEnabled','setAutoEnterEnabled','PictureInPictureParams',
    'enterPictureInPictureMode','onUserLeaveHint','onPictureInPictureModeChanged',
    'onMultiWindowModeChanged','onConfigurationChanged','setPictureInPictureParams',
    'setFixedSize','setSizeFromLayout','requestLayout','surfaceChanged','SurfaceHolder'
]

all_smali=[]
for d in ROOT.glob('smali*'):
    all_smali.extend(d.rglob('*.smali'))

add('\n[PiP / lifecycle / surface matches]')
for p in all_smali:
    try: txt=p.read_text(errors='ignore')
    except: continue
    hits=[x for x in patterns if x in txt]
    if hits:
        add(f'FILE: {p.relative_to(ROOT)}')
        add('HITS: '+', '.join(hits))
        # Include methods containing key hits.
        for mm in re.finditer(r'(?ms)^\.method[^\n]*\n.*?^\.end method', txt):
            body=mm.group(0)
            if any(x in body for x in patterns):
                add(body[:5000])
                add('---')

add('\n[Likely custom helper classes]')
for p in all_smali:
    n=p.name.lower()
    if any(k in n for k in ['pip','phone','bridge','infinity','fold','surface','window']):
        add(str(p.relative_to(ROOT)))

# Detect exact Main class and dump relevant method names.
add('\n[Main class candidates]')
for p in all_smali:
    if p.name=='Main.smali' and ('projectinfinity' in str(p).lower() or 'xbmc' in str(p).lower()):
        add(str(p.relative_to(ROOT)))
        txt=p.read_text(errors='ignore')
        for name in ['onCreate','onResume','onPause','onStop','onUserLeaveHint','onPictureInPictureModeChanged','onMultiWindowModeChanged','onConfigurationChanged']:
            for mm in re.finditer(rf'(?ms)^\.method[^\n]* {re.escape(name)}\([^\n]*\n.*?^\.end method', txt):
                add(mm.group(0))
                add('---')

out='\n'.join(report)
Path('/tmp/stable2-report.txt').write_text(out)
print(out)
