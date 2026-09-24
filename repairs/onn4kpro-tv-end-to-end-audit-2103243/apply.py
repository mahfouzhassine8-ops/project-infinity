#!/usr/bin/env python3
"""Apply the reviewed TV-only RC23 diff. Source preservation is not device certification."""
from pathlib import Path
import argparse,difflib,hashlib,json,runpy,subprocess
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
VERSION=2103243
RELEASE='1.0.9-Cobra-Onn4KPro-TV-End-To-End-Audit-RC23'
BASE_COMMIT='f95e84676932470ec6093bf6408a920d40239702'
BASE_ACTIVITY_SHA='0db1f02b5b766ec3b6cae8f0c82d8829ab9539221692604ff3c34b5ac640672a'
ACT='tools/android/packaging/xbmc/src/InfinityLiveActivity.java.in'
GRADLE='tools/android/packaging/xbmc/build.gradle.in'
CHANGED_METHODS=set('''onBackPressed cobraTvClosePowerMenuRestoreFocus showCobraPowerMenu cobraTvChannelPlaybackState cobraTvPlayingIndicatorKey cobraTvFocusDrawer cobraTvCloseDrawerRestoreFocus cobraTvBeginRemoteEdgeAction cobraTvPostDirectoryFocus toggleCobraDrawer clearStage cobraTvRecoverUnexpectedPause showVodLibrary cobraPopulateVodLandingDefault cobraPopulateVodLandingSearchResults renderVodBrowse cobraRenderVodCollection cobraTvRenderVodSearchResults cobraBrowseVodPerson cobraBrowseVodCollectionMetadata cobraShowVodDetails cobraLoadVodArtwork cobraTvFocusMultiRow cobraTvActivateMultiRow cobraTvMoveTransientFocus cobraTvHandleTransientKey dispatchKeyEvent cobraRefreshModeDetails'''.split())
ADDED=set('''field:mCobraTvConsumedDevices field:mCobraTvConsumedDownTimes field:mCobraTvFocusInputGeneration field:mCobraTvMultiActivationPending field:mCobraTvPowerFocusGeneration field:mCobraTvPowerPreviousFocus field:mCobraTvRemoteEdgeDevice field:mCobraVodDetailsGeneration method:cobraReleaseVodTrimTree(View) method:cobraTvActualPlaybackState(ExoPlayer) method:cobraTvDiscreteKey(int) method:cobraTvFocusTargetCurrent(View) method:cobraTvRecordConsumedKey(KeyEvent)'''.split())
def digest(data):return hashlib.sha256(data).hexdigest()
def file_hash(path):return digest(path.read_bytes())
def dump(path,value):path.write_text(json.dumps(value,indent=2,sort_keys=True)+'\n')
def inventory(source,out):
 raw=subprocess.check_output(['java',str(HERE/'AuditJavaInventory.java'),str(source)],text=True)
 value=json.loads(raw);dump(out,value);return value

