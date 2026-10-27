"""Propose the tested Cobra-only component; retain every other owner exactly."""
import argparse,copy,subprocess
from pathlib import Path
from inventory import HERE,ROOT,load,save,file_sha,digest,canonical
from component_bundles import read_bundle
from release_authority import transition,verify_evidence

def propose(component,producer_run,source,version):
 path=HERE/'release-authority.json';previous=load(path);row=load(component/'catalog-row.json');meta=read_bundle(component/row['file'],row)
 assert row['approved_source']==source
 text=(component/'GEOMETRY-RESULTS.txt').read_text();assert 'Tests run: 6, Failures: 0, Errors: 0, Skipped: 0' in text
 preservation=load(component/'PRESERVATION.json');assert preservation['status']=='PASS_COBRA_DELTA_PRESERVATION' and preservation['player_retune_seek_audio_shutdown_methods_changed'] is False
 proposed=copy.deepcopy(previous);proposed.update(generation=previous['generation']+1,candidate_versionCode=version,
  update_kind='owner_update',target_owners=['COBRA'],previous_authority_sha256=digest(canonical(previous)),assembly_mode='selected_owner_bundles')
 proposed['payload']={k:v for k,v in previous['payload'].items() if v['owner']!='COBRA'};proposed['payload'].update(meta['payload'])
 proposed['components']['COBRA']={k:meta[k] for k in ['version','digest','settings_schema','approved_source']}
 proposed['components']['COBRA']['revision']=previous['components']['COBRA']['revision']+1
 proposed['bundle_catalog']['bundles']['COBRA']=row
 proposed['bundle_sources']={o:{'run_id':40447183241,'artifact':'Infinity-Combined-Owner-Components-40447183241','path':r['file'],
   'build_source':'b69d18637658be676605c61e5a8792ab5ca179cb'} for o,r in proposed['bundle_catalog']['bundles'].items()}
 proposed['bundle_sources']['COBRA']={'run_id':producer_run,'artifact':'Cobra-All-Layout-Reflow-Owner-'+str(producer_run),'path':'COBRA.zip','build_source':row['approved_source']}
 paths={ROOT/p for p in previous['source_files']}|set(HERE.glob('*.py'))
 proposed['source_files']={str(p.relative_to(ROOT)):file_sha(p) for p in sorted(paths)}
 proposed['owner_update_evidence']={'owner':'COBRA','producer_run':producer_run,'producer_source':row['approved_source'],
  'component_zip_sha256':row['sha256'],'geometry_tests':6,'failures':0,'errors':0,'physical_Fold':'PENDING',
  'test_inputs':load(component/'TEST-INPUTS.json'),'preservation':preservation,
  'installed_base_report':'User reported installing 421; accepted pointer is not advanced'}
 transition(previous,proposed,{'COBRA'});verify_evidence(proposed,lambda n:(ROOT/n).read_bytes());save(path,proposed)
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--component',type=Path,required=True);p.add_argument('--producer-run',type=int,required=True);p.add_argument('--source',required=True);p.add_argument('--version',type=int,required=True);propose(**vars(p.parse_args()))
