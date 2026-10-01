from pathlib import Path
import hashlib,json,xml.etree.ElementTree as E
allowed={'tools/android/packaging/xbmc/src/Main.java.in','tools/android/packaging/xbmc/build.gradle.in','cmake/scripts/android/Install.cmake'}
added={'tools/android/packaging/xbmc/src/InfinityKodiAmbientGate.java.in'}
old=Path('rollback281/shell-kodi');new=Path('shell-kodi')
before={str(p.relative_to(old)):p for p in old.rglob('*') if p.is_file()}
after={str(p.relative_to(new)):p for p in new.rglob('*') if p.is_file()}
assert after.keys()-before.keys()==added
assert not before.keys()-after.keys()
changed={n for n in before if before[n].read_bytes()!=after[n].read_bytes()};assert changed==allowed,changed
names=[p.name for p in Path('evidence281/screenshots/protected').glob('*.png')];assert len(names)==20
for name in names:assert Path('evidence281/screenshots/protected',name).read_bytes()==Path('audit282/screenshots/protected',name).read_bytes(),name
tests={}
for f in Path('build282/xbmc/build/test-results/testReleaseUnitTest').glob('TEST-*.xml'):
    t=E.parse(f).getroot();assert all(int(t.attrib.get(k,0))==0 for k in ['failures','errors','skipped']),(f,t.attrib);tests[t.attrib['name']]=int(t.attrib['tests'])
assert sum(tests.values())==524,tests
report={'parent_lock':'bf9e70d68f696fae156c9f33dedf1224c37d7137','parent_apk_sha256':'4c119343d623be5c15233e7b1ed7fa82e3d1f92c3a5ec56f7d3f85b0707cbfe5','parent_is_user_authorized_not_new_device_certification':True,'test_count':524,'test_methods':tests,'protected_renders_byte_identical':20,'other_source_files_unchanged':len(before)-len(changed),'changed_source_files':sorted(changed),'added_source_files':sorted(added),'source_hashes':{n:hashlib.sha256(p.read_bytes()).hexdigest() for n,p in after.items()},'physical_device_verified':False,'locked':False,'runtime_scope':'Cobra Java emulator preservation and update-over-install, not ARM Kodi ambient acceptance'}
Path('candidate282/AUDIT-VERIFICATION.json').write_text(json.dumps(report,indent=2))
print('PASS: exact Cobra source/render preservation and 524 Android tests; Fold acceptance pending')
