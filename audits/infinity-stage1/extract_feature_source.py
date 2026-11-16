#!/usr/bin/env python3
"""Read-only export of APK-embedded plain text program code, UI XML and metadata."""
import json, sys, zipfile
from pathlib import Path
apk,out=Path(sys.argv[1]),Path(sys.argv[2])
out.mkdir(parents=True,exist_ok=True)
prefixes=(
"assets/addons/skin.infinity.diggz/",
"assets/addons/script.infinity.",
"assets/addons/script.kodihealthcenter/",
"assets/addons/service.infinity.",
"assets/addons/plugin.infinity.",
"assets/addons/script.skinshortcuts/",
"assets/system/settings/",
)
allowed={'.xml','.py','.json','.po','.txt','.md','.properties','.cfg','.ini','.yaml','.yml'}
selected=[]
with zipfile.ZipFile(apk) as z:
    for item in z.infolist():
        name=item.filename
        if item.is_dir() or not name.startswith(prefixes) or item.file_size>1_500_000: continue
        p=Path(name)
        if p.suffix.lower() not in allowed: continue
        if '/language/' in name and not any(x in name for x in ('en_us','en_gb','en-US','en_GB')): continue
        if '/resources/language/' in name and not any(x in name for x in ('en_us','en_gb','en-US','en_GB')):continue
        target=out/name
        target.parent.mkdir(parents=True,exist_ok=True)
        target.write_bytes(z.read(item))
        selected.append({'path':name,'bytes':item.file_size,'crc32':format(item.CRC,'08x')})
    # DEX and manifest names are independently inventoried; code bytes are not decompiled.
(out/'EXTRACT-INDEX.json').write_text(json.dumps(selected,indent=2))
(out/'READ-ME.txt').write_text(
    'Static QA APK sources for Infinity Stage 1 only. Do not treat as live Fold evidence. '
    'Code/text from publicly published signed APK; no app data or device information. '
    'No code was executed. Extracted files MUST NOT be used to patch a release without authorization.\n'
)
print('SELECTED_FEATURE_SOURCE_FILES',len(selected),'BYTES',sum(x['bytes'] for x in selected))
