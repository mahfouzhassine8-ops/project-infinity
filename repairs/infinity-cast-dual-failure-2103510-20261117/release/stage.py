"""Exact signed510-derived Cast-only pair. Key-free; no registry write or rebuild."""
from pathlib import Path
from zipfile import ZipFile
import copy,hashlib,json,os,subprocess,sys,types
HERE=Path(__file__).resolve().parent;TASK=HERE.parent;ROOT=HERE.parents[2]
BASE='8fd4d06d4a93b29764d4820bd6000795562411802fb52a402e1b3b2ddaa93ab0'
LIB='lib/arm64-v8a/libinfinitycastremux.so';DEX='classes6.dex';LABEL='assets/experience-component-updates.properties'
def sha(p):
 with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def canonical(v):return json.dumps(v,sort_keys=True,separators=(',',':')).encode()
def main():
 assert os.environ['GITHUB_ACTIONS']=='true' and os.environ['GITHUB_REPOSITORY']=='mahfouzhassine8-ops/project-infinity' and os.environ['GITHUB_REF']=='refs/heads/work/infinity-2103510-cast-dual-failure-20261117'
 r=json.loads((HERE/'STAGE-REQUEST.json').read_bytes());assert r['baseline_versionCode']==2103510 and r['signing'] is False and r['registry_write'] is False
 assert set(r['versions'])=={'candidate','recovery'} and r['versions']['recovery']>r['versions']['candidate']>2103511
 required={str((HERE/'stage.py').relative_to(ROOT)),str((TASK/'SCOPE.json').relative_to(ROOT)),str((TASK/'component_contract.py').relative_to(ROOT)),str((TASK/'verify_android_media.py').relative_to(ROOT)),'repairs/infinity-cast-hardware-pipeline-2103506-20261117/native/CastVideoAdapter.h',str((TASK/'CAST-CLASS-DELTA.json').relative_to(ROOT)),'repairs/infinity-six-repairs-2103502-20261116/cast/native/InfinityCastRemux.cpp','repairs/infinity-cast-end-to-end-2103504-20261116/native/CastAudioAdapter.h','.github/workflows/infinity-506-cast-hardware-stage.yml'}
 assert set(r['inputs'])==required,'EXACT_STAGE_SOURCE_BINDINGS'
 for n,h in r['inputs'].items():assert sha(ROOT/n)==h,n
 scope_note=json.loads((TASK/'SCOPE.json').read_bytes());assert scope_note['foundation_APK_sha256']==BASE and scope_note['engine_build'] is False and scope_note['shutdown'] is False
 names=subprocess.check_output(['git','diff','--name-only','c39a7612c612e29a54e70fe0b3116049bef00e5d',r['source_commit']],text=True).splitlines();allowed=set(scope_note['allowed_source'])|set(scope_note['orchestration_allowed'])
 assert all(n in allowed or n.startswith(str(TASK.relative_to(ROOT))+'/') for n in names),'OUT_OF_SCOPE_SOURCE_CHANGED'
 for n,h in scope_note['allowed_source'].items():assert hashlib.sha256(subprocess.check_output(['git','show',scope_note['foundation_signing_source']+':'+n])).hexdigest()==h,n
 assert subprocess.check_output(['git','diff','--name-only',r['source_commit'],os.environ['GITHUB_SHA']],text=True).splitlines()==[str((HERE/'STAGE-REQUEST.json').relative_to(ROOT))]
 review_raw=(HERE/'STAGE-REVIEW.json').read_bytes();assert hashlib.sha256(review_raw).hexdigest()==r['review_sha256'];review=json.loads(review_raw)
 fixed={k:r[k] for k in ('baseline','Android','component','versions','inputs','parent_authority_sha256','class_delta_sha256','known_limitations')};assert review['reviewer']=='Astra' and review['status']=='PASS_CAST510_DUAL_STAGE' and review['request_sha256']==hashlib.sha256(canonical(fixed)).hexdigest()
 helper='repairs/infinity-movies-continue-cast-2103486-20261112/release/common_release.py';raw=subprocess.check_output(['git','show','21616dfa94bf7ca9ec52e40119edf95df5e64073:'+helper]);scope={'__file__':str(ROOT/helper),'__name__':'_original_stage_reader'};exec(compile(raw,str(ROOT/helper),'exec'),scope);c=types.SimpleNamespace(**scope)
 remote=subprocess.check_output(['git','ls-remote','origin','refs/heads/'+c.CANONICAL],text=True).split()[0];subprocess.run(['git','fetch','--no-tags','origin',remote],check=True);live=subprocess.check_output(['git','show',remote+':'+c.AUTHORITY]);assert hashlib.sha256(live).hexdigest()==r['parent_authority_sha256'],'LIVE_REGISTRY_CHANGED'
 registry=json.loads(live);assert r['versions']['candidate']>max(registry['candidate_versionCode'],registry['last_issued_versionCode'])
 base=c.unique(c.obtain(r['baseline'],'cast510-dual-stage-base'),'Infinity-2103510-Combined-Original-Signer.apk');assert sha(base)==BASE;c.signature(base)
 verified=c.obtain(r['Android'],'cast510-dual-stage-Android');gate=json.loads(c.unique(verified,'RESULT.json').read_bytes());assert gate['pass'] is True and gate['status']=='PASS_ACTUAL_ARM64_DUAL_CAST_CORRECTIONS'
 assert gate['SDK_error_fields']['null_vs_zero'] is True and gate['SDK_error_fields']['safe_reason'] is True and gate['SDK_error_fields']['real_SDK_object'] is True
 direct=gate['direct_HEVC'];assert direct['fragment5_complete'] is True and direct['AAC'] is True and direct['Main10_level']==153
 if direct['HLS']['actual_Android_HLS_playback'] is not True:
  assert direct['HLS']['actual_Android_HLS_playback'] is False
  inventory=direct['codec_inventory'];assert direct['HLS']['status']=='NOT_SUPPORTED_BY_ACTUAL_CI_CODEC_INVENTORY' and inventory['supported_decoders']==0 and inventory['decoders'] and all(v['format_supported'] is False for v in inventory['decoders'])
  assert r['known_limitations']['Main10_Android_decode']=='UNVERIFIED_HARDWARE; CIcodec_inventoryunsupported_is_notPASS'
 assert gate['hardware_input_fixture']=='genuine_HEVC_Main8_L3_RADL_inband; not_Main10_hardware_qualification'
 assert gate['production_R8_Relay'] is True and gate['provider_auth'] is True and gate['whole_fragment_HTTP'] is True and gate['failure_cleanup'] is True and gate['owned_native_after_close']==0 and 0<=gate['cancellation_ms']<=10000
 hls=gate['HLS'];assert hls['actual_Android_HLS_playback'] is True and hls['video_rendered_frames']>hls['video_rendered_frames_before_seek'] and hls['audio_rendered_buffers']>hls['audio_rendered_buffers_before_seek'] and abs(hls['seek_mapped_ms']-2500)<200 and hls['seek_position_ms']>=2650
 proof=json.loads(c.unique(verified,'ARM64.json').read_bytes());library=c.unique(verified,'libinfinitycastremux.so');assert proof['status']=='PASS_CAST510_DUAL_ARM64_LINK' and sha(library)==proof['new_library_sha256'] and proof['existing_engine_sha256']=='b3d8d96aa55bf0e48f6cf7c995b2c2ebf9c53720b94f2a9e791dd039d64bf1e7'
 for n in ('repairs/infinity-six-repairs-2103502-20261116/cast/native/InfinityCastRemux.cpp','repairs/infinity-cast-hardware-pipeline-2103506-20261117/native/CastVideoAdapter.h','repairs/infinity-cast-end-to-end-2103504-20261116/native/CastAudioAdapter.h'):assert sha(ROOT/n)==proof['source_hashes'][n],n
 compiled=c.obtain(r['component'],'cast510-dual-stage-component');component=json.loads(c.unique(compiled,'COMPONENT-RESULT.json').read_bytes());assert component['status']=='PASS_COMPONENT_COMPILE_AND_EXISTING_API_LINK_CONTRACT' and component['baseline_APK_sha256']==BASE
 cast=ROOT/'repairs/infinity-movies-continue-cast-2103486-20261112/cast'
 for n,h in component['feature_Java_sha256'].items():assert sha(cast/n)==h,n
 dex=c.unique(compiled,'classes.dex');assert sha(dex)==component['dex']['classes.dex']
 builds=[json.loads(p.read_bytes()) for p in verified.rglob('BUILD.json')];assert builds and all(v==builds[0] for v in builds);assert builds[0]['production_Cast_DEX_sha256']==sha(dex) and builds[0]['new_Cast_library_sha256']==sha(library)
 assert builds[0]['source']==r['Android']['source'] and builds[0]['foundation']==r['baseline'] and builds[0]['native']['libkodi.so']=='b3d8d96aa55bf0e48f6cf7c995b2c2ebf9c53720b94f2a9e791dd039d64bf1e7'
 assert sha(TASK/'CAST-CLASS-DELTA.json')==r['class_delta_sha256'];delta=json.loads((TASK/'CAST-CLASS-DELTA.json').read_bytes());assert delta['candidate_member_sha256']==sha(dex)
 inventory,bundles,_,_,_=c.tools();out=ROOT/'cast510-dual-stage';out.mkdir();sys.path.insert(0,str(TASK));from component_contract import verify
 (out/'EXTERNAL-API.json').write_text(json.dumps(verify(base,dex.parent),indent=2)+'\n')
 # Revalidate actual media, including AAC packet bytes/timestamps against the
 # original-video/AAC reference. The selected verifier writes only its receipt
 # and temporary decoded inspection files, never user/profile data.
 subprocess.run(['python',str(TASK/'verify_android_media.py'),str(verified),str(out/'MEDIA.json')],check=True)
 reports={}
 with ZipFile(base) as before:
  names=set(inventory.validate_names(before))-set(inventory.SIGNATURE)
  assert json.loads(before.read('assets/infinity/cast/RESOURCE-IDENTITY.json'))['sha256']==component['resources']['sha256']
  for kind,version in r['versions'].items():
   changes={'AndroidManifest.xml':bundles.set_version(before.read('AndroidManifest.xml'),version),LABEL:('infinity.last_updated_in='+str(version)+'\ncobra.last_updated_in=2103445\n').encode()}
   if kind=='candidate':changes.update({LIB:library.read_bytes(),DEX:dex.read_bytes()})
   apk=out/('Infinity-'+str(version)+'-UNSIGNED-NOT-INSTALLABLE.apk')
   with ZipFile(apk,'w',allowZip64=True) as after:
    for info in before.infolist():
     if info.filename in names:after.writestr(copy.copy(info),changes.get(info.filename,before.read(info.filename)))
   vector={}
   with ZipFile(apk) as after:
    assert set(inventory.validate_names(after))==names
    for name in names:
     def digest(z):
      with z.open(name) as f:return hashlib.file_digest(f,'sha256').hexdigest()
     a,b=digest(before),digest(after)
     if a!=b:vector[name]={'before':a,'after':b}
   assert set(vector)==set(changes),('EXACT_CAST510_MEMBER_DIFF',kind,set(vector))
   reports[kind]={'APK_sha256':sha(apk),'versionCode':version,'changes':vector,'unchanged_members':len(names)-len(vector)}
 (out/'STAGING.json').write_text(json.dumps({'status':'PASS_UNSIGNED_CAST510_DUAL_STAGE','source':os.environ['GITHUB_SHA'],'baseline_APK_sha256':BASE,'versions':r['versions'],'payloads':reports,'Android_artifact':r['Android'],'component_artifact':r['component'],'Cobra':'BYTE_UNCHANGED','Kodi_other_DEX_modules_resources':'BYTE_UNCHANGED','owner_data':'NOT_ACCESSED','signed':False,'physical_hardware_TV':'PENDING_OWNER'},indent=2)+'\n')
if __name__=='__main__':main()
