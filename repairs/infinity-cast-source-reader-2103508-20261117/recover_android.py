"""Strict read-only repair of CI result transport; original failed run stays failed."""
from pathlib import Path
from zipfile import ZipFile
import hashlib,json,os,re,stat,subprocess,types
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1]
def sha(p):
 with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def unique_pairs(rows):
 d={}
 for k,v in rows:
  assert k not in d,'DUPLICATE_RESULT_KEY';d[k]=v
 return d

def core_from_log(text):
 lines=[line for line in text.splitlines() if re.search(r'\bI InfinityPipelineProbe:\s*\{',line)];assert len(lines)==1,'ONE_FINAL_PROBE_RECORD'
 record=lines[0].split('InfinityPipelineProbe:',1)[1].strip();decoder=json.JSONDecoder(object_pairs_hook=unique_pairs);assert record.startswith('{');at=1;core={}
 while True:
  while at<len(record) and record[at].isspace():at+=1
  key,end=decoder.raw_decode(record,at);assert type(key) is str and key not in core;at=end
  while at<len(record) and record[at].isspace():at+=1
  assert record[at]==':';at+=1
  while at<len(record) and record[at].isspace():at+=1
  if key=='events':
   assert record[at]=='"'
   try:decoder.raw_decode(record,at)
   except json.JSONDecodeError:break
   raise AssertionError('EXPECTED_KNOWN_TRUNCATED_EVENTS_STRING')
  value,at=decoder.raw_decode(record,at);core[key]=value
  while at<len(record) and record[at].isspace():at+=1
  assert record[at]==',';at+=1
 return core,hashlib.sha256(lines[0].encode()).hexdigest()

def validate(g):
 expected={'limit_negative_actual_bytes','cold_source_bytes','cold_allowance','sequential_random_regeneration','hardware_video','planner_error_reporting','HLS','production_R8_Relay','provider_auth','byte_ranges','cancellation_ms','pass','status','owned_native_after_close','TV_playback','phone_handoff','shutdown'}
 assert set(g)==expected,'EXACT_COMPLETE_CORE_FIELDS_REQUIRED'
 for n in ('pass','sequential_random_regeneration','planner_error_reporting','production_R8_Relay','provider_auth','byte_ranges'):assert g[n] is True,n
 for n in ('limit_negative_actual_bytes','cold_source_bytes','cold_allowance','cancellation_ms','owned_native_after_close'):assert type(g[n]) is int and g[n]>=0
 assert g['status']=='PASS_ACTUAL_ARM64_BOUNDED_SOURCE_READER' and g['hardware_video']=='NOT_EXERCISED' and g['TV_playback']=='PENDING_OWNER' and g['shutdown']=='NOT_SELECTED'
 assert g['limit_negative_actual_bytes']==33554432 and 33554432<g['cold_source_bytes']<=g['cold_allowance']<=134217728 and g['cancellation_ms']<=8000 and g['owned_native_after_close']==0
 h=g['HLS'];assert type(h) is dict;assert h['actual_Android_HLS_playback'] is True and h['isPlaying'] is True
 for n in ('continuous_position_before_seek','video_rendered_frames_before_seek','video_rendered_frames','audio_rendered_buffers_before_seek','audio_rendered_buffers','duration_ms','seek_mapped_ms','seek_elapsed_ms','seek_position_ms','rendered_first_frame_events'):assert type(h[n]) is int and h[n]>=0,n
 assert h['continuous_position_before_seek']>=4800 and abs(h['seek_mapped_ms']-20500)<200 and abs(h['duration_ms']-24000)<200
 assert h['video_rendered_frames']>h['video_rendered_frames_before_seek'] and h['audio_rendered_buffers']>h['audio_rendered_buffers_before_seek'] and h['rendered_first_frame_events']>0
 assert 20650<=h['seek_position_ms']<h['duration_ms']-100 and h['seek_position_ms']<=20500+h['seek_elapsed_ms']+500 and h['seek_elapsed_ms']<=8000

