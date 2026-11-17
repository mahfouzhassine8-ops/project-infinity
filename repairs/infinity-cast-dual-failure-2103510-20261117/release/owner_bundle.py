"""Reconcile only the exact reviewed Cast delta in the INFINITY owner archive.

The staged APK DEX is never rebuilt here. Every resulting owner definition is
reparsed and required to match that APK. Protected owner archives are not inputs
to this mutator; the caller copies them byte-for-byte.
"""
from pathlib import Path
from zipfile import ZipFile
import hashlib,json,shutil,subprocess
def digest(b):return hashlib.sha256(b).hexdigest()
def classes(root):
 result={}
 for p in Path(root).rglob('*.smali'):
  b=p.read_bytes();name=b.decode().splitlines()[0].split()[-1];assert name not in result and name.startswith('L') and name.endswith(';');result[name]=(p,digest(b))
 return result
def disassemble(raw,jars,work):
 work.mkdir();dex=work/'input.dex';dex.write_bytes(raw);folder=work/'smali';subprocess.run(['java','-cp',str(Path(jars)/'*'),'org.jf.baksmali.Main','disassemble','--sequential-labels',str(dex),'-o',str(folder)],check=True);return folder,classes(folder)
def rewrite(source,dest,apk,owner,payload,baseline_payload,actual_smali,delta,jars,work,version,source_commit,inventory,bundles,copy_entry):
 assert owner in ('INFINITY','CHOOSER_SHELL');work.mkdir(parents=True,exist_ok=False)
 changed=set(delta['changed']);added=set(delta['added']);removed=set(delta['removed']);all_delta=changed|added|removed
 expected={name[6:]:row['sha256'] for name,row in payload.items() if row['owner']==owner and name.startswith('class:')}
 # Delta names are raw DEX descriptors, while authority keys are class:<name>.
 for name in changed|removed:assert baseline_payload['class:'+name]['owner']=='INFINITY'
 for name in changed|added:assert payload['class:'+name]['owner']=='INFINITY' and actual_smali[name][1]==payload['class:'+name]['sha256']
 with ZipFile(source) as old,ZipFile(apk) as app:
  meta=json.loads(old.read('component.json'));assert meta['owner']==owner;patches={}
  cast_raw=None;cast_definitions={}
  if owner=='INFINITY' and all_delta:
   cast_raw=app.read('classes6.dex');_,cast_definitions=disassemble(cast_raw,jars,work/'actual-cast-dex')
  for name,row in meta['members'].items():
   with app.open(name) as f:h=hashlib.file_digest(f,'sha256').hexdigest()
   if h!=row['sha256']:
    assert name in ('AndroidManifest.xml','assets/experience-component-updates.properties','lib/arm64-v8a/libinfinitycastremux.so'),('Unapproved owner member',name);patches['payload/'+name]=app.read(name);row['sha256']=h
  found=set();inserted=False;verified_union={}
  for index,name in enumerate(meta['dex']):
   raw=old.read(name);folder,before=disassemble(raw,jars,work/('slot-'+str(index)))
   for descriptor,(_,h) in before.items():assert baseline_payload['class:'+descriptor]=={'owner':owner,'sha256':h},('Original owner DEX is stale',descriptor)
   affected=set(before)&(changed|removed)
   if owner=='INFINITY' and affected:
    found|=affected
    if set(before)==(set(cast_definitions)-added)|removed:
     # Exact existing Cast slot: copy the already verified production DEX.
     # No assembler/optimizer runs on either the APK or this owner slot.
     raw=cast_raw;after=cast_definitions;inserted=True
    else:
     for descriptor in affected:
      path=before[descriptor][0]
      if descriptor in removed:path.unlink()
      else:shutil.copyfile(actual_smali[descriptor][0],path)
     if not inserted:
      for descriptor in added:
       path=folder/(descriptor[1:-1]+'.smali');path.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(actual_smali[descriptor][0],path)
      inserted=True
     output=work/('updated-'+str(index)+'.dex');subprocess.run(['java','-cp',str(Path(jars)/'*'),'org.jf.smali.Main','assemble',str(folder),'-o',str(output)],check=True);raw=output.read_bytes();_,after=disassemble(raw,jars,work/('verified-'+str(index)))
    patches[name]=raw;meta['dex'][name]=digest(raw)
   else:after=before
   for descriptor,(_,h) in after.items():assert descriptor not in verified_union;verified_union[descriptor]=h
  if owner=='INFINITY' and all_delta:assert found==changed|removed and (not added or inserted),'Exact Cast owner DEX delta required'
  assert verified_union==expected,'Whole owner DEX union must equal actual staged APK'
  meta['payload']={n:r for n,r in payload.items() if r['owner']==owner};meta.update(version=str(version)+'.'+owner.lower()+'.cast510dual.1',approved_source=source_commit);meta['digest']=bundles.component_digest(meta['payload'],owner)
  with ZipFile(dest,'w',allowZip64=True) as out:
   for name in old.namelist():copy_entry(old,out,name,inventory.canonical(meta) if name=='component.json' else patches.get(name))
 return meta
