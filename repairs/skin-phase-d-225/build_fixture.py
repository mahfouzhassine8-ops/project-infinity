from pathlib import Path
import argparse,zipfile,json,hashlib
p=argparse.ArgumentParser();p.add_argument('--before',type=Path,required=True);p.add_argument('--after',type=Path,required=True);a=p.parse_args();out=Path(__file__).parent/'fixtures';out.mkdir(exist_ok=True)
receipt={}
with zipfile.ZipFile(out/'production-skin-renderer.zip','w',zipfile.ZIP_DEFLATED,compresslevel=9) as z:
 for section in ['unified','media','fonts','colors','resources','language']:
  for f in sorted((a.before/section).rglob('*')):
   if not f.is_file() or f.name.startswith('.'):continue
   # Retain packed textures; historical temporary XBT is not used by Kodi's renderer.
   n=str(f.relative_to(a.before));data=f.read_bytes();z.writestr('before/'+n,data);receipt['before/'+n]=hashlib.sha256(data).hexdigest()
 for n in ['addon.xml']:
  data=(a.before/n).read_bytes();z.writestr('before/'+n,data);receipt['before/'+n]=hashlib.sha256(data).hexdigest()
 for f in sorted(a.after.rglob('*')):
  if not f.is_file():continue
  n=str(f.relative_to(a.after))
  if ('before/'+n) in receipt and f.read_bytes()!=(a.before/n).read_bytes():
   data=f.read_bytes();z.writestr('after-overlay/'+n,data);receipt['after-overlay/'+n]=hashlib.sha256(data).hexdigest()
 z.writestr('SOURCE-IDENTITY.json',json.dumps(receipt,indent=2))
print(out/'production-skin-renderer.zip',(out/'production-skin-renderer.zip').stat().st_size)
