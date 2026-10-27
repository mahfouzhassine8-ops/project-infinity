"""Create one immutable Cobra input; preserve all non-code Cobra members."""
import argparse,copy,json,re,sys
from pathlib import Path
from zipfile import ZipFile
HERE=Path(__file__).resolve().parent;ISO=HERE.parent/'dual-experience-isolation-2103420';sys.path.insert(0,str(ISO))
from inventory import load,save,file_sha,digest,canonical,APP
from component_bundles import read_bundle,record
from release_gate import component_digest,require
from build import VERSION

def package(work,bundles,out,source):
 out.mkdir();catalog=load(bundles/'catalog.json');row=catalog['bundles']['COBRA'];old=read_bundle(bundles/row['file'],row);meta=copy.deepcopy(old)
 classes={}
 for p in (work/'owner-dex/COBRA').glob('part-*/**/*.smali'):
  n=p.read_text().splitlines()[0].split()[-1];classes['class:'+n]={'owner':'COBRA','sha256':file_sha(p)}
 require(len(classes)>7000,'COMPLETE_COBRA_REQUIRED')
 original={k:v for k,v in old['payload'].items() if k.startswith('class:')}
 changed=[k for k in original if classes.get(k)!=original[k]]
 require(set(changed)=={'class:'+APP+'InfinityLiveActivity;','class:'+APP+'CobraComponent;'},'UNRELATED_CLASS_CHANGED')
 for k in set(classes)-set(original):require(k.startswith('class:'+APP+'CobraWindowReflow'),'UNOWNED_NEW_CLASS')
 meta['payload']={k:v for k,v in old['payload'].items() if not k.startswith('class:')};meta['payload'].update(classes)
 meta.update(version=VERSION,approved_source=source,dex={})
 target=out/'COBRA.zip'
 with ZipFile(bundles/row['file']) as original_zip,ZipFile(target,'w') as z:
  for n in meta['members']:z.writestr(record('payload/'+n),original_zip.read('payload/'+n))
  for p in sorted((work/'owner-dex/COBRA').glob('*.dex')):
   name='dex/'+p.name;meta['dex'][name]=file_sha(p);z.writestr(record(name),p.read_bytes())
  meta['digest']=component_digest(meta['payload'],'COBRA');z.writestr(record('component.json'),canonical(meta))
 result={k:meta[k] for k in ['version','digest','approved_source','settings_schema']};result.update(file='COBRA.zip',sha256=file_sha(target))
 read_bundle(target,result);save(out/'catalog-row.json',result);save(out/'component.json',meta)

if __name__=='__main__':
 p=argparse.ArgumentParser()
 for n in ['work','bundles','out']:p.add_argument('--'+n,type=Path,required=True)
 p.add_argument('--source',required=True);package(**vars(p.parse_args()))