def main():
 assert os.environ['GITHUB_ACTIONS']=='true' and os.environ['GITHUB_REPOSITORY']=='mahfouzhassine8-ops/project-infinity' and os.environ['GITHUB_REF']=='refs/heads/work/infinity-2103508-cast-source-reader-20261117'
 r=json.loads((HERE/'CI-RECOVERY.json').read_bytes());assert not r['engine_build'] and not r['Android_rerun'] and not r['owner_APK'] and not r['shutdown']
 reviewRaw=(HERE/'RECOVERY-REVIEW.json').read_bytes();assert hashlib.sha256(reviewRaw).hexdigest()==r['review_sha256'];review=json.loads(reviewRaw)
 assert review['reviewer']=='Astra' and review['status']=='PASS_READONLY_ANDROID_TRANSPORT_RECOVERY'
 fixed={k:r[k] for k in ('execution','baseline','log_sha256','final_record_sha256','library_sha256','Cast_DEX_sha256','native_inputs','execution_source_files','inputs')}
 assert hashlib.sha256(json.dumps(fixed,sort_keys=True,separators=(',',':')).encode()).hexdigest()==review['request_sha256']
 for n,h in r['inputs'].items():assert sha(ROOT/n)==h,n
 assert subprocess.check_output(['git','diff','--name-only',r['source_commit'],os.environ['GITHUB_SHA']],text=True).splitlines()==[str((HERE/'CI-RECOVERY.json').relative_to(ROOT))]
 helper='repairs/infinity-movies-continue-cast-2103486-20261112/release/common_release.py';raw=subprocess.check_output(['git','show','21616dfa94bf7ca9ec52e40119edf95df5e64073:'+helper]);s={'__file__':str(ROOT/helper),'__name__':'_original_reader'};exec(compile(raw,str(ROOT/helper),'exec'),s);c=types.SimpleNamespace(**s)
 row=r['execution'];run=c.api('actions/runs/'+str(row['run']));assert run['status']=='completed' and run['conclusion']=='failure' and run['head_sha']==row['source'] and run['workflow_id']==row['workflow_id']
 jobs=c.api('actions/runs/'+str(row['run'])+'/jobs?per_page=100')['jobs'];selected=[j for j in jobs if j['name']=='source-reader'];assert len(selected)==1
 failures={v['name'] for v in selected[0]['steps'] if v['conclusion']=='failure'}
 assert failures=={'Run reactivecircus/android-emulator-runner@a421e43855164a8197daf9d8d40fe71c6996bb0d','Require actual pipeline result independently of emulator action'}
 assert any(v['name'].startswith('Compile changed Cast JNI only') and v['conclusion']=='success' for v in selected[0]['steps'])
 assert all(j['conclusion'] in ('skipped','success') for j in jobs if j['name']!='source-reader')

 artifact=c.api('actions/artifacts/'+str(row['id']));assert not artifact['expired'] and artifact['workflow_run']['id']==row['run'] and all(artifact[k]==row[k] for k in ('name','digest','size_in_bytes'))
 out=ROOT/'cast508-recovered';out.mkdir();archive=out/'ORIGINAL-FAILED-EXECUTION.zip'
 with archive.open('xb') as f:subprocess.run(['gh','api','repos/'+c.REPO+'/actions/artifacts/'+str(row['id'])+'/zip'],stdout=f,check=True,timeout=900)
 assert archive.stat().st_size==row['size_in_bytes'] and 'sha256:'+sha(archive)==row['digest'];files=out/'execution';files.mkdir()
 with ZipFile(archive) as z:
  assert len(z.namelist())==len(set(z.namelist())) and len(z.namelist())<1000 and sum(i.file_size for i in z.infolist())<64*1024*1024
  for i in z.infolist():assert not Path(i.filename).is_absolute() and '..' not in Path(i.filename).parts and '\\' not in i.filename and not stat.S_ISLNK(i.external_attr>>16)
  z.extractall(files)
 log=c.unique(files,'LOGCAT.txt');assert sha(log)==r['log_sha256'];text=log.read_text();core,line_hash=core_from_log(text);assert line_hash==r['final_record_sha256'];validate(core)
 assert not re.search(r'Process: com\.projectinfinity\.castqa\.pipeline,',text) and not re.search(r'JNI DETECTED ERROR',text),'PROBE_PROCESS_FATAL_OR_CHECKJNI_ERROR'
 original=c.unique(files,'RESULT.json');assert json.loads(original.read_bytes())=={'pass':False,'wrapper_failure':"Expecting ',' delimiter: line 1 column 663 (char 662)"},'EXACT_ORIGINAL_WRAPPER_FAILURE'
 for p,h in r['execution_source_files'].items():assert hashlib.sha256(subprocess.check_output(['git','show',row['source']+':'+p])).hexdigest()==h,p
 requiredNative={'repairs/infinity-six-repairs-2103502-20261116/cast/native/InfinityCastRemux.cpp','repairs/infinity-cast-hardware-pipeline-2103506-20261117/native/CastVideoAdapter.h','repairs/infinity-cast-end-to-end-2103504-20261116/native/CastAudioAdapter.h'};assert set(r['native_inputs'])==requiredNative
 arm=c.unique(files,'ARM64.json');proof=json.loads(arm.read_bytes());library=c.unique(files,'libinfinitycastremux.so');assert proof['status']=='PASS_CAST508_SOURCE_READER_ARM64_LINK' and proof['baseline']==2103508 and proof['source']==row['source'] and proof['engine_rebuilt'] is False and sha(library)==proof['new_library_sha256']==r['library_sha256']
 for n in r['native_inputs']:assert sha(ROOT/n)==proof['source_hashes'][n],n
 for n,h in r['execution_source_files'].items():assert proof['source_hashes'][n]==h,n
 build=c.unique(files,'BUILD.json');b=json.loads(build.read_bytes());assert b['source']==row['source'] and b['foundation']==r['baseline'] and b['native']['libkodi.so']=='b3d8d96aa55bf0e48f6cf7c995b2c2ebf9c53720b94f2a9e791dd039d64bf1e7' and b['production_Cast_DEX_sha256']==r['Cast_DEX_sha256'] and b['new_Cast_library_sha256']==r['library_sha256']
 from verify_android_media import verify
 media=verify(files,out/'MEDIA.json');assert abs(media['source_duration_us']//1000-core['HLS']['duration_ms'])<2
 # New receipt preserves the historical failure, not an edited original result.
 core.update(status='PASS_RECOVERED_ACTUAL_ARM64_SOURCE_READER_EVIDENCE',original_execution=row,original_workflow_conclusion='failure',original_wrapper='FAIL_JSON_RESULT_TRANSPORT',source=os.environ['GITHUB_SHA'],execution_source=row['source'],recovery='READ_ONLY_AUTHENTICATED_COMPLETE_CORE_AND_MEDIA_CHECK; NO_ANDROID_RERUN',truncated_events='UNAVAILABLE',runtime_API_field='UNAVAILABLE',log_sha256=sha(log),final_record_sha256=line_hash,media_sha256=sha(out/'MEDIA.json'),original_RESULT_sha256=sha(original))
 (out/'RECOVERED.json').write_text(json.dumps(core,indent=2)+'\n');print(json.dumps(core,indent=2))
if __name__=='__main__':main()
