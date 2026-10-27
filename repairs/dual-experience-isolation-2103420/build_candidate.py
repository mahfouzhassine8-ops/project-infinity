"""Reproduce the scoped production modules from the immutable signed baseline.

Packaging validates existing source-bound behavioral evidence; it never runs
application/shutdown scenarios or changes the user's accepted pointer.
"""
import argparse,shutil,subprocess,json
from pathlib import Path
from inventory import HERE,APK_SHA,load,save,file_sha,disassemble
from prepare_runtime import prepare
from compile_runtime import compile_runtime
from build_modules import build
from verify_runtime import check
from review_ownership import review
from component_bundles import pack,combine,read_bundle
from release_gate import require
from release_authority import verify

def candidate(baseline,jars,android,d8,out):
    require(file_sha(baseline)==APK_SHA,'EXACT_BASELINE');out.mkdir()
    authority=load(HERE/'release-authority.json')
    if authority.get('assembly_mode')=='selected_owner_bundles':
        # Future independent updates select immutable CI artifacts per owner.
        # Never take the opposite component from the developer's old APK.
        bundles=out/'components';bundles.mkdir()
        catalog=authority['bundle_catalog']
        for owner,row in catalog['bundles'].items():
            location=authority['bundle_sources'][owner];download=out/('download-'+owner)
            run=json.loads(subprocess.check_output(['gh','api','repos/mahfouzhassine8-ops/project-infinity/actions/runs/'+str(location['run_id'])],text=True))
            require(run['conclusion']=='success' and run['head_sha']==row['approved_source'],'COMPONENT_BUILD_SOURCE')
            subprocess.run(['gh','run','download',str(location['run_id']),
                '--repo','mahfouzhassine8-ops/project-infinity','--name',location['artifact'],
                '--dir',str(download)],check=True)
            source=download/location['path']
            require(source.resolve().is_relative_to(download.resolve()),'BUNDLE_SOURCE_PATH')
            read_bundle(source,row);shutil.copyfile(source,bundles/row['file'])
        save(bundles/'catalog.json',catalog)
        result=combine(bundles,catalog,out/'combined-unsigned.apk',authority['candidate_versionCode'])
        verify(authority,{k:v['sha256'] for k,v in result['payload'].items()},result['versionCode'],authority['generation'])
        save(out/'ASSEMBLY.json',result)
        return out/'combined-unsigned.apk'
    require(authority.get('assembly_mode')=='scoped_baseline_rebuild','UNKNOWN_ASSEMBLY_MODE')
    original=out/'original';disassemble(baseline,jars,original)
    work=out/'runtime';prepare(original,work);compile_runtime(work,jars,android,d8)
    build(work,jars,original)
    check(work,original,out/'RUNTIME-PRESERVATION.json')
    ownership=out/'ownership';review(work,baseline,ownership)
    sources={r['approved_source'] for r in authority['components'].values()}
    require(len(sources)==1,'INDEPENDENT_UPDATES_REQUIRE_SELECTED_BUNDLE_CATALOG')
    bundles=out/'components';catalog=pack(baseline,work,ownership,bundles,sources.pop())
    apk=out/'combined-unsigned.apk'
    result=combine(bundles,catalog,apk,authority['candidate_versionCode'])
    verify(authority,{k:v['sha256'] for k,v in result['payload'].items()},result['versionCode'],authority['generation'])
    save(out/'ASSEMBLY.json',result)
    for owner,row in catalog['bundles'].items():
        meta=read_bundle(bundles/row['file'],row)
        save(bundles/(owner+'.json'),meta)
    return apk

if __name__=='__main__':
    p=argparse.ArgumentParser()
    for n in ('baseline','jars','android','d8','out'):p.add_argument('--'+n,type=Path,required=True)
    candidate(**vars(p.parse_args()))
