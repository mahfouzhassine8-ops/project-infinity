"""Stage a native-only504-derived pair after the exact Android gate passes.
No key access, application launch, registry write, module/DEX or Kodi build.
"""
from pathlib import Path
from zipfile import ZipFile
import copy,hashlib,json,os,subprocess,types
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[2]
BASE='ab9104471c729751d6127cc4dfc6e98d8bb4c916212c356ce9c0295b2a0c5234'
LIB='lib/arm64-v8a/libinfinitycastremux.so'
LABEL='assets/experience-component-updates.properties'
BRANCH='work/infinity-2103504-cast-end-to-end-20261116'
def sha(p):
 with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def canonical(v):return json.dumps(v,sort_keys=True,separators=(',',':')).encode()
def main():
 assert os.environ['GITHUB_ACTIONS']=='true' and os.environ['GITHUB_REPOSITORY']=='mahfouzhassine8-ops/project-infinity'
 assert os.environ['GITHUB_REF']=='refs/heads/'+BRANCH
 r=json.loads((HERE/'STAGE-REQUEST.json').read_bytes())
 assert r['baseline_versionCode']==2103504 and r['signing'] is False and r['registry_write'] is False
 assert set(r['versions'])=={'candidate','recovery'}
 assert r['versions']['recovery']>r['versions']['candidate']>2103505
 for name,wanted in r['inputs'].items():assert sha(ROOT/name)==wanted,name
 changed=subprocess.check_output(['git','diff','--name-only',r['source_commit'],os.environ['GITHUB_SHA']],text=True).splitlines()
 assert changed==[str((HERE/'STAGE-REQUEST.json').relative_to(ROOT))]
 review_raw=(HERE/'STAGE-REVIEW.json').read_bytes();assert hashlib.sha256(review_raw).hexdigest()==r['review_sha256']
 review=json.loads(review_raw);assert review['reviewer']=='Astra' and review['status']=='PASS_NATIVE_ONLY504_STAGE'
 fixed={k:r[k] for k in ('baseline','native','Android','versions','inputs','parent_authority_sha256')}
 assert hashlib.sha256(canonical(fixed)).hexdigest()==review['request_sha256']
 helper='repairs/infinity-movies-continue-cast-2103486-20261112/release/common_release.py'
 raw=subprocess.check_output(['git','show','21616dfa94bf7ca9ec52e40119edf95df5e64073:'+helper])
 scope={'__file__':str(ROOT/helper),'__name__':'_pinned_artifact_reader'};exec(compile(raw,str(ROOT/helper),'exec'),scope);c=types.SimpleNamespace(**scope)
 # The allocator is live canonical metadata, never its recovery APK contents.
 authority='repairs/dual-experience-isolation-2103420/release-authority.json'
 remote=subprocess.check_output(['git','ls-remote','origin','refs/heads/'+c.CANONICAL],text=True).split()[0]
 subprocess.run(['git','fetch','--no-tags','origin',remote],check=True)
 live=subprocess.check_output(['git','show',remote+':'+authority]);assert hashlib.sha256(live).hexdigest()==r['parent_authority_sha256'],'LIVE_REGISTRY_CHANGED'
 live_json=json.loads(live);assert r['versions']['candidate']>max(live_json['candidate_versionCode'],live_json['last_issued_versionCode'])
 base=c.unique(c.obtain(r['baseline'],'cast504-stage-base'),'Infinity-2103504-Combined-Original-Signer.apk');assert sha(base)==BASE;c.signature(base)
 native=c.obtain(r['native'],'cast504-stage-native');proof=json.loads(c.unique(native,'CAST-AUDIO-ARM64.json').read_bytes());library=c.unique(native,'libinfinitycastremux.so')
 assert proof['status']=='PASS_CAST_AUDIO_ARM64_LINK_AND_EXACT504_ABI' and sha(library)==proof['new_library_sha256']
 for name in ('repairs/infinity-six-repairs-2103502-20261116/cast/native/InfinityCastRemux.cpp',str((HERE.parent/'native/CastAudioAdapter.h').relative_to(ROOT))):assert sha(ROOT/name)==proof['reviewed_inputs'][name]
 android=c.obtain(r['Android'],'cast504-stage-Android');gate=json.loads(c.unique(android,'ANDROID-CAST-AUDIO.json').read_bytes())
 assert gate['pass'] is True and gate['status']=='PASS_ACTUAL_ARM64_ANDROID_AAC_JNI_RELAY'
 builds=list(android.rglob('BUILD.json'));assert builds and all(p.read_bytes()==builds[0].read_bytes() for p in builds)
 build=json.loads(builds[0].read_bytes());assert build['native_library_sha256']==sha(library) and build['native_artifact']==r['native']
 assert gate['native_contexts_after_close']==0 and gate['cancellation'] is True
 assert all(v['video_byte_exact'] and v['AAC_LC_stereo'] and v['monotonic_DTS'] for v in gate['output_proof'])
 hls=gate['cases'][0]['HLS'];assert hls['actual_Android_HLS_playback'] and hls['video_rendered_frames']>0 and hls['audio_rendered_buffers']>hls['audio_rendered_buffers_before_seek']
 inventory,bundles,_,_,_=c.tools()
 out=ROOT/'cast504-stage';out.mkdir();reports={}
 with ZipFile(base) as before:
  # Exact signature members are omitted only in these explicitly unsigned files.
  names=set(before.namelist())-set(inventory.SIGNATURE)
  for kind,version in r['versions'].items():
   changes={'AndroidManifest.xml':bundles.set_version(before.read('AndroidManifest.xml'),version),LABEL:('infinity.last_updated_in='+str(version)+'\ncobra.last_updated_in=2103445\n').encode()}
   if kind=='candidate':changes[LIB]=library.read_bytes()
   path=out/('Infinity-'+str(version)+'-UNSIGNED-NOT-INSTALLABLE.apk')
   with ZipFile(path,'w',allowZip64=True) as after:
    for info in before.infolist():
     if info.filename in names:after.writestr(copy.copy(info),changes.get(info.filename,before.read(info.filename)))
   delta={}
   with ZipFile(path) as after:
    assert set(after.namelist())==names and len(after.namelist())==len(names)
    for name in names:
     def digest(z):
      with z.open(name) as f:return hashlib.file_digest(f,'sha256').hexdigest()
     a,b=digest(before),digest(after)
     if a!=b:delta[name]={'before':a,'after':b}
   assert set(delta)==set(changes),'EXACT_NATIVE_ONLY_MEMBER_DIFF'
   reports[kind]={'APK_sha256':sha(path),'versionCode':version,'changes':delta,'unchanged_members':len(names)-len(delta)}
 (out/'STAGING.json').write_text(json.dumps({'status':'PASS_UNSIGNED_NATIVE_ONLY504_STAGE','source':os.environ['GITHUB_SHA'],'baseline_APK_sha256':BASE,'versions':r['versions'],'payloads':reports,'native_artifact':r['native'],'Android_artifact':r['Android'],'Cobra':'UNCHANGED','module_signatures':'UNCHANGED','DEX':'UNCHANGED','Kodi':'UNCHANGED','owner_data':'NOT_ACCESSED','signed':False},indent=2)+'\n')
 print('PASS_NATIVE_ONLY_UNSIGNED_PAIR_NO_KODI_DEX_OR_MODULE_BUILD')
if __name__=='__main__':main()
