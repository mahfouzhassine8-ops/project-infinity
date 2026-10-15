from pathlib import Path
import argparse,importlib.util,json,hashlib
spec=importlib.util.spec_from_file_location('responsive269',Path(__file__).parent/'apply.py');r=importlib.util.module_from_spec(spec);spec.loader.exec_module(r)
p=argparse.ArgumentParser();p.add_argument('--root',type=Path,required=True);p.add_argument('--baseline',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args()
b=(a.baseline/'shell-kodi'/r.ACTIVITY).read_text();s=(a.root/'shell-kodi'/r.ACTIVITY).read_text();assert s.count(r.HELPERS)==1;s=s.replace(r.HELPERS,'')
for name in r.ALLOWED:
 x,y=r.span(b,name);s=r.member(s,name,b[x:y])
assert s==b,'Changes outside responsive presentation members'
items=[];changed=[]
for f in sorted((a.baseline/'shell-kodi').rglob('*')):
 if not f.is_file():continue
 n=str(f.relative_to(a.baseline/'shell-kodi'));g=a.root/'shell-kodi'/n;assert g.is_file();old=r.sha(f.read_bytes());new=r.sha(g.read_bytes());items.append(dict(path=n,before=old,after=new))
 if old!=new:changed.append(n)
assert set(changed)=={r.ACTIVITY,r.CHOOSER,'tools/android/packaging/xbmc/build.gradle.in'},changed
assert (a.root/'shell-kodi'/r.CHOOSER).read_bytes()==(Path(__file__).parent/'InfinityGlassChooser.java.in').read_bytes()
a.out.mkdir(parents=True,exist_ok=True);(a.out/'source-verification.json').write_text(json.dumps(dict(changed_shell_files=changed,activity_members=r.ALLOWED,protected_source_preserved=True,infinity_skin_touched=False,physical_device_verified=False,locked=False,files=items),indent=2)+'\n');print('PASS: exact 268 checkpoint, protected native/provider/player/Pro source unchanged')
