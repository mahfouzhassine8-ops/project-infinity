from pathlib import Path
import sys,json,shutil
ambient_here=Path(__file__).parent
mode=sys.argv[1]
if mode in ('runtime','unit'):
    filename='stage_runtime.py' if mode=='runtime' else 'stage_tests.py'
    source=Path('repairs/remaining-repair-2103281',filename).read_text().replace('build281','build282').replace('audit281','audit282')
    exec(compile(source,filename,'exec'))
    if mode=='unit':
        shutil.copy2(ambient_here/'InfinityAmbientGateTest.java','build282/xbmc/src/test/java/com/projectinfinity/kodi/InfinityAmbientGateTest.java')
        p=Path('audit282/test-classes.json');names=json.loads(p.read_text());names.append('com.projectinfinity.kodi.InfinityAmbientGateTest');p.write_text(json.dumps(names,indent=2))
elif mode=='runner':
    text=Path('repairs/remaining-repair-2103281/runtime.sh').read_text()
    text=text.replace('locked280/Infinity-2103280-Audit-Followup-RC1.apk','locked281/Infinity-2103281-Remaining-Audit-RC1.apk')
    text=text.replace('candidate281/Infinity-2103281-Remaining-Audit-RC1.apk','candidate282/Infinity-2103282-Infinity-Native-Ambient-RC1.apk')
    text=text.replace('Cobra-audit-followup-tests.apk','Cobra-preservation-tests.apk');Path('runtime282.sh').write_text(text)
else:raise SystemExit('unknown stage')