def main():
 p=argparse.ArgumentParser();p.add_argument('--shell',type=Path,required=True);p.add_argument('--out',type=Path,default=Path('audit243/source'));a=p.parse_args()
 shell=a.shell.resolve();out=a.out.resolve();out.mkdir(parents=True,exist_ok=True)
 receipt_path=ROOT/'engine/background-resume-source.json';receipt=json.loads(receipt_path.read_text())
 assert receipt['version_code']==2103242 and receipt['version_name']=='1.0.9-Cobra-Onn4KPro-TV-Final-Product-Audit-RC22','Not locked RC22 source'
 assert receipt['tv_target_abi']=='armeabi-v7a' and receipt['mobile_parent_untouched'] is True
 for name,row in receipt['files'].items():assert file_hash(shell/name)==row['after'],'Baseline receipt drift: '+name
 before_files={str(f.relative_to(shell)):file_hash(f) for f in shell.rglob('*') if f.is_file()}
 path=shell/ACT;original=path.read_text();assert file_hash(path)==BASE_ACTIVITY_SHA,'Wrong Activity preimage'
 baseline_copy=out/'InfinityLiveActivity-RC22.java.in';baseline_copy.write_text(original)
 before=inventory(path,out/'baseline-declarations.json')
 lib=runpy.run_path(str(ROOT/'repairs/onn4kpro-tv-final-product-audit-2103242/apply.py'))
 modified=runpy.run_path(str(HERE/'activity_edits.py'),init_globals={'s':original,'lib':lib})['s']
 path.write_text(modified)
 after=inventory(path,out/'candidate-declarations.json')
 changed=[k for k in before if k in after and before[k]['sha256']!=after[k]['sha256']]
 removed=sorted(set(before)-set(after));added=sorted(set(after)-set(before))
 assert not removed,'Original declarations removed: '+repr(removed)
 assert set(added)==ADDED,'Unexpected added declarations: '+repr(set(added)^ADDED)
 names={k.split(':',1)[1].split('(',1)[0] for k in changed if k.startswith('method:')}
 assert names==CHANGED_METHODS,'Unexpected changed methods: '+repr(names^CHANGED_METHODS)
 assert [k for k in changed if not k.startswith('method:')]==['field:mCobraVodTrimRoles'],'Unexpected class/field mutation'
 # Every original nested class (including streaming, timeshift, playback binding and dot renderer)
 # is covered by this declaration comparison, not merely selected grep tokens.
 assert len(changed)==29 and len(added)==13
 gradle=shell/GRADLE;text=gradle.read_text()
 for old,new in [('versionCode 2103242','versionCode 2103243'),('versionName "1.0.9-Cobra-Onn4KPro-TV-Final-Product-Audit-RC22"','versionName "'+RELEASE+'"')]:
  assert text.count(old)==1,old;text=text.replace(old,new,1)
 gradle.write_text(text)
 after_files={str(f.relative_to(shell)):file_hash(f) for f in shell.rglob('*') if f.is_file()}
 assert set(before_files)==set(after_files),'Source file inventory changed'
 changed_files=sorted(k for k in before_files if before_files[k]!=after_files[k])
 assert changed_files==sorted([ACT,GRADLE]),'Unrelated source mutation: '+repr(changed_files)
 for name in changed_files:receipt['files'][name]['after']=after_files[name]
 receipt.update(version_code=VERSION,version_name=RELEASE,source_parent=2103242,candidate_locked=False,physical_device_verified=False,runtime_device_tested=False,
  tv_rc23_source_audit=True,tv_modal_input_priority=True,tv_focus_callback_owner_validation=True,
  tv_explicit_focus_links_respected=True,tv_remote_keypair_consumption=True,tv_remote_edge_guard_ms=None,
  tv_remote_edge_guard_policy='key-down-time-device identity; repeat suppression; no inter-press cooldown',
  tv_transport_repeat_guard=True,tv_native_long_press_preserved=True,
  tv_unexpected_non_user_pause_recovery=False,tv_unexpected_pause_recovery_delay_ms=None,
  tv_non_user_pause_observation_only=True,tv_system_pause_respected=True,
  tv_playing_dot_actual_is_playing=True,tv_vod_async_navigation_guard=True,
  tv_vod_search_ime_flush_before_focus=True,tv_vod_search_detach_cancels_pending=True,
  tv_vod_search_cards_wrap_content=True,tv_vod_collection_card_height_normal_dp=314,
  tv_vod_collection_card_height_compact_dp=286,tv_vod_trim_registry_weak=True,
  tv_vod_artwork_input_limit_bytes=4194304,tv_vod_artwork_decode_max_edge_px=1024,
  tv_vod_artwork_cache_limit_bytes=16777216,tv_multi_picker_adapter_generation_guard=True,
  tv_native_engine_rebuilt=False,native_engine_rebuilt=False,mobile_parent_untouched=True,
  playback_engine_unchanged=True)
 dump(receipt_path,receipt)
 for name,row in receipt['files'].items():assert file_hash(shell/name)==row['after'],'Candidate receipt drift: '+name
 patch=''.join(difflib.unified_diff(original.splitlines(True),modified.splitlines(True),fromfile='locked-RC22/'+ACT,tofile='candidate-RC23/'+ACT))
 (out/'rc23-activity.patch').write_text(patch)
 report={'baseline_commit':BASE_COMMIT,'baseline_version':2103242,'candidate_version':VERSION,'version_name':RELEASE,
  'activity_before_sha256':BASE_ACTIVITY_SHA,'activity_after_sha256':after_files[ACT],
  'original_declarations':len(before),'unchanged_original_declarations':len(before)-len(changed),'changed_declarations':changed,
  'added_declarations':added,'removed_declarations':removed,'inventoried_source_files':len(before_files),
  'changed_source_files':changed_files,'unchanged_source_files':len(before_files)-len(changed_files),
  'android_resources_source_unchanged':True,'all_original_nested_classes_byte_identical':True,
  'physical_device_tested':False,'android_view_tests_status':'separate mandatory workflow gate',
  'live_provider_and_decoder_tests_status':'not executed by this source audit'}
 dump(out/'source-preservation.json',report)
 dump(out/'source-file-hashes-before.json',before_files);dump(out/'source-file-hashes-after.json',after_files)
 print('PASS: RC23 explicit 29-declaration correction allowlist; all other',len(before)-29,'original declarations and',len(before_files)-2,'source files unchanged')
if __name__=='__main__':main()
